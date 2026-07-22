# Implementation Status

The requested changes are already applied in this package. No Codex patch step is required.

For review or further modification, preserve these contracts:

1. Supported frame folders are discovered from `web/assets/frames/*/manifest.json`.
2. `edge-repeat` and `decorated-border` may omit `runtimeAsset` when all required parts are present.
3. JavaScript editor rendering and Python/Pillow rendering must use equivalent layout calculations.
4. A decorated border draws its procedural base line once, then places independent decorations.
5. Built-in bubble shapes are loaded from `web/assets/shapes/manifest.json` and serialized as `path_points`.
6. Preview messages must be sent after rendering and must carry monotonic revision numbers.
7. Stale asynchronous preview loads must never replace newer previews.

Run all files under `tests/` after changes.
