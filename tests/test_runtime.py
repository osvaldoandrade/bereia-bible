"""Fail-closed Apple hardware and accelerator contracts."""

from __future__ import annotations

import unittest
from types import ModuleType
from unittest.mock import patch

from bereia_audio.domain import HardwareProfile
from bereia_audio.errors import RuntimeContractError
from bereia_audio.runtime import inspect_hardware, validate_host, validate_mlx_runtime


class _FakeMetal:
    @staticmethod
    def is_available() -> bool:
        return True


class _FakeRandom:
    @staticmethod
    def seed(value: int) -> None:
        del value


class _FakeMLX:
    metal = _FakeMetal()
    random = _FakeRandom()
    gpu = "gpu"
    float32 = "float32"
    _device = "cpu"

    @classmethod
    def set_default_device(cls, device: str) -> None:
        cls._device = device

    @classmethod
    def default_device(cls) -> str:
        return cls._device

    @staticmethod
    def ones(shape: tuple[int, int], dtype: str) -> list[int]:
        del dtype
        return [1] * (shape[0] * shape[1])

    @staticmethod
    def sum(values: list[int]) -> int:
        return sum(values)

    @staticmethod
    def eval(value: int) -> None:
        del value


class RuntimeTests(unittest.TestCase):
    def test_current_machine_matches_contract(self) -> None:
        profile = validate_host(inspect_hardware())

        self.assertEqual((profile.chip, profile.memory_gb), ("Apple M4 Max", 128))

    def test_each_unsupported_host_dimension_fails_closed(self) -> None:
        cases = [
            HardwareProfile("Linux", "arm64", "host", "Apple M4 Max", 128),
            HardwareProfile("Darwin", "x86_64", "host", "Apple M4 Max", 128),
            HardwareProfile("Darwin", "arm64", "host", "Apple M3 Max", 128),
            HardwareProfile("Darwin", "arm64", "host", "Apple M4 Max", 127),
        ]
        for profile in cases:
            with (
                self.subTest(profile=profile),
                self.assertRaisesRegex(RuntimeContractError, "unsupported runtime"),
            ):
                validate_host(profile)

    def test_mlx_probe_selects_gpu_and_reports_mps_contract(self) -> None:
        fake = _FakeMLX()
        fake._device = "cpu"
        mlx_package = ModuleType("mlx")
        mlx_package.core = fake
        modules = {"mlx": mlx_package, "mlx.core": fake}
        with (
            patch.dict("sys.modules", modules),
            patch("importlib.metadata.version", return_value="0.5.3"),
        ):
            report = validate_mlx_runtime()

        self.assertEqual(report["runtime"], "mps")
        self.assertEqual(report["framework"], "mlx")
        self.assertEqual(fake.default_device(), "gpu")

    def test_missing_mlx_audio_never_falls_back(self) -> None:
        with (
            patch(
                "importlib.metadata.version",
                side_effect=__import__("importlib.metadata").metadata.PackageNotFoundError,
            ),
            self.assertRaisesRegex(RuntimeContractError, "not installed"),
        ):
            validate_mlx_runtime()

    def test_unavailable_metal_never_falls_back(self) -> None:
        fake = _FakeMLX()
        fake.metal = unittest.mock.MagicMock()
        fake.metal.is_available.return_value = False
        mlx_package = ModuleType("mlx")
        mlx_package.core = fake
        modules = {"mlx": mlx_package, "mlx.core": fake}
        with (
            patch.dict("sys.modules", modules),
            patch("importlib.metadata.version", return_value="0.5.3"),
            self.assertRaisesRegex(RuntimeContractError, "CPU fallback is forbidden"),
        ):
            validate_mlx_runtime()


if __name__ == "__main__":
    unittest.main()
