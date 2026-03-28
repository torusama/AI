"""
main.py
Entry point — just launches the app.
All screen logic lives in menu.py.
"""

import os
from menu import run_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    run_app(BASE_DIR)