# Comic Stamps / Symbols

Static built-in assets are grouped by purpose:

- `symbols/` — marks, arrows, hearts, rarity marks, and similar symbols
- `effects/` — visual effect stamps such as rays, motion lines, sweat, and light

Manifest-driven stamp packs use one folder per pack:

```text
stamps/<pack-id>/
  manifest.json
  <runtime assets>
```

Each manifest item must use a unique `id` and an `asset` path relative to its
pack folder. Runtime assets may be lossless WebP or PNG. Keep PNG only when it
is the actual runtime source; do not add preview copies unless a manifest or UI
explicitly references them.
