# Delivery

Deliver the requested mode: asset files, a playable prototype, or a polished scene. Keep verified results separate from missing checks.

## Portable packaging

From the browser/asset project root:

```text
python "<skill>/scripts/pack.py" --name my-game --zip
```

Use a portable name containing letters, digits, hyphens and underscores. The packer stages the result before replacing anything. Existing output is preserved unless `--replace` targets a marked ref2game build. If an archive already exists, include `--zip` on replacement to keep it consistent. An older unmarked build must be preserved or a new output name chosen; do not delete it to bypass the check.

| Path | Contents |
|---|---|
| `game/` | Playable browser build with reload polling and overlay disabled; omitted for assets mode |
| `assets/textures/` | Prepared textures |
| `assets/source/` | All generated source art, including sheets with different names from final sprites |
| `assets/manifest.json` | Dimensions, crops and other texture metadata |
| `project/` | Editable live code, art/raw/gen/prompts/requests/logs, study, project settings and reference when present |
| `checksums.json` | SHA-256 inventory of packaged files |
| `README.md` | Mode, controls where available, run instructions and verification caveat |

The archive intentionally contains the project's prompts and reference images to make continued editing possible. Keep credentials and unrelated files outside these project directories. Packing is not a publishing action and does not certify gameplay.

## Verify the extracted result

1. Extract the archive into a fresh directory.
2. Check required sources and checksums. For assets mode, inspect/import the textures in the intended target.
3. For playable builds, serve the extracted `game/` directory over loopback HTTP.
4. Run `livecheck.mjs --url <actual-url>/index.html --scenario <project-scenario.json>`. Do not use hot-reload verification on a static build.
5. Inspect the rendered frame and report the scenario results. A passing load-only smoke test is not gameplay acceptance.

For native engines, use their export/package workflow and run that output. Bundled scripts do not implement Godot, Pyxel, Unity or Phaser exporters. Do not create a browser detour for an explicitly requested native game.

## Hand-back

Give the output link, playable URL if available, controls and what to try, completed changes, actual verification results and remaining gaps. Include only applicable critic findings. Make a video only when asked. State that a local preview depends on its server process; do not promise indefinite availability.
