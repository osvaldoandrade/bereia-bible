"""Pinned Chatterbox synthesis through MLX and Metal only."""

from __future__ import annotations

import math
import os
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .constants import (
    ALLOWED_MODEL_FILES,
    ALLOWED_TOKENIZER_FILES,
    TTS_LANGUAGE,
    TTS_MODEL,
    TTS_MODEL_REVISION,
    TTS_SAMPLE_RATE,
    TTS_TOKENIZER,
    TTS_TOKENIZER_REVISION,
)
from .domain import VoiceResolution
from .errors import TTSFailure
from .runtime import validate_mlx_runtime


@dataclass(frozen=True, slots=True)
class SynthesisMetrics:
    """SynthesisMetrics captures one segment's bounded execution result."""

    duration_seconds: float
    processing_seconds: float
    real_time_factor: float
    samples: int

    def metadata(self) -> dict[str, object]:
        return {
            "duration_seconds": round(self.duration_seconds, 6),
            "processing_seconds": round(self.processing_seconds, 6),
            "real_time_factor": round(self.real_time_factor, 4),
            "samples": self.samples,
        }


class Synthesizer(Protocol):
    """Synthesizer is the injectable segment-generation boundary."""

    def warm_model(self) -> None:
        """warm_model downloads and loads immutable weights."""

    def synthesize(
        self,
        segment: dict[str, object],
        voice: VoiceResolution,
        destination: Path,
        seed: int,
    ) -> SynthesisMetrics:
        """synthesize renders exact segment text into a PCM WAV."""


class ChatterboxMLX:
    """ChatterboxMLX owns one sequential, pinned MLX model instance."""

    def __init__(self) -> None:
        self._model: object | None = None
        self._model_path: Path | None = None
        self._tokenizer_path: Path | None = None

    def warm_model(self) -> None:
        """warm_model resolves pinned snapshots and materializes weights on Metal."""

        if self._model is not None:
            return
        validate_mlx_runtime()
        model_path, tokenizer_path = prepare_pinned_snapshots()
        try:
            import huggingface_hub
            from mlx_audio.tts.utils import load_model
        except ImportError as exc:
            raise TTSFailure("pinned MLX-Audio runtime is unavailable") from exc

        original_download = huggingface_hub.snapshot_download

        def pinned_download(*args: object, **kwargs: object) -> str:
            repo_id = kwargs.get("repo_id") or (args[0] if args else None)
            if repo_id != TTS_TOKENIZER:
                raise TTSFailure(f"unexpected unpinned model request: {repo_id!r}")
            return str(tokenizer_path)

        try:
            huggingface_hub.snapshot_download = pinned_download
            self._model = load_model(model_path, lazy=False, strict=True)
        except Exception as exc:
            raise TTSFailure("failed to load pinned Chatterbox weights on MLX Metal") from exc
        finally:
            huggingface_hub.snapshot_download = original_download
        sample_rate = getattr(self._model, "sample_rate", None)
        if sample_rate != TTS_SAMPLE_RATE:
            self._model = None
            raise TTSFailure(f"unexpected Chatterbox sample rate: {sample_rate!r}")
        self._model_path = model_path
        self._tokenizer_path = tokenizer_path

    def synthesize(
        self,
        segment: dict[str, object],
        voice: VoiceResolution,
        destination: Path,
        seed: int,
    ) -> SynthesisMetrics:
        """synthesize passes repository-hydrated text and supported controls unchanged."""

        self.warm_model()
        text = segment.get("text")
        if not isinstance(text, str) or not text:
            raise TTSFailure("cannot synthesize an empty narration segment")
        try:
            import mlx.core as mx

            mx.random.seed(seed)
            started = time.perf_counter()
            kwargs: dict[str, object] = {
                "exaggeration": float(segment["exaggeration"]),
                "cfg_weight": float(segment["cfg_weight"]),
                "temperature": float(segment["temperature"]),
                "repetition_penalty": float(segment["repetition_penalty"]),
                "min_p": float(segment["min_p"]),
                "top_p": float(segment["top_p"]),
                "max_new_tokens": 1_000,
                "lang_code": TTS_LANGUAGE,
                "verbose": False,
            }
            if voice.reference_path is not None:
                kwargs["ref_audio"] = str(voice.reference_path)
            results = list(self._model.generate(text, **kwargs))
            processing_seconds = time.perf_counter() - started
            if len(results) != 1:
                raise TTSFailure("Chatterbox returned an unexpected result count")
            result = results[0]
            samples = _write_wav_atomic(destination, result.audio, int(result.sample_rate))
        except TTSFailure:
            raise
        except Exception as exc:
            raise TTSFailure(
                f"Chatterbox failed for segment {segment.get('segment_id', 'unknown')}"
            ) from exc
        duration = samples / TTS_SAMPLE_RATE
        return SynthesisMetrics(
            duration_seconds=duration,
            processing_seconds=processing_seconds,
            real_time_factor=processing_seconds / duration,
            samples=samples,
        )


