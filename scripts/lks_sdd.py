#!/usr/bin/env python3
"""LKS-SDD v5 public dispatcher; legacy formats use read-only migration readers."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v5_cli import main
if __name__ == "__main__":
    raise SystemExit(main())
