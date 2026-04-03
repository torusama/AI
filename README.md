# Shipper AI Pathfinding in a Weighted Grid World

## Introduction to Artificial Intelligence - Lab 1

This project is a Python + Pygame visualization of search algorithms on a weighted grid map. A shipper starts from `P`, navigates through the environment, and tries to reach `G` while avoiding walls and handling different movement costs. The program focuses on making algorithm behavior easy to observe through animation, map selection, and result statistics.

## Team Members

| Name | Student ID |
| --- | --- |
| Võ Tấn An | 24127318 |
| Mai Khánh Băng | 24127147 |
| Nguyễn Ngọc Minh | 24127204 |
| Trần Minh Hiển | 24127037 |
| Đoàn Võ Ngọc Lâm | 24127435 |

## What This Project Includes

- A full-screen style GUI built with `pygame`
- A main menu, map selection screen, and simulation screen
- 6 predefined maps in `maps/`
- 8 search algorithms for comparison
- Animated exploration, frontier updates, and final path playback
- Heuristic selection for informed search algorithms
- Beam width selection for Beam Search
- Run, pause, reset, and speed controls
- Result tracking for cost, path length, explored nodes, execution time, and RAM
- Background music and sound effects

## Algorithms Implemented

- `BFS`
- `DFS`
- `UCS`
- `A*`
- `Greedy Search`
- `Beam Search`
- `Bidirectional Search`
- `IDA*`

### Heuristics Available

The GUI supports these heuristics where applicable:

- `manhattan`
- `euclidean`

Heuristic-based selection is enabled for:

- `A*`
- `Greedy Search`
- `Beam Search`
- `IDA*`

Beam Search also supports beam width options:

- `2`
- `5`
- `8`
- `10`

## Important Behavior Note

The README below reflects the current code behavior.

- `Greedy Search`, `Beam Search`, `Bidirectional Search`, and `IDA*` track collected goods in the search state.
- `BFS`, `DFS`, `UCS`, and `A*` currently search mainly by position from `P` to `G`.

If your report or presentation needs all algorithms to explicitly collect every good `T`, you may want to mention this difference or update the code later.

## Grid Symbols

| Symbol | Meaning |
| --- | --- |
| `P` | Shipper start position |
| `G` | Goal |
| `W` | Wall, not passable |
| `E` | Normal cell |
| `O` | High-cost cell / pothole |
| `T` | Goods |

## Movement Cost

The move cost is based on the cell the shipper enters.

| Cell Type | Cost |
| --- | --- |
| `E` | `1` |
| `P` | `1` |
| `G` | `1` |
| `T` | `1` |
| `O` | `3` |
| `W` | blocked |

## Movement Rules

- The shipper moves in 4 directions: up, down, left, right
- Diagonal movement is not used
- The shipper cannot move outside the grid
- The shipper cannot move through walls

## Interface Flow

### 1. Main Menu

- Start the application
- Exit the application
- Adjust music volume

### 2. Choose Map Screen

- Select one of the available maps
- Preview map thumbnails
- Open the statistics popup for completed runs
- Return to the main menu

### 3. Simulation Screen

- Choose an algorithm
- Choose a heuristic when supported
- Choose beam width for Beam Search
- Choose animation speed
- Run, pause, and reset the simulation
- Watch explored cells, frontier cells, and final path animation
- View result metrics in the side panel

## Result Metrics Shown in the GUI

After or during a run, the side panel can display:

- Algorithm name
- Path cost
- Path length
- Nodes found / explored
- Execution time
- RAM usage

## Project Structure

```text
AI/
|-- main.py
|-- menu.py
|-- sound_manager.py
|-- README.md
|-- Jersey15-Regular.ttf
|-- Algorithm/
|   |-- bfs.py
|   |-- dfs.py
|   |-- UCS.py
|   |-- ASTAR.py
|   |-- greedy.py
|   |-- beamsearch.py
|   |-- bidirectional.py
|   |-- idastar.py
|-- core/
|   |-- grid.py
|   |-- cost.py
|   |-- heuristic.py
|   |-- state.py
|-- gui/
|   |-- renderer.py
|   |-- panel.py
|   |-- colors.py
|-- maps/
|   |-- Open.txt
|   |-- Cost_trap.txt
|   |-- Dead_end.txt
|   |-- Map4_Dead_End_Maze.txt
|   |-- Map5_Symmetric.txt
|   |-- Map6_Realistic_Mixed.txt
|-- picture/
|   |-- menu, map, tile, and sprite assets
|-- sound/
|   |-- background music and sound effects
```

## Requirements

- Python `3.10+`
- `pip`

### Main Dependency

- `pygame`

### Optional Dependencies

These are only needed if you want the animated video background on the map selection screen:

- `opencv-python`
- `numpy`

If they are missing, the program falls back to a static background image.

## Installation

Open a terminal inside the `AI` folder, then run:

```bash
python -m venv .venv
```

### On Windows

```bash
.venv\Scripts\activate
```

### Install packages

Minimal install:

```bash
pip install pygame
```

Recommended install:

```bash
pip install pygame opencv-python numpy
```

## How to Run

From inside the `AI` directory:

```bash
python main.py
```

## How to Use

1. Launch the program with `python main.py`.
2. Click `Start` in the main menu.
3. Choose a map.
4. In the simulation screen, select:
   - an algorithm
   - a heuristic if available
   - a beam width if using Beam Search
   - an animation speed
5. Click `Run` to start the search.
6. Use `Pause` or `Reset` when needed.
7. Watch the shipper follow the final path if a solution is found.

## Map File Format

Maps are stored as plain text files in the `maps/` folder.

- Each row is written on a new line
- Cells are separated by spaces
- All rows must have the same number of columns

Example:

```text
P E E E
W W E O
E T E E
E E E G
```

## Notes on the Codebase

- `main.py` is the entry point
- `menu.py` controls screen flow and algorithm execution
- `core/` contains grid logic, costs, heuristics, and state definitions
- `Algorithm/` contains the search implementations
- `gui/` contains rendering and control panel logic
- `picture/` and `sound/` store all visual and audio assets used by the interface

## Sample Maps Included

The project currently includes these maps:

- `Open Map`
- `Cost Trap Map`
- `Dead End Map`
- `Dead End Maze`
- `Symmetric Map`
- `Realistic Map`

## Summary

This project is a visual search-algorithm simulator centered around a shipper moving in a weighted grid world. It is useful for demonstrating how different search strategies behave, how heuristics affect performance, and how pathfinding changes across different map layouts and movement costs.
