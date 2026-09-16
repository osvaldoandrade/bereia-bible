"""Fail-closed validation of the single supported Apple runtime."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .constants import TTS_PACKAGE, TTS_PACKAGE_VERSION
from .domain import HardwareProfile
from .errors import RuntimeContractError


def inspect_hardware() -> HardwareProfile:
    """inspect_hardware reads only non-sensitive fields from System Profiler."""

    if platform.system() != "Darwin":
        return HardwareProfile(platform.system(), platform.machine(), "unknown", "unknown", 0)
    try:
        process = subprocess.run(
            ["system_profiler", "SPHardwareDataType", "-json"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        records = json.loads(process.stdout).get("SPHardwareDataType")
        record = records[0] if isinstance(records, list) and records else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise RuntimeContractError("cannot inspect Apple hardware contract") from exc
    memory_match = re.fullmatch(r"(\d+) GB", str(record.get("physical_memory", "")))
    return HardwareProfile(
        system=platform.system(),
        machine=platform.machine(),
        model_name=str(record.get("machine_name", "unknown")),
        chip=str(record.get("chip_type", "unknown")),
        memory_gb=int(memory_match.group(1)) if memory_match else 0,
    )


def validate_host(profile: HardwareProfile | None = None) -> HardwareProfile:
    """validate_host rejects every machine outside the requested M4 Max contract."""

    selected = profile or inspect_hardware()
    failures = []
    if selected.system != "Darwin":
        failures.append("operating system must be macOS")
    if selected.machine != "arm64":
        failures.append("architecture must be arm64")
    if selected.chip != "Apple M4 Max":
        failures.append("chip must be Apple M4 Max")
    if selected.memory_gb < 128:
        failures.append("unified memory must be at least 128 GB")
    if sys.version_info[:2] != (3, 12):
        failures.append("Python must be 3.12")
    if failures:
        raise RuntimeContractError("unsupported runtime: " + "; ".join(failures))
    return selected


def require_tool(name: str) -> Path:
    """require_tool resolves one executable or fails the runtime boundary."""

    executable = shutil.which(name)
    if executable is None:
        raise RuntimeContractError(f"required executable is unavailable: {name}")
    return Path(executable).resolve()


def validate_audio_tools() -> dict[str, str]:
    """validate_audio_tools requires both FFmpeg generation and probing."""

    return {name: str(require_tool(name)) for name in ("ffmpeg", "ffprobe")}


def validate_mlx_runtime() -> dict[str, str]:
    """validate_mlx_runtime selects MLX GPU and rejects unavailable Metal."""

    try:
        installed = importlib.metadata.version(TTS_PACKAGE)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeContractError(f"{TTS_PACKAGE} is not installed") from exc
    if installed != TTS_PACKAGE_VERSION:
        raise RuntimeContractError(
            f"{TTS_PACKAGE} version must be {TTS_PACKAGE_VERSION}, found {installed}"
        )
    try:
        import mlx.core as mx
    except ImportError as exc:
        raise RuntimeContractError("MLX is not installed") from exc
    try:
        if not mx.metal.is_available():
            raise RuntimeContractError("MLX Metal is unavailable; CPU fallback is forbidden")
        mx.set_default_device(mx.gpu)
        probe = mx.sum(mx.ones((32, 32), dtype=mx.float32))
        mx.eval(probe)
        if "gpu" not in str(mx.default_device()).lower():
            raise RuntimeContractError("MLX default device is not GPU; CPU fallback is forbidden")
    except RuntimeContractError:
        raise
    except Exception as exc:
        raise RuntimeContractError("MLX Metal execution probe failed") from exc
    return {
        "runtime": "mps",
        "framework": "mlx",
        "accelerator": "metal",
        "mlx_audio_version": installed,
    }


def inspect_environment(*, include_mlx: bool = True) -> dict[str, object]:
    """inspect_environment returns a non-secret report and raises on incompatibility."""

    hardware = validate_host()
    report: dict[str, object] = {
        "supported": True,
        "hardware": {
            "system": hardware.system,
            "architecture": hardware.machine,
            "model": hardware.model_name,
            "chip": hardware.chip,
            "memory_gb": hardware.memory_gb,
        },
        "python": platform.python_version(),
        "tools": validate_audio_tools(),
        "codex": str(require_tool("codex")),
    }
    if include_mlx:
        report.update(validate_mlx_runtime())
    return report
