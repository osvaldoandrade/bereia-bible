# Threat model 0001 — Bereia Audio local generation

## Scope, assets, and adversary

This model covers the local CLI boundary from repository verse files through
Codex, Hugging Face model downloads, user-supplied WAV files, MLX inference,
FFmpeg, and `output/`. The protected assets are biblical-text integrity, local
filesystem paths, model provenance, Codex credentials held outside the process,
and the operator's machine resources. An adversary can modify untrusted LLM
output, a local reference WAV, a downloaded artifact, or CLI input; the
adversary cannot receive permission to edit `translation/` through this tool.

## STRIDE review

| Threat | Boundary | Control | Residual status |
|---|---|---|---|
| Spoofed Bible coordinate | CLI to source adapter | Validate canonical book identifiers and positive chapter integers; discover the matching repository directory and verify each record coordinate. | Accepted for a single-user local CLI after unit tests. |
| Tampered biblical wording | Codex output to narration plan | Codex returns unit IDs; application code hydrates exact source text; strict coverage and normalized reconstruction run before TTS. | Block generation on the first mismatch. |
| Tampered model weights | Hugging Face to local cache | Pin repository revisions, permit safetensors/config/tokenizer files only, and record file hashes after download. | Endor evidence unavailable on 2026-09-09 UTC; do not redistribute or publish a bundle without a new review. |
| Repudiated generation inputs | CLI to output | Record source commit, dirty flag, prompt/model versions, registry hash, voice hashes, seed, controls, cache key, run ID, and timestamps. | Metadata remains local and user-editable; it is provenance, not a signature. |
| Information disclosure | Process to logs/Codex | Send only public Bible text, narration units, and non-secret registry metadata; never print environment values or command output that may contain tokens. | Codex authentication remains owned by the installed CLI. |
| Denial of service | WAV/model/text to memory and disk | Require M4 Max/128 GB, cap WAV duration/size, validate segment lengths, run sequentially, set subprocess timeouts, and retain restartable segment cache. | A valid full chapter can still consume minutes and several GB by design. |
| Command injection | CLI fields to Codex/FFmpeg | Build argv arrays without `shell=True`; derive output paths only from validated identifiers; pass FFmpeg lists through files created by the application. | Block unsupported paths and malformed values. |
| Elevation through executable model code | Model cache to Python | Load fixed MLX implementation and safetensors; do not enable remote code or deserialize pickle weights. | Python package code remains trusted through the locked dependency review. |
| Silent CPU inference | MLX runtime | Set the default MLX device to GPU, execute a Metal probe, and fail when the device or chip check differs. | No fallback branch exists. |

## Security verification

The implementation must pass the unit rejection paths, lockfile vulnerability
audit, dependency-license report, repository secret scan, model revision check,
and command-construction review before the local milestone closes.

