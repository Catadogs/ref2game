#!/usr/bin/env python3
"""Pack a portable build and complete editable sources. Run from the project root."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid


def child(root, rel):
    p = (root / rel).resolve()
    if not p.is_relative_to(root) or p == root:
        raise ValueError(f'Path must be inside the project: {rel}')
    return p


def copy_tree(src, dst):
    if not src.exists():
        return
    if src.is_symlink() or (hasattr(src, 'is_junction') and src.is_junction()) or any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in src.rglob('*')):
        raise ValueError(f'Refusing linked source tree: {src}')
    shutil.copytree(src, dst)


def build(project, stage, name, cfg):
    mode = cfg.get('mode', 'prototype')
    prep = cfg.get('prep', {})
    manifest_path = child(project, prep.get('manifest', 'live/assets.js'))
    manifest = json.loads(re.sub(r'^\s*window\.ASSETS\s*=\s*|;\s*$', '', manifest_path.read_text(encoding='utf-8-sig')))
    textures = child(project, prep.get('dst', 'live/assets'))
    for n in manifest:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', n) or not (textures / (n + '.png')).is_file():
            raise ValueError(f'Invalid or missing texture: {n}')
    assets = stage / 'assets'
    assets.mkdir()
    copy_tree(textures, assets / 'textures')
    copy_tree(project / 'art/gen', assets / 'source')
    (assets / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    editable = stage / 'project'
    editable.mkdir()
    for d in ['live', 'art', 'study']:
        copy_tree(project / d, editable / d)
    if mode == 'assets':
        copy_tree(project / 'assets', editable / 'assets')
    for f in ['ref2game.json', 'ref.png']:
        if (project / f).is_file():
            shutil.copy2(project / f, editable / f)
    hint = 'See project/live/sim.js and the on-screen controls.'
    if mode != 'assets':
        game = stage / 'game'
        copy_tree(project / 'live', game)
        for f in game.rglob('*.cjs'):
            f.unlink()
        html = (game / 'index.html').read_text(encoding='utf-8-sig')
        if not re.search(r'<script\b', html, re.I):
            raise ValueError('Cannot mark static build: index.html has no script element')
        html = re.sub(r'<script\b', '<script>window.__STATIC__=1;</script>\n<script', html, count=1, flags=re.I)
        (game / 'index.html').write_text(html, encoding='utf-8')
        try:
            result = subprocess.run(['node', '-e', "const s=require(process.argv[1]);console.log(s.HINT||'')", str(project / 'live/sim.js')], capture_output=True, text=True, timeout=10, check=True)
            hint = result.stdout.strip() or hint
        except (OSError, subprocess.SubprocessError):
            pass
    readme = f'# {name}\n\nMode: {mode}.\n\n'
    if mode != 'assets':
        readme += f'Run a static server inside game/ (for example python -m http.server --bind 127.0.0.1), then open index.html through that server.\nControls: {hint}\n\n'
    readme += 'assets/textures/ contains prepared images; assets/source/ preserves every generated source, including sheets.\nproject/ contains the editable project, prompts, raw generations and settings.\nchecksums.json inventories the files. Packaging does not certify gameplay: run QA and interaction scenarios against the extracted build.\n'
    (stage / 'README.md').write_text(readme, encoding='utf-8')
    (stage / '.ref2game-build.json').write_text(json.dumps({'format': 2, 'name': name, 'mode': mode}), encoding='utf-8')
    checksums = {p.relative_to(stage).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
    (stage / 'checksums.json').write_text(json.dumps(checksums, indent=2), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--name', default=Path.cwd().name)
    ap.add_argument('--out', type=Path, default=Path('dist'))
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--replace', action='store_true', help='Replace only a marked ref2game build')
    a = ap.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', a.name) or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])', a.name):
            raise ValueError('Name must be a portable single directory name (letters, digits, hyphen, underscore).')
        project = Path.cwd().resolve()
        out = a.out.resolve()
        if out == project or project.is_relative_to(out) or any(out.is_relative_to(project / d) for d in ['live', 'art', 'study', 'assets']):
            raise ValueError('Output must not replace or nest inside project sources.')
        out.mkdir(parents=True, exist_ok=True)
        target, archive = out / a.name, out / (a.name + '.zip')
        for p in [target, archive]:
            if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) or p.resolve().parent != out:
                raise ValueError('Refusing linked or escaping output path.')
        if target.exists() and (not a.replace or not (target / '.ref2game-build.json').is_file()):
            raise ValueError('Existing output preserved. Use a new name, or --replace for a marked ref2game build.')
        if a.zip and archive.exists() and (not a.replace or not target.exists()):
            raise ValueError('Existing archive preserved. Choose a new name.')
        if a.replace and archive.exists() and not a.zip:
            raise ValueError('Use --zip when replacing a build with an archive, so they stay consistent.')
        cfg_path = project / 'ref2game.json'
        cfg = json.loads(cfg_path.read_text(encoding='utf-8-sig')) if cfg_path.exists() else {}
        with tempfile.TemporaryDirectory(prefix='.ref2game-', dir=out) as temp:
            tmp = Path(temp).resolve()
            assert tmp.parent == out
            stage = tmp / a.name
            stage.mkdir()
            build(project, stage, a.name, cfg)
            zip_path = Path(shutil.make_archive(str(tmp / 'build'), 'zip', tmp, a.name)) if a.zip else None
            previous, previous_zip = tmp / 'previous', tmp / 'previous.zip'
            if target.exists():
                target.rename(previous)
            try:
                if a.zip and archive.exists():
                    archive.rename(previous_zip)
                stage.rename(target)
                if zip_path:
                    zip_path.rename(archive)
            except Exception:
                if target.exists():
                    target.rename(tmp / ('failed-' + uuid.uuid4().hex))
                if previous.exists():
                    previous.rename(target)
                if previous_zip.exists():
                    previous_zip.rename(archive)
                raise
        print(f'packed {target}' + (f'\nzip {archive}' if a.zip else ''))
    except (ValueError, OSError, json.JSONDecodeError) as e:
        ap.exit(2, f'pack: {e}\n')


if __name__ == '__main__':
    main()
