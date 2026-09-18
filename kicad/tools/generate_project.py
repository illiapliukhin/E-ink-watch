#!/usr/bin/env python3
"""Alias: run tools/gen.py"""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("gen.py")), run_name="__main__")
