import datetime
import hashlib
import json
import math
import mimetypes
import os
import re
import tempfile
import uuid
from pathlib import Path

from PIL import ImageFont

try:
    from fontTools.ttLib import TTFont
except ImportError:  # Pillow remains a usable fallback in minimal ComfyUI installs.
    TTFont = None

from .nodes_speech_bubble import (
    NODE_CLASS_MAPPINGS as SPEECH_BUBBLE_NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SPEECH_BUBBLE_NODE_DISPLAY_NAME_MAPPINGS,
    get_frame_asset_catalog,
    get_shape_asset_catalog,
    get_sfx_asset_catalog,
    reload_asset_catalogs,
)
from .nodes_frame_cleanup import (
    NODE_CLASS_MAPPINGS as FRAME_TOOL_NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as FRAME_TOOL_NODE_DISPLAY_NAME_MAPPINGS,
)

NODE_CLASS_MAPPINGS = {
    **SPEECH_BUBBLE_NODE_CLASS_MAPPINGS,
    **FRAME_TOOL_NODE_CLASS_MAPPINGS,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **SPEECH_BUBBLE_NODE_DISPLAY_NAME_MAPPINGS,
    **FRAME_TOOL_NODE_DISPLAY_NAME_MAPPINGS,
}


_FONT_CACHE = None
_USER_PRESET_FILE = "speech-bubble/presets.json"
_USER_PRESET_LIMIT = 200
_BASE_PRESET_IDS = {
    "base-oval",
    "base-oval-alt",
    "base-box",
    "base-thought",
    "base-heart",
    "base-hexagon",
}
_SHAPE_NUMBER_RANGES = {
    "shape_intensity": (0, 100),
    "shape_asymmetry": (0, 100),
    "shape_seed": (0, 4294967295),
    "shape_roundness": (0, 100),
    "spike_count": (5, 32),
    "valley_concavity": (0, 100),
    "lobe_count": (5, 20),
    "lobe_depth": (0, 100),
    "shape_softness": (0, 100),
}
_PREFERRED_FONTS = (
    "meiryo",
    "yu gothic",
    "noto sans cjk jp",
    "noto sans jp",
    "hiragino",
    "segoe ui",
    "arial",
    "helvetica",
    "times new roman",
    "dejavu sans",
    "liberation sans",
)

_FONT_LANGUAGE_META = {
    "ja": {"label": "日本語", "sample": "文字もじモジ"},
    "zh-hans": {"label": "简体中文", "sample": "字体示例"},
    "zh-hant": {"label": "繁體中文", "sample": "字體範例"},
    "ko": {"label": "한국어", "sample": "서체견본"},
    "latin": {"label": "Latin", "sample": "Sample Aa"},
    "arabic": {"label": "العربية", "sample": "أبجدية"},
    "hebrew": {"label": "עברית", "sample": "אבגדה"},
    "devanagari": {"label": "देवनागरी", "sample": "अक्षर"},
    "emoji": {"label": "Emoji", "sample": "😀 ★ ♪"},
    "symbol": {"label": "Symbols", "sample": "● ◆ ♪"},
    "other": {"label": "Other", "sample": "Sample"},
}

_FONT_LANGUAGE_HINTS = {
    "emoji": ("emoji", "color emoji"),
    "symbol": ("wingdings", "webdings", "symbol", "dingbat"),
    "ja": (
        "japanese", " cjk jp", " jp ", "meiryo", "yu gothic", "yu mincho",
        "ms gothic", "ms mincho", "biz ud", "hiragino", "kozuka gothic pr6n",
        "kozuka mincho pr6n", "ipaex", "ipagothic", "ipamincho",
    ),
    "ko": (
        "korean", " cjk kr", " kr ", "malgun", "gulim", "dotum", "batang",
        "gungsuh", "nanum", "noto sans kr", "noto serif kr",
    ),
    "zh-hans": (
        "simplified chinese", " cjk sc", " sc ", "hans", "simsun", "simhei",
        "simkai", "simfang", "microsoft yahei", "dengxian", "fangsong", "kaiti",
        "noto sans sc", "noto serif sc",
    ),
    "zh-hant": (
        "traditional chinese", " cjk tc", " tc ", "hant", "mingliu",
        "microsoft jhenghei", "dfkai", "noto sans tc", "noto serif tc",
    ),
    "arabic": ("arabic", "andalus", "sakkal", "urdu", "quran", "scheherazade"),
    "hebrew": ("hebrew", "aharoni", "david clm", "frank ruehl", "miriam", "nachlieli"),
    "devanagari": ("devanagari", "mangal", "kokila", "aparajita", "utsaah"),
}


