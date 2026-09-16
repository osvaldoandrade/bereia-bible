"""Setup-time pinned-model smoke test using repository-owned Genesis text."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .bible import BibleRepository, find_repository_root
from .domain import VoiceResolution
from .integrity import validate_reconstruction
from .mastering import probe_audio
from .tts import ChatterboxMLX


def main() -> int:
    """main loads Chatterbox and synthesizes one real Bereia verse on MLX Metal."""

    root = find_repository_root()
    chapter = BibleRepository(root).get_chapter("GEN", 1)
    source_text = chapter.verses[0].text
    segment: dict[str, object] = {
        "segment_id": "setup-smoke",
        "text": source_text,
        "exaggeration": 0.35,
        "cfg_weight": 0.3,
        "temperature": 0.8,
        "repetition_penalty": 1.2,
        "min_p": 0.05,
        "top_p": 1.0,
    }
    validate_reconstruction(source_text, str(segment["text"]))
    voice = VoiceResolution(
        character="narrator",
        requested_voice_id="narrator",
        resolved_voice_id="narrator",
        reference_path=None,
        reference_label=None,
        reference_sha256="model-default",
        fallback=False,
        fallback_reason=None,
    )
    synthesizer = ChatterboxMLX()
    synthesizer.warm_model()
    with tempfile.TemporaryDirectory(prefix="bereia-audio-smoke-") as temporary:
        destination = Path(temporary) / "smoke.wav"
        metrics = synthesizer.synthesize(segment, voice, destination, seed=1234)
        duration = probe_audio(destination, expected_codec="pcm_s16le")
    print(
        json.dumps(
            {
                "smoke": "passed",
                "source": "Bereia GEN 1:1",
                "runtime": "mps",
                "framework": "mlx",
                "duration_seconds": round(duration, 3),
                "processing_seconds": round(metrics.processing_seconds, 3),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
