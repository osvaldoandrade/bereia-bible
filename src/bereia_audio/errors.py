"""Typed failures exposed by the CLI."""


class BereiaAudioError(Exception):
    """BereiaAudioError carries the stable CLI exit code for a failed boundary."""

    exit_code = 1


class RuntimeContractError(BereiaAudioError):
    """RuntimeContractError reports unsupported hardware or missing local tools."""

    exit_code = 3


class SourceError(BereiaAudioError):
    """SourceError reports an invalid or unavailable Bereia source projection."""

    exit_code = 4


class NarrationError(BereiaAudioError):
    """NarrationError reports invalid LLM metadata or failed text integrity."""

    exit_code = 5


class TTSFailure(BereiaAudioError):
    """TTSFailure reports model resolution, loading, or synthesis failure."""

    exit_code = 6


class MasteringError(BereiaAudioError):
    """MasteringError reports an FFmpeg or final-audio validation failure."""

    exit_code = 7