def _glyph_signature(font, character):
    mask = font.getmask(character)
    return mask.size, bytes(mask)


def _font_supports(font, character, missing_signature):
    try:
        return _glyph_signature(font, character) != missing_signature
    except (OSError, ValueError):
        return False


def _font_language(family, style, font):
    searchable = f" {family} {style} ".lower()
    for language in ("emoji", "symbol", "ja", "ko", "zh-hans", "zh-hant", "arabic", "hebrew", "devanagari"):
        if any(hint in searchable for hint in _FONT_LANGUAGE_HINTS[language]):
            return language
    if re.search(r"[\u3040-\u30ff]", family):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", family):
        return "ko"
    try:
        missing = _glyph_signature(font, chr(0x10FFFF))
    except (OSError, ValueError):
        return "other"
    supports = lambda character: _font_supports(font, character, missing)
    if supports("한"):
        return "ko"
    if supports("あ") and supports("ア"):
        return "ja"
    if supports("汉"):
        return "zh-hans"
    if supports("漢"):
        return "zh-hant"
    if supports("अ"):
        return "devanagari"
    if supports("ا") and not supports("A"):
        return "arabic"
    if supports("א") and not supports("A"):
        return "hebrew"
    if supports("A"):
        return "latin"
    return "other"


def _font_roots():
    roots = []
    if os.name == "nt":
        roots.extend(
            [
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
            ]
        )
    elif os.sys.platform == "darwin":
        roots.extend([Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"])
    else:
        roots.extend(
            [
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
                Path.home() / ".local/share/fonts",
            ]
        )
    return [root for root in roots if root.is_dir()]


def _font_name_table_text(path, name_ids):
    """Read Unicode family/style names without Pillow's Windows codepage loss."""
    if TTFont is None:
        return None
    try:
        table = TTFont(str(path), lazy=True)["name"]
    except Exception:
        return None

    records = []
    for record in table.names:
        if record.nameID not in name_ids:
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if not value or value.count("?") * 2 >= len(value):
            continue
        language_rank = 0 if record.langID in {0x411, 0x409} else 1
        platform_rank = 0 if record.platformID == 3 else 1 if record.platformID == 0 else 2
        records.append((language_rank, platform_rank, value))
    return min(records, default=(None, None, None))[2]


def _font_display_names(path, fallback_family, fallback_style):
    family = _font_name_table_text(path, (16, 1)) or fallback_family
    style = _font_name_table_text(path, (17, 2)) or fallback_style
    return family, style


def _system_fonts():
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE
    fonts = []
    seen = set()
    for root in _font_roots():
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".ttf", ".otf", ".ttc", ".otc"}:
                continue
            normalized = str(path.resolve())
            if normalized.lower() in seen:
                continue
            seen.add(normalized.lower())
            try:
                font = ImageFont.truetype(normalized, 12)
                fallback_family, fallback_style = font.getname()
            except (OSError, ValueError):
                continue
            family, style = _font_display_names(normalized, fallback_family, fallback_style)
            name = family if style in {"Regular", "Normal", "Book"} else f"{family} — {style}"
            lower_name = name.lower()
            rank = next((index for index, preferred in enumerate(_PREFERRED_FONTS) if preferred in lower_name), 999)
            language = _font_language(family, style, font)
            try:
                missing = _glyph_signature(font, chr(0x10FFFF))
                supports_latin = _font_supports(font, "A", missing)
            except (OSError, ValueError):
                supports_latin = language == "latin"
            meta = _FONT_LANGUAGE_META[language]
            fonts.append(
                {
                    "id": hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20],
                    "name": name,
                    "family": family,
                    "style": style,
                    "path": normalized,
                    "recommended": rank < 999,
                    "rank": rank,
                    "language": language,
                    "language_label": meta["label"],
                    "sample": meta["sample"],
                    "supports_latin": supports_latin,
                    "primary_style": style.lower() in {"regular", "normal", "book", "roman"},
                }
            )
    fonts.sort(key=lambda item: (item["rank"], item["name"].lower(), item["path"].lower()))
    for item in fonts:
        item.pop("rank", None)
    _FONT_CACHE = fonts
    return _FONT_CACHE