def prepare_pinned_snapshots() -> tuple[Path, Path]:
    """prepare_pinned_snapshots downloads only declared immutable model files."""

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise TTSFailure("huggingface-hub is unavailable") from exc
    try:
        model_path = Path(
            snapshot_download(
                repo_id=TTS_MODEL,
                revision=TTS_MODEL_REVISION,
                allow_patterns=list(ALLOWED_MODEL_FILES),
            )
        )
        tokenizer_path = Path(
            snapshot_download(
                repo_id=TTS_TOKENIZER,
                revision=TTS_TOKENIZER_REVISION,
                allow_patterns=list(ALLOWED_TOKENIZER_FILES),
            )
        )
    except Exception as exc:
        raise TTSFailure("failed to download pinned Chatterbox snapshots") from exc
    _validate_snapshot(
        model_path,
        allowed=set(ALLOWED_MODEL_FILES),
        required={"config.json", "model.safetensors", "tokenizer.json", "conds.safetensors"},
    )
    _validate_snapshot(
        tokenizer_path,
        allowed=set(ALLOWED_TOKENIZER_FILES),
        required={"config.json", "model.safetensors"},
    )
    return model_path, tokenizer_path


def _validate_snapshot(path: Path, *, allowed: set[str], required: set[str]) -> None:
    present = {item.name for item in path.iterdir() if item.is_file()}
    if not required <= present:
        missing = ", ".join(sorted(required - present))
        raise TTSFailure(f"pinned model snapshot is incomplete: {missing}")
    unexpected = present - allowed
    if unexpected:
        raise TTSFailure("pinned model snapshot contains undeclared files")
    if any(item.suffix in {".bin", ".pt", ".pth", ".pkl"} for item in path.iterdir()):
        raise TTSFailure("executable or pickle model weights are forbidden")


def _write_wav_atomic(destination: Path, audio: object, sample_rate: int) -> int:
    if sample_rate != TTS_SAMPLE_RATE:
        raise TTSFailure(f"Chatterbox emitted unsupported sample rate {sample_rate}")
    try:
        import numpy as np

        waveform = np.asarray(audio, dtype=np.float32).reshape(-1)
    except Exception as exc:
        raise TTSFailure("Chatterbox emitted an unreadable waveform") from exc
    if waveform.size == 0 or not np.isfinite(waveform).all():
        raise TTSFailure("Chatterbox emitted an empty or non-finite waveform")
    peak = float(np.max(np.abs(waveform)))
    if not math.isfinite(peak) or peak == 0.0:
        raise TTSFailure("Chatterbox emitted silent or invalid audio")
    pcm = (np.clip(waveform, -1.0, 1.0) * 32767.0).astype("<i2")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".wav", dir=destination.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with wave.open(str(temporary_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            handle.writeframes(pcm.tobytes())
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return int(pcm.size)
