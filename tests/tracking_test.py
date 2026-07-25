import importlib.util
import sys
import types
from pathlib import Path


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_tracking_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeFont:
    size = 100


class FakeDraw:
    def __init__(self):
        self.calls = []

    def textlength(self, text, font=None):
        if text == "AV":
            return 18.0
        return float(len(text) * 10)

    def text(self, position, text, **kwargs):
        self.calls.append((position, text, kwargs))


font = FakeFont()
measure = FakeDraw()

assert module._spaced_text_width(measure, "AV", font, 0) == 18.0
assert module._spaced_text_width(measure, "AB", font, -5) == 15.0
assert module._spaced_text_width(measure, "AB", font, 5) == 25.0
assert module._spaced_text_width(measure, "A", font, 50) == 10.0

zero_draw = FakeDraw()
assert module._draw_spaced_text(zero_draw, 0, 0, "AV", font, "black", 0, "white", 0) == 18.0
assert [call[1] for call in zero_draw.calls] == ["AV"]

spaced_draw = FakeDraw()
assert module._draw_spaced_text(spaced_draw, 0, 0, "AB", font, "black", 0, "white", 5) == 25.0
assert [call[1] for call in spaced_draw.calls] == ["A", "B"]

assert module._wrap_lines(measure, "ABC", font, 30, 5) == ["AB", "C"]
assert module._wrap_lines(measure, "ABC", font, 30, -2) == ["ABC"]
assert module._wrap_lines(measure, "AB\nCD", font, 100, 20) == ["AB", "CD"]
assert module._vertical_glyph_rotation("2") == 0
assert module._vertical_glyph_rotation("ー") == module.math.pi / 2
assert module._vertical_glyph_rotation("－") == module.math.pi / 2

print("tracking measurement, drawing, and wrapping: pass")