def _public_font(font):
    """Keep filesystem paths internal while preserving stable browser font IDs."""
    return {key: value for key, value in font.items() if key != "path"}


def _font_by_id(font_id):
    return next((font for font in _system_fonts() if font["id"] == font_id), None)


def _preset_storage_path(request, server):
    manager = getattr(server, "user_manager", None)
    if manager is not None:
        path = manager.get_request_user_filepath(request, _USER_PRESET_FILE)
        if path:
            return Path(path)
    import folder_paths

    return Path(folder_paths.get_user_directory()) / "default" / _USER_PRESET_FILE


def _read_user_presets(path):
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    presets = data.get("presets", []) if isinstance(data, dict) else []
    return presets if isinstance(presets, list) else []


def _write_user_presets(path, presets):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "presets": presets[:_USER_PRESET_LIMIT]}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink(missing_ok=True)


def _bounded_number(value, minimum, maximum, default):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return max(minimum, min(maximum, number))


def _sanitize_path_points(points):
    if not isinstance(points, list) or not 3 <= len(points) <= 256:
        raise ValueError("A user preset needs 3 to 256 path points")
    clean = []
    for point in points:
        if not isinstance(point, dict):
            raise ValueError("Invalid path point")
        x = _bounded_number(point.get("x"), -10, 10, None)
        y = _bounded_number(point.get("y"), -10, 10, None)
        if x is None or y is None:
            raise ValueError("Path points require finite x/y values")
        clean.append(
            {
                "x": x,
                "y": y,
                "in_x": _bounded_number(point.get("in_x"), -10, 10, x),
                "in_y": _bounded_number(point.get("in_y"), -10, 10, y),
                "out_x": _bounded_number(point.get("out_x"), -10, 10, x),
                "out_y": _bounded_number(point.get("out_y"), -10, 10, y),
            }
        )
    return clean


def _sanitize_user_preset(value, existing=None):
    if not isinstance(value, dict):
        raise ValueError("Invalid user preset")
    name = str(value.get("name") or "").strip()[:80]
    if not name:
        raise ValueError("Preset name is required")
    raw_id = str(value.get("id") or "")
    preset_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw_id).strip("-")[:80]
    if not preset_id:
        preset_id = f"user-{uuid.uuid4().hex}"
    elif not preset_id.startswith("user-"):
        preset_id = f"user-{preset_id}"[:80]
    shape_data = value.get("shape_data")
    if not isinstance(shape_data, dict):
        raise ValueError("Missing shape data")
    clean_shape = {
        "shape": str(shape_data.get("shape") or "custom")[:32],
        "path_points": _sanitize_path_points(shape_data.get("path_points")),
        "valley_style": "straight" if shape_data.get("valley_style") == "straight" else "concave",
    }
    for key, (minimum, maximum) in _SHAPE_NUMBER_RANGES.items():
        if key in shape_data:
            default = 1 if key == "shape_seed" else minimum
            number = _bounded_number(shape_data.get(key), minimum, maximum, default)
            clean_shape[key] = int(round(number)) if key in {"shape_seed", "spike_count", "lobe_count"} else number
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    base_preset = str(value.get("base_preset_id") or "base-oval")
    if base_preset not in _BASE_PRESET_IDS:
        base_preset = "base-oval"
    return {
        "id": preset_id,
        "name": name,
        "base_preset_id": base_preset,
        "aspect_ratio": _bounded_number(value.get("aspect_ratio"), 0.1, 10, 1.5),
        "shape_data": clean_shape,
        "created_at": (existing or {}).get("created_at") or str(value.get("created_at") or now),
        "updated_at": now,
    }


