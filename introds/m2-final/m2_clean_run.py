#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IntroDS Milestone 2: clean, fresh parse of M1 checkpoints.

No M1 changes. No M2 v5/v6 reads. No targeted repair/merge.
A missing/empty LaTeX source is classified SKIP_NO_LATEX, never M2_ERROR.
Parser issues are recorded with evidence, not inferred from file names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import traceback
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from m2_final_patch import install_parser_overlay, smoke_test_overlay

M2_REVISION = 10
RANGE_IDS = tuple(range(1, 6))
TABLE_FILES = ("elements.jsonl", "hierarchy.jsonl", "bibtex.jsonl", "metrics_m2.json")
TECHNICAL_INCLUDES = frozenset((
    "xy", "xypic", "epsf", "glyphtounicode", "supp-pdf",
    "pdftexcmds", "epstopdf", "color", "texnansi", "pdfsync"
))
NO_LATEX_REASONS = (
    "missing sources directory", "empty record from m1",
    "no tex", "no latex", "pdf_only", "pdf only", "no source",
    "no_source", "source archive unavailable"
)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(message):
    print(f"[{utc_now()}] {message}", flush=True)


def json_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def jsonl_write(path, items):
    with Path(path).open("w", encoding="utf-8") as output:
        for item in items:
            output.write(json.dumps(item, ensure_ascii=False) + "\n")


def sha256(path):
    dig = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            dig.update(chunk)
    return dig.hexdigest()


def drive_service():
    import google.auth
    from googleapiclient.discovery import build
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def children(service, parent):
    result, token = [], None
    while True:
        page = service.files().list(
            q=f"'{parent}' in parents and trashed=false",
            fields="nextPageToken,files(id,name,size,mimeType,parents)",
            pageSize=1000, pageToken=token, supportsAllDrives=True,
            includeItemsFromAllDrives=True).execute()
        result.extend(page.get("files", []))
        token = page.get("nextPageToken")
        if not token:
            return result


