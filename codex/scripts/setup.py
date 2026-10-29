#!/usr/bin/env python3
"""Portable, idempotent project setup. Uses this interpreter; never installs packages."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parent.parent


def write_new(path, text):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('project', type=Path)
    ap.add_argument('--ref', type=Path)
    ap.add_argument('--genre', choices=['side', 'top', 'blank'], default='side')
    ap.add_argument('--mode', choices=['assets', 'prototype', 'slice'], default='prototype')
    ap.add_argument('--refresh-engine', action='store_true')
    ap.add_argument('--deps-only', action='store_true')
    a = ap.parse_args()
    missing = [name for name in ['PIL', 'numpy'] if importlib.util.find_spec(name) is None]
    if missing:
        ap.error('Missing ' + ', '.join(missing) + '. Use a local Python environment with Pillow and NumPy.')
    if a.mode != 'assets' and not shutil.which('node'):
        ap.error('Node.js is required for the browser template.')
    if a.ref and not a.ref.is_file():
        ap.error('Reference does not exist: ' + str(a.ref))
    if a.deps_only:
        print('Core dependencies OK; doctor.py checks optional study/browser tools.')
        return
    p = a.project.resolve()
    p.mkdir(parents=True, exist_ok=True)
    existing = p / 'ref2game.json'
    if existing.exists():
        cfg = json.loads(existing.read_text(encoding='utf-8-sig'))
        # Existing projects retain their mode and user code.
        a.mode = cfg.get('mode', 'prototype')
    else:
        cfg = {'mode': a.mode, 'fidelity': 'style', 'generator': {'tool': 'imagegen', 'size': '1536x1024', 'alpha': 'auto', 'opaque': ['bg_sky*', '*_tex']},
               'style_bible': 'art/style_bible.txt', 'style_ref': ['ref.png'] if a.ref else [], 'view': [1920, 1080],
               'qa': {'required': ['states'], 'not_applicable': []},
               'prep': {'src': 'art/gen', 'dst': 'live/assets', 'manifest': 'live/assets.js', 'notrim': ['bg_*', '*_tex'], 'skip': ['*_sheet', '*_raw'], 'max': 2048, 'walk': {'ground': 0.6, 'ledge*': 0.45}}}
        if a.mode == 'assets':
            cfg['qa']['required'] = []
            cfg['prep'].update(dst='assets/textures', manifest='assets/assets.js')
        write_new(existing, json.dumps(cfg, indent=2) + '\n')
    for d in ['art/gen', 'art/raw', 'art/logs', 'art/prompts', 'art/requests', 'study/crops', 'study/critique', 'frames']:
        (p / d).mkdir(parents=True, exist_ok=True)
    write_new(p / 'art/style_bible.txt', 'STYLE BIBLE (replace after the study):\n<style family>; palette; projection; light; pixel grid or line weight; preserved invariants.\n')
    if a.ref:
        src = a.ref.resolve()
        if src != p / 'ref.png':
            if src.suffix.lower() in {'.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v', '.mpg', '.mpeg'}:
                if not all(shutil.which(x) for x in ['ffmpeg', 'ffprobe']):
                    ap.error('Video reference needs ffmpeg and ffprobe.')
                duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)], text=True).strip())
                subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(duration / 2), '-i', str(src), '-frames:v', '1', str(p / 'ref.png')], check=True)
            else:
                from PIL import Image
                with Image.open(src) as im:
                    im.convert('RGBA').save(p / 'ref.png')
        if not cfg.get('style_ref'):
            cfg['style_ref'] = ['ref.png']
            existing.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
    if a.mode == 'assets':
        print(f'Assets project ready: {p}; no engine, placeholders or server created.')
        return
    live = p / 'live'
    (live / 'assets').mkdir(parents=True, exist_ok=True)
    genre = SKILL / 'templates' / {'side': 'live', 'top': 'live-topdown', 'blank': 'live-blank'}[a.genre]
    for f in ['index.html', 'gl.js', 'lib.js', 'sim.js', 'scene.js', 'tune.cjs']:
        src = (genre if f in ['sim.js', 'scene.js'] else SKILL / 'templates/live') / f
        if not (live / f).exists() or (a.refresh_engine and f in ['gl.js', 'lib.js']):
            shutil.copy2(src, live / f)
    write_new(live / 'sizes.js', 'window.SIZES = window.SIZES || {};\n')
    write_new(live / 'audio.js', '// Optional audio driven by the simulation event bus.\n')
    for script, args in [('placeholders.py', ['--out', 'art/gen', '--set', a.genre]), ('prep.py', [])]:
        subprocess.run([sys.executable, str(SKILL / 'scripts' / script), *args], cwd=p, check=True)
    print(f'Project ready: {p}\nPreview: node "{SKILL / "scripts/serve.mjs"}" (run from the project)')


if __name__ == '__main__':
    main()
