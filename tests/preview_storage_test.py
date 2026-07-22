import importlib.util
import sys
import tempfile
import types
from pathlib import Path

import torch


with tempfile.TemporaryDirectory() as temporary_directory:
    folder_paths = types.SimpleNamespace(get_output_directory=lambda: temporary_directory)
    sys.modules["folder_paths"] = folder_paths
    module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
    spec = importlib.util.spec_from_file_location("speech_bubble_preview_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first = module._persistent_preview_images(torch.zeros((1, 8, 6, 3)), "node/2")
    preview_path = Path(temporary_directory) / "speech_bubble_preview" / first[0]["filename"]
    first_bytes = preview_path.read_bytes()
    second = module._persistent_preview_images(torch.ones((1, 8, 6, 3)), "node/2")

    assert first[0]["type"] == "output"
    assert first[0]["filename"] == "speech_bubble_node_2_0.png"
    assert second[0]["filename"] == first[0]["filename"]
    assert second[0]["cache_key"]
    assert preview_path.read_bytes() != first_bytes
    assert len(list(preview_path.parent.glob("*.png"))) == 1

    keyed = module._persistent_preview_images(torch.zeros((1, 8, 6, 3)), "2", "workflow-a")
    assert keyed[0]["filename"] == "speech_bubble_workflow-a_2_0.png"

    assert module.SpeechBubbleLayer.INPUT_TYPES()["hidden"]["unique_id"] == "UNIQUE_ID"
    assert module.SpeechBubbleLayer.INPUT_TYPES()["optional"]["preview_key"][1]["default"] == ""
    execution = module.SpeechBubbleLayer().execute(
        torch.zeros((1, 8, 6, 3)),
        '{"version": 1, "elements": []}',
        "",
        1,
        preview_key="workflow-a",
        unique_id="42",
    )
    assert execution["ui"]["images"][0]["type"] == "output"
    assert execution["ui"]["images"][0]["filename"] == "speech_bubble_workflow-a_42_0.png"
    assert len(execution["result"]) == 2

print("preview storage: pass")
