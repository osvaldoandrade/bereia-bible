# Bereia Audio generation runbook

## Symptom

`bereia-audio` exits nonzero, leaves a missing chapter master, or reports an
invalid narration/cache/runtime artifact on the local M4 Max.

## Triage

1. Run `.venv/bin/bereia-audio inspect` and resolve the first failed hardware,
   MLX, Codex, FFmpeg, model-revision, or voice check.
2. Read the final JSON event on standard error and note its `run_id`, `stage`,
   and error category; do not paste environment variables into an issue.
3. Inspect `output/<BOOK>/<CHAPTER>/narration.json` before audio generation and
   run the unit suite when the failure category is narration or integrity.
4. Inspect `metadata.json` and `segments/*.cache.json` when a rerun unexpectedly
   misses cache.

## Mitigation

1. Preserves a manually reviewed plan. Copy `narration.json` outside `output/`,
   then run `.venv/bin/bereia-audio analyze --book GEN --chapter 1` only when
   the existing plan is stale or invalid.
2. Resumes a partial generation. Run `.venv/bin/bereia-audio generate --book GEN
   --chapter 1`; matching segment fingerprints remain cached.
3. Diagnoses a reference file. Run `ffprobe -v error voices/narrator.wav` and
   replace the file when its format or duration violates the documented range.
4. Repairs setup without changing source text. Run `./scripts/setup.sh`; the
   script reuses exact package and model revisions and stops on a Metal failure.

## Rollback

Move `output/GEN/001` to a timestamped directory outside `output/`, then revert
only the Audio Production paths listed in ADR-0006. This action leaves every
file under `translation/` unchanged.

## Post-incident

Record a repeatable implementation defect under
`docs/incidents/YYYY-MM-DD-bereia-audio-<stage>.md` with the redacted JSON event,
exact command, model revisions, and source commit.