def find_m1_parent(service, explicit):
    if explicit != "AUTO":
        return explicit
    match = service.files().list(
        q="name = 'range_1_dev' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="nextPageToken,files(id,name,parents)", pageSize=1000,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    candidates = []
    for found in match.get("files", []):
        for parent in found.get("parents", []):
            names = {f["name"] for f in children(service, parent)
                     if f.get("mimeType") == "application/vnd.google-apps.folder"}
            if all(f"range_{x}_dev" in names for x in RANGE_IDS):
                candidates.append(parent)
    candidates = sorted(set(candidates))
    if len(candidates) != 1:
        raise RuntimeError("M1 source parent is ambiguous/not visible. Set M1_PARENT_ID explicitly.")
    return candidates[0]


def download(service, item, dest):
    from googleapiclient.http import MediaIoBaseDownload
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = int(item["size"]) if item.get("size") else None
    if dest.is_file() and expected is not None and dest.stat().st_size == expected:
        return
    temp = dest.with_name(dest.name + ".downloading")
    for attempt in range(4):
        try:
            temp.unlink(missing_ok=True)
            request = service.files().get_media(fileId=item["id"], supportsAllDrives=True)
            with temp.open("wb") as stream:
                d = MediaIoBaseDownload(stream, request, chunksize=8 * 1024 * 1024)
                finished = False
                while not finished:
                    _, finished = d.next_chunk(num_retries=3)
            if expected is not None and temp.stat().st_size != expected:
                raise IOError("Download length mismatch for " + item["name"])
            os.replace(temp, dest)
            return
        except Exception:
            temp.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def source_status(paper, version, trace, raw_kind, raw_detail):
    arxiv_id = paper["arxiv_id"]
    trace = trace or {}
    reason = str(trace.get("reason") or "")
    src_len = int(trace.get("source_characters") or 0)
    root = trace.get("root_file")
    issues = []
    if raw_kind == "FAILED" and (
        src_len == 0 and (not root or any(x in reason.lower() for x in NO_LATEX_REASONS))
    ):
        status = "SKIP_NO_LATEX"
    elif raw_kind == "EMPTY" and src_len == 0:
        status = "SKIP_NO_LATEX"
    elif raw_kind == "FAILED":
        status = "PARSER_FAILED"
    elif raw_kind == "EMPTY":
        status = "REVIEW_EMPTY_WITH_SOURCE"
    elif raw_kind == "PARTIAL":
        status = "PARTIAL_REVIEW"
    else:
        status = "PARSED"

    headings = list(trace.get("unrepresented_headings") or [])
    real_looking = [str(h) for h in headings if not re.search(r"#[1-9]", str(h))]
    macros = [str(h) for h in headings if re.search(r"#[1-9]", str(h))]
    if real_looking:
        issues.append({"level": "REVIEW", "code": "HEADING_NOT_REPRESENTED",
                       "evidence": real_looking})
    if macros:
        issues.append({"level": "INFO", "code": "MACRO_PLACEHOLDER_HEADING",
                       "evidence": macros})
    unresolved = list(trace.get("missing_includes") or [])
    if unresolved:
        support, other = [], []
        for entry in unresolved:
            filename = str(entry).split(":", 1)[-1].strip().replace("\\", "/").split("/")[-1].lower()
            filename = filename.removesuffix(".tex")
            (support if filename in TECHNICAL_INCLUDES else other).append(entry)
        if support:
            issues.append({"level": "INFO", "code": "SUPPORT_INCLUDE_UNRESOLVED",
                           "evidence": support})
        if other:
            issues.append({"level": "REVIEW", "code": "INCLUDE_UNRESOLVED",
                           "evidence": other})
    if status == "PARSER_FAILED":
        issues.append({"level": "ERROR", "code": "PARSER_FAILED_WITH_SOURCE",
                       "evidence": [raw_detail.get("error") or raw_detail.get("reason") or reason]})
    if status == "PARTIAL_REVIEW" and not unresolved and not headings:
        issues.append({"level": "REVIEW", "code": "PARTIAL_UNCLASSIFIED",
                       "evidence": [raw_detail.get("reason") or reason]})
    if status == "REVIEW_EMPTY_WITH_SOURCE":
        issues.append({"level": "REVIEW", "code": "EMPTY_NONEMPTY_INPUT",
                       "evidence": [raw_detail.get("reason") or reason]})
    # No file-name heuristics: sample.tex and template.tex are not evidence of failure.
    return {
        "arxiv_id": arxiv_id, "version": version, "status": status,
        "parser_status": raw_kind, "root_file": root,
        "source_characters": src_len, "reason": reason,
        "error": raw_detail.get("error") or "",
        "included_files": trace.get("included_files", []),
        "source_heading_count": trace.get("source_heading_count", 0),
        "issues": issues,
    }


def report_papers(metrics, out_dir):
    statuses, issues, skipped = [], [], []
    for paper in metrics["coverage"]:
        traces = {row.get("version"): row for row in paper.get("source_trace", [])}
        version_kinds = {}
        for field, kind in (
            ("parsed_versions", "PARSED"), ("partial_versions", "PARTIAL"),
            ("empty_versions", "EMPTY"), ("failed_versions", "FAILED")
        ):
            for entry in paper.get(field, []):
                v = entry if isinstance(entry, int) else entry.get("version")
                if v in version_kinds:
                    raise RuntimeError(f"Overlapping version status {paper['arxiv_id']} v{v}")
                version_kinds[v] = (kind, entry if isinstance(entry, dict) else {})
        for version in paper.get("versions", []):
            if version not in version_kinds:
                raise RuntimeError(f"Missing M2 version status {paper['arxiv_id']} v{version}")
            kind, details = version_kinds[version]
            item = source_status(paper, version, traces.get(version), kind, details)
            statuses.append(item)
            if item["status"] == "SKIP_NO_LATEX":
                skipped.append({"arxiv_id": item["arxiv_id"], "version": version,
                                "reason": item["reason"] or item["error"] or kind})
            for issue in item["issues"]:
                issues.append({"arxiv_id": item["arxiv_id"], "version": version,
                               "status": item["status"], "root_file": item["root_file"],
                               **issue})
        if not paper.get("versions"):
            skipped.append({"arxiv_id": paper["arxiv_id"], "version": None,
                            "reason": "M1 contains no version"})
            statuses.append({"arxiv_id": paper["arxiv_id"], "version": None,
                             "status": "SKIP_NO_LATEX", "parser_status": "EMPTY",
                             "root_file": None, "source_characters": 0,
                             "reason": "M1 contains no version", "issues": []})
    jsonl_write(out_dir / "paper_version_log.jsonl", statuses)
    jsonl_write(out_dir / "m2_issues.jsonl", issues)
    jsonl_write(out_dir / "skip_no_latex.jsonl", skipped)
    counter = Counter(p["status"] for p in statuses)
    counter["TOTAL_VERSIONS"] = len(statuses)
    counter["TOTAL_PAPERS"] = len(metrics["coverage"])
    counter["REVIEW_ISSUES"] = sum(1 for i in issues if i["level"] == "REVIEW")
    counter["ERROR_ISSUES"] = sum(1 for i in issues if i["level"] == "ERROR")
    counter["INFO_ISSUES"] = sum(1 for i in issues if i["level"] == "INFO")
    json_write(out_dir / "m2_status_summary.json", dict(counter))
    return dict(counter)


def safe_tar_headers(path):
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            pp = Path(member.name)
            if pp.is_absolute() or ".." in pp.parts or member.issym() or member.islnk():
                raise ValueError(f"Unsafe M1 tar member: {path.name} / {member.name}")


def verify_archives(batch_dir):
    from src.m2_parsing.batch_pipeline import discover_checkpoint_batches
    batches = discover_checkpoint_batches(batch_dir)
    for idx, (_, archive, manifest) in enumerate(batches, 1):
        if archive.stat().st_size != manifest["archive_bytes"]:
            raise IOError(f"M1 archive size mismatch: {archive.name}")
        if sha256(archive) != manifest["archive_sha256"]:
            raise IOError(f"M1 archive hash mismatch: {archive.name}")
        safe_tar_headers(archive)
        if idx % 10 == 0 or idx == len(batches):
            log(f"M1 source integrity: verified {idx}/{len(batches)} batches")
    count = sum(len(m["ids"]) for _, _, m in batches)
    if count != 5000:
        raise ValueError(f"Expected 5,000 papers per range; found {count}")
    return batches


def run_parser(label, work, batch_dir, workers):
    cmd = [sys.executable, "-u", "-m", "src.m2_parsing.run_m2",
           "--batch-dir", str(batch_dir), "--working-dir", str(work / "working"),
           "--tables-dir", str(work / "tables"), "--workers", str(workers),
           "--resume"]
    logfile = work / "parser_full.log"
    started = time.monotonic()
    done = threading.Event()
    count = [0]

    def heartbeat():
        while not done.wait(30):
            log(f"{label}: running for {int(time.monotonic() - started)}s; "
                f"parser lines={count[0]} (full log saved)")

    monitor = threading.Thread(target=heartbeat, daemon=True)
    monitor.start()
    try:
        with logfile.open("a", encoding="utf-8") as output:
            output.write(f"\n=== M2 START {utc_now()} ===\n")
            proc = subprocess.Popen(cmd, cwd=PROJECT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                    errors="replace", bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                count[0] += 1
                output.write(line)
                output.flush()
                if count[0] <= 20 or count[0] % 100 == 0 or re.search(
                    r"error|failed|traceback|warning|batch", line, flags=re.I
                ):
                    print(f"[{label}] {line.rstrip()}", flush=True)
            result = proc.wait()
    finally:
        done.set()
        monitor.join(timeout=3)
    if result not in (0, 2):
        raise RuntimeError(f"Parser CLI returned {result}; see {logfile}")
    return logfile


def verify_completed(rng, final_dir):
    from src.m2_parsing.quality_checks import verify_tables_zip
    from src.m2_parsing.selective_repair import read_metrics
    zipfile_path = final_dir / f"M2_range_{rng}_tables.zip"
    required = [zipfile_path, final_dir / "metrics_m2.json",
                final_dir / "quality_report.json", final_dir / "benchmark_summary.json",
                final_dir / "paper_version_log.jsonl", final_dir / "m2_status_summary.json"]
    if not final_dir.exists():
        return False
    if any(not x.is_file() for x in required):
        raise RuntimeError(f"Incomplete output folder: {final_dir}. Inspect before retry.")
    qa = json.loads(required[2].read_text(encoding="utf-8"))
    bench = json.loads(required[3].read_text(encoding="utf-8"))
    if not qa.get("passed") or qa.get("pipeline_revision") != M2_REVISION:
        raise RuntimeError(f"Range {rng} QA did not pass")
    if sha256(zipfile_path) != bench.get("zip_sha256"):
        raise RuntimeError(f"Range {rng} ZIP checksum changed")
    verify_tables_zip(zipfile_path)
    if read_metrics(zipfile_path) != json.loads(required[1].read_text(encoding="utf-8")):
        raise RuntimeError(f"Range {rng} metrics inconsistent")
    log(f"Range {rng} already verified: skip (resume)")
    return True


def publish_stage(stage, target):
    if target.exists():
        raise FileExistsError("Refusing to overwrite " + str(target))
    temp = target.parent / ("." + target.name + "_incomplete")
    if temp.exists():
        raise RuntimeError("Incomplete previous upload: " + str(temp))
    temp.mkdir(parents=True)
    try:
        for source in sorted(stage.iterdir()):
            if not source.is_file():
                continue
            destination = temp / source.name
            shutil.copy2(source, destination)
            if sha256(source) != sha256(destination):
                raise IOError("Drive copy verification failed: " + source.name)
        os.rename(temp, target)
    except Exception:
        log("Incomplete upload kept for inspection at " + str(temp))
        raise


def run_range(service, rng, remote_folder, out_root, local_root, workers):
    from src.m2_parsing.quality_checks import validate_range_output, verify_tables_zip
    from src.m2_parsing.batch_pipeline import PIPELINE_REVISION
    assert PIPELINE_REVISION == M2_REVISION
    label = f"range_{rng}"
    work = local_root / label
    batch_dir = work / "checkpoints"
    batch_dir.mkdir(parents=True, exist_ok=True)
    candidates = [f for f in children(service, remote_folder)
                  if f["name"].startswith("batch_") and
                  f["name"].endswith((".json", ".tar.gz"))]
    remote = {f["name"]: f for f in candidates}
    if len(remote) != len(candidates):
        raise RuntimeError(f"{label}: duplicate M1 files")
    archives = [name for name in remote if name.endswith(".tar.gz")]
    if not archives:
        raise RuntimeError(f"{label}: no M1 checkpoint archives found")
    for name in archives:
        if name.removesuffix(".tar.gz") + ".json" not in remote:
            raise RuntimeError(f"{label}: missing manifest for {name}")
    log(f"{label}: downloading {len(remote)} M1 source files")
    for i, name in enumerate(sorted(remote), 1):
        download(service, remote[name], batch_dir / name)
        if i % 20 == 0 or i == len(remote):
            log(f"{label}: source files {i}/{len(remote)}")
    verified_batches = verify_archives(batch_dir)
    log(f"{label}: source archives verified ({len(verified_batches)} batches)")
    logfile = run_parser(label, work, batch_dir, workers)
    tables = work / "tables"
    qa_raw = validate_range_output(tables, batch_dir, check_rows=True)
    if not qa_raw.get("passed"):
        raise RuntimeError(f"{label}: structural QA failed")
    metrics = json.loads((tables / "metrics_m2.json").read_text(encoding="utf-8"))
    if metrics.get("pipeline_revision") != M2_REVISION or metrics.get("n_publications") != 5000:
        raise RuntimeError(f"{label}: invalid parser revision/coverage")
    stage = work / "publish"
    stage.mkdir(exist_ok=True)
    classified = report_papers(metrics, stage)
    # Preserve raw engine QA for auditing, but remove unsupported NAME-ONLY
    # heuristics from the primary report to prevent false "error" labels.
    json_write(stage / "quality_report_engine_raw.json", qa_raw)
    qa = dict(qa_raw)
    qa["warnings"] = [w for w in qa_raw.get("warnings", [])
                      if "root possibly template" not in w and
                      "suspiciously short source" not in w]
    qa["validation_mode"] = "FULL_FROM_M1_NO_BASELINE"
    qa["semantic_decision"] = "Unverified content observations are REVIEW/INFO, never automatic ERROR"
    qa["per_version_log"] = "paper_version_log.jsonl"
    qa["log_counts"] = classified
    json_write(stage / "quality_report.json", qa)
    local_zip = work / f"M2_{label}_tables.zip"
    with zipfile.ZipFile(local_zip, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as out:
        for filename in TABLE_FILES:
            out.write(tables / filename, arcname=filename)
    verify_tables_zip(local_zip)
    shutil.copy2(local_zip, stage / local_zip.name)
    shutil.copy2(tables / "metrics_m2.json", stage / "metrics_m2.json")
    shutil.copy2(logfile, stage / "parser_full.log")
    checksum = sha256(local_zip)
    json_write(stage / "benchmark_summary.json", {
        "range": label, "pipeline_revision": M2_REVISION,
        "n_publications": metrics["n_publications"],
        "n_versions_total": metrics["n_versions_total"],
        "n_versions_parsed": metrics["n_versions_parsed"],
        "n_versions_empty": metrics["n_versions_empty"],
        "n_versions_failed": metrics["n_versions_failed"],
        "n_versions_partial": metrics["n_versions_partial"],
        "zip_sha256": checksum, "tables_zip_bytes": local_zip.stat().st_size,
        "source": "M1 CHECKPOINT FRESH REBUILD",
        "time_utc": utc_now()
    })
    json_write(stage / "input_manifest_summary.json", {
        "batches": len(verified_batches), "unique_papers": 5000,
        "source_check": "SHA256+archive size+tar path safety",
        "note": "Skip reasons in skip_no_latex.jsonl are INPUT statuses, not M2 parser failures"
    })
    publish_stage(stage, out_root / label)
    shutil.rmtree(work, ignore_errors=True)
    log(f"{label}: COMPLETE | {classified}")
    return classified


def build_master(out_root):
    from src.m2_parsing.quality_checks import combine_verified_range_zips
    if not all((out_root / f"range_{rng}" / "quality_report.json").is_file()
               for rng in RANGE_IDS):
        log("Master not created: not all 5 ranges finished.")
        return
    for rng in RANGE_IDS:
        verify_completed(rng, out_root / f"range_{rng}")
    master = out_root / "M2_master_PROVISIONAL_tables.zip"
    if master.exists():
        log("Existing master left unchanged. Create a new output directory to rebuild it.")
        return
    pending = out_root / ".M2_master_assembling.zip"
    if pending.exists():
        raise FileExistsError("Interrupted master ZIP exists: " + str(pending))
    manifest = combine_verified_range_zips(out_root, list(RANGE_IDS), pending)
    with zipfile.ZipFile(pending) as archive:
        assert archive.testzip() is None
    os.replace(pending, master)
    manifest["sha256"] = sha256(master)
    manifest["validation_label"] = "TECHNICAL_QA_PASS_CONTENT_REVIEW_PENDING"
    manifest["created_utc"] = utc_now()
    json_write(out_root / "M2_master_manifest.json", manifest)
    log(f"Combined master: {master}")


def summarize(out_root):
    rows = []
    for rng in RANGE_IDS:
        directory = out_root / f"range_{rng}"
        path = directory / "m2_status_summary.json"
        if not path.is_file():
            rows.append({"range": rng, "status": "MISSING"})
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        rows.append({"range": rng, **summary})
    json_write(out_root / "M2_ALL_RANGES_SUMMARY.json", {
        "created_utc": utc_now(), "mode": "FULL_REBUILD_FROM_M1_ONLY",
        "total_expected_papers": 25000, "ranges": rows
    })
    for row in rows:
        log(json.dumps({k: v for k, v in row.items() if k != "total"}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="M2 fresh, case-aware Colab runner")
    ap.add_argument("--ranges", nargs="+", type=int, default=list(RANGE_IDS))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--local", type=Path, default=Path("/content/m2_clean_workspace"))
    ap.add_argument("--m1-parent-id", default="AUTO")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--no-master", action="store_true")
    args = ap.parse_args()
    selected = args.ranges
    if not selected or len(selected) != len(set(selected)) or not set(selected).issubset(RANGE_IDS):
        ap.error("--ranges must be unique integers 1 to 5")
    if args.workers < 1:
        ap.error("--workers must be >= 1")
    if any(x in str(args.out).lower() for x in ("m2_processed_v5", "m2_processed_v6")):
        ap.error("Output cannot overwrite v5/v6")
    args.out.mkdir(parents=True, exist_ok=True)
    args.local.mkdir(parents=True, exist_ok=True)
    try:
        install_parser_overlay(PROJECT)
        import src.m2_parsing.hierarchy as hierarchy
        smoke_test_overlay()
        if not args.skip_tests:
            log("Running M2 regression tests...")
            subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"],
                           cwd=PROJECT, check=True)
            log("M2 regression tests PASS")
        service = drive_service()
        parent = find_m1_parent(service, args.m1_parent_id)
        directory = {x["name"]: x["id"] for x in children(service, parent)
                     if x.get("mimeType") == "application/vnd.google-apps.folder"}
        for rng in selected:
            source = directory.get(f"range_{rng}_dev")
            if source is None:
                raise FileNotFoundError(f"M1 range_{rng}_dev not found")
        for rng in selected:
            label = f"range_{rng}"
            if verify_completed(rng, args.out / label):
                continue
            try:
                run_range(service, rng, directory[f"range_{rng}_dev"],
                          args.out, args.local, args.workers)
                verify_completed(rng, args.out / label)
            except Exception:
                err = args.out / f"FAILED_range_{rng}_{int(time.time())}.json"
                json_write(err, {"range": rng, "time_utc": utc_now(),
                                 "traceback": traceback.format_exc()})
                log(f"Range {rng} FAILED. Detailed exception: {err}")
                raise
            finally:
                summarize(args.out)
        if not args.no_master:
            build_master(args.out)
        summarize(args.out)
        log(f"DONE. Outputs: {args.out}")
    except Exception:
        log("Run interrupted. Check logs / failed-range report; previous completed ranges are kept.")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