try:
    from aiohttp import web
    from server import PromptServer

    @PromptServer.instance.routes.get("/speech_bubble/fonts")
    async def speech_bubble_fonts(_request):
        return web.json_response({"fonts": [_public_font(font) for font in _system_fonts()]})

    @PromptServer.instance.routes.get("/speech_bubble/font-file/{font_id}")
    async def speech_bubble_font_file(request):
        font = _font_by_id(str(request.match_info.get("font_id") or ""))
        if not font:
            raise web.HTTPNotFound()
        content_type = mimetypes.guess_type(font["path"])[0] or "application/octet-stream"
        return web.FileResponse(font["path"], headers={"Content-Type": content_type})

    @PromptServer.instance.routes.get("/speech_bubble/frame-assets")
    async def speech_bubble_frame_assets(_request):
        return web.json_response(get_frame_asset_catalog())

    @PromptServer.instance.routes.get("/speech_bubble/assets/sfx")
    async def speech_bubble_sfx_assets(_request):
        return web.json_response(get_sfx_asset_catalog())

    @PromptServer.instance.routes.get("/speech_bubble/assets/shapes")
    async def speech_bubble_shape_assets(_request):
        return web.json_response(get_shape_asset_catalog())

    @PromptServer.instance.routes.post("/speech_bubble/assets/reload")
    async def speech_bubble_reload_assets(_request):
        reload_asset_catalogs()
        response = get_sfx_asset_catalog()
        response["frameCatalog"] = get_frame_asset_catalog()
        response["shapeCatalog"] = get_shape_asset_catalog()
        return web.json_response(response)

    @PromptServer.instance.routes.get("/speech_bubble/presets")
    async def speech_bubble_presets(request):
        path = _preset_storage_path(request, PromptServer.instance)
        return web.json_response({"version": 1, "presets": _read_user_presets(path)})

    @PromptServer.instance.routes.post("/speech_bubble/presets")
    async def speech_bubble_update_presets(request):
        try:
            payload = await request.json()
            action = str(payload.get("action") or "upsert")
            path = _preset_storage_path(request, PromptServer.instance)
            presets = [preset for preset in _read_user_presets(path) if isinstance(preset, dict)]
            if action == "delete":
                preset_id = str(payload.get("id") or "")
                presets = [preset for preset in presets if preset.get("id") != preset_id]
            elif action == "import":
                imported = payload.get("presets")
                if not isinstance(imported, list):
                    raise ValueError("Import needs a presets array")
                by_id = {preset.get("id"): preset for preset in presets if isinstance(preset, dict)}
                for value in imported[:_USER_PRESET_LIMIT]:
                    source_id = str(value.get("id") or "") if isinstance(value, dict) else ""
                    clean = _sanitize_user_preset(value, by_id.get(source_id))
                    by_id[clean["id"]] = clean
                presets = list(by_id.values())
            else:
                value = payload.get("preset")
                source_id = str(value.get("id") or "") if isinstance(value, dict) else ""
                existing = next((preset for preset in presets if preset.get("id") == source_id), None)
                clean = _sanitize_user_preset(value, existing)
                presets = [preset for preset in presets if preset.get("id") != clean["id"]]
                presets.append(clean)
            presets = presets[-_USER_PRESET_LIMIT:]
            _write_user_presets(path, presets)
            return web.json_response({"version": 1, "presets": presets})
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            raise web.HTTPBadRequest(text=str(error)) from error
except (ImportError, AttributeError):
    pass

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
