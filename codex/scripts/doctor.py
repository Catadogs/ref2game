#!/usr/bin/env python3
"""Read-only dependency report; optional tools do not prevent assets-only work."""
import importlib.util
import json
import shutil
import sys

report = {'python': sys.executable, 'core': {m: importlib.util.find_spec(m) is not None for m in ['PIL', 'numpy']},
          'optional': {'scipy_for_study': importlib.util.find_spec('scipy') is not None},
          'executables': {m: shutil.which(m) for m in ['node', 'ffmpeg', 'ffprobe']},
          'browser': 'Run node scripts/browser-check.mjs. PLAYWRIGHT selects a package; REF2GAME_BROWSER selects an executable.'}
print(json.dumps(report, indent=2))
sys.exit(0 if all(report['core'].values()) else 1)
