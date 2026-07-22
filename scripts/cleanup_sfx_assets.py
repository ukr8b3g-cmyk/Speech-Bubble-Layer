"""Batch-apply the shared outline-safe SFX mask cleanup."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from outline_safe_sfx import (
    DEFAULT_PARAMS,
    exclusion_reason,
    load_symbol_asset_ids,
    save_outline_safe_asset,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_DIR = ROOT / "web" / "assets" / "sfx"
DEFAULT_OUTPUT_DIR = ROOT / "tmp" / "outline-safe-sfx"
NODES_PATH = ROOT / "nodes_speech_bubble.py"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", type=Path, default=DEFAULT_ASSET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--only", nargs="*", help="Process only these asset IDs")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    asset_dir = args.asset_dir.resolve()
    output_dir = args.output_dir.resolve()
    symbol_ids = load_symbol_asset_ids(NODES_PATH)
    only = set(args.only or ())
    targets: list[Path] = []
    skipped: list[dict[str, str]] = []

    for source in sorted(asset_dir.glob("*.webp")):
        asset_id = source.stem
        if only and asset_id not in only:
            continue
        reason = exclusion_reason(asset_id, symbol_ids)
        if reason:
            skipped.append({"id": asset_id, "reason": reason})
        else:
            targets.append(source)

    if args.dry_run:
        print(f"targets={len(targets)} skipped={len(skipped)}")
        for source in targets:
            print(f"PROCESS {source.stem}")
        for item in skipped:
            print(f"SKIP {item['id']} ({item['reason']})")
        return 0

    results: list[dict[str, object]] = []
    for source in targets:
        asset_id = source.stem
        result = save_outline_safe_asset(
            source,
            source,
            output_dir / "png" / f"{asset_id}.png",
            output_dir / "preview" / f"{asset_id}.png",
            DEFAULT_PARAMS,
        )
        results.append(
            {
                "id": asset_id,
                "runtimeWebp": f"web/assets/sfx/{source.name}",
                "png": f"png/{asset_id}.png",
                "preview": f"preview/{asset_id}.png",
                **result,
            }
        )
        print(f"Wrote {asset_id}")

    write_manifest(
        output_dir / "manifest.json",
        {
            "schemaVersion": 1,
            "processor": "outline-safe-smoothing",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "sourceRoot": "web/assets/sfx (root files only)",
            "outputRoot": str(output_dir),
            "excluded": skipped,
            "items": results,
        },
    )
    print(f"Completed targets={len(results)} skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

