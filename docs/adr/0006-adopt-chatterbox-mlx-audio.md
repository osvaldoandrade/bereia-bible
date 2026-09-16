# ADR-0006 — Adopt Chatterbox through MLX-Audio for local Bible narration

## Status

Accepted on 2026-09-09 UTC.

## Decision request

The repository maintainer approved a local Apple M4 Max audio-production
context on 2026-09-09 UTC. The implementation must move Genesis 1 from zero
generated chapter artifacts to `narration.json`, `metadata.json`, `chapter.wav`,
and `chapter.m4a` by the end of the implementation session, measured by the
commands in `docs/bereia-audio.md`, at the cost of one 37-package Python runtime
lock and approximately 3.2 GB of pinned Chatterbox and tokenizer weights. The
repository maintainer owns the dependency and generated-output lifecycle.

## Context

The repository owns the Bereia Version text as one JSON record per verse. Audio
production needs a Portuguese multilingual model, stable character voices,
chapter-level narrative context, and a hard guarantee that the narration model
cannot rewrite Scripture. The target machine is one MacBook Pro with an Apple
M4 Max and 128 GB of unified memory. CUDA, remote synthesis, CPU inference, and
distributed processing are outside this decision.

Chatterbox publishes a multilingual model with voice cloning and explicit
`exaggeration` and `cfg_weight` controls. MLX-Audio 0.5.3 ports that model to
Apple MLX and loads safetensor weights without a CUDA runtime. The lock contains
37 resolved Python packages on Python 3.12. The Endor package lookup could not
authenticate on 2026-09-09 UTC; the implementation therefore pins the package,
locks transitives, records artifact revisions, runs an OSV-compatible audit,
and keeps that evidence gap explicit.

## Decision

Audio Production will depend directly on `mlx-audio==0.5.3` and will load
`mlx-community/chatterbox-fp16` at revision
`4923fcca09086356aeab5191a2348c5a17a23694`. It will load
`mlx-community/S3TokenizerV2` at revision
`e0c9886f0e1c35ae85b1f27277416fb19fc72bec`. The adapter will resolve both
snapshots before model construction, restrict model files to safetensors and
configuration/tokenizer data, and force the MLX GPU device. It will not set or
permit a CPU fallback.

The LLM director will return ordered source-unit identifiers plus narration
metadata. Application code, not the LLM, will materialize every segment's text
from the repository-owned units. Generation stops before TTS unless the units
cover the chapter exactly once in source order and normalized reconstruction
equals normalized source text.

The synthesizer must receive an approved reference from a native Brazilian
Portuguese narrator. The built-in Chatterbox narrator is forbidden: listening
review found a foreign accent and unsuitable prosody. Absence of the approved
reference is a hard generation failure, not a fallback condition.

## Reversibility

The decision is reversible within one local change: remove the Python package,
the Audio Production source tree, and the ignored generated/cache directories.
No rollback edits `translation/` or any source record. Existing WAV/M4A files
remain derived artifacts and can be moved out of `output/` before rollback.

## Consequences

The positive consequence is a native Metal execution path with zero CUDA and
zero CPU-inference branches in the application. The generated metadata pins the
source commit, narration prompt, package version, model revision, tokenizer
revision, seed, voice hashes, and generation parameters for each chapter.

The negative consequence is a larger local dependency graph and two model
downloads. `mlx-community/S3TokenizerV2` does not declare a license in its own
model card; its declared base model, `FunAudioLLM/CosyVoice2-0.5B`, uses
Apache-2.0. This project downloads but does not redistribute either weight set,
records the gap, and requires a new review before publishing weights or a binary
bundle.

## Alternatives considered

1. Use the upstream `chatterbox-tts` PyTorch package on MPS. Rejected because
   the upstream loader contains a CPU fallback when MPS is unavailable and the
   package's documented development baseline is Debian/Python 3.11; both facts
   increase the chance of violating the fail-closed Apple-only contract.
2. Maintain a repository-local MLX port. Rejected because it would duplicate a
   0.5B-parameter model implementation and transfer upstream parity, security,
   and numerical-correctness work to this repository.
3. Call a hosted TTS API. Rejected because it crosses the local-only boundary,
   introduces credentials and usage cost, and does not satisfy the requested
   M4 Max runtime.

## References

- T-2: write the narrative first.
- T-5: a new dependency requires this ADR.
- T-7: model downloads and the Codex director cross explicit network boundaries.
- `docs/bereia-audio.md`
- `docs/threat-models/0001-bereia-audio.md`
