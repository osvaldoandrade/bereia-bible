# Audio Production glossary

Audio Production converts the immutable Bereia Version projection into local
reviewable narration and audio artifacts. Osvaldo Andrade owns every term and
invariant below; the next glossary review is due 2026-12-09 UTC.

| Term | Definition and example | Rejected synonym | Invariants |
|---|---|---|---|
| Source verse | The `referencia` coordinate and exact `texto_bv` read from one repository JSON record; for example `Gen.1.3`. | “TTS text,” because synthesis is downstream and cannot own wording. | Coordinate is unique; text is non-empty; adapter never writes the record. |
| Source chapter | One book/chapter projection whose verses are sorted by numeric verse. | “Document,” because the source consists of verse records rather than the rendered Markdown. | All verses share book/chapter; verse numbers are unique and strictly increasing. |
| Source unit | A contiguous, immutable slice of source-chapter text offered to the director by identifier. | “Sentence,” because quote boundaries and verse boundaries can create non-sentence units. | Units concatenate byte-for-byte to source text and each unit belongs to one verse. |
| Narration plan | Versioned metadata that groups source units and assigns speaker, character, voice, tone, pace, pauses, and Chatterbox controls. | “Script,” because a script suggests editable wording. | Unit identifiers cover the chapter once in order; hydrated text reconstructs the source; numeric controls stay in schema bounds. |
| Character | A canonical participant identifier such as `god`, `adam`, or `eve`. | “Speaker instance,” because occurrences must share identity across chapters. | Identifier is stable; an existing registry entry never changes automatically. |
| Voice profile | A stable `voice_id` plus optional WAV reference used to condition Chatterbox. | “Random voice,” which violates continuity. | Resolution is deterministic; missing character audio falls back to narrator and records the reason. |
| Generation fingerprint | SHA-256 over every input capable of changing the audio. | “Cache key” alone, because the fingerprint is also provenance. | Includes source, narration, registry, voice hashes, model revisions, seed, generation controls, and mastering controls. |
| Chapter master | The final mastered WAV and derived AAC/M4A for one source chapter. | “Source audio,” because it is reproducible output. | Produced only after integrity validation; metadata identifies the exact inputs. |

## Aggregate invariants

`SourceChapter` rejects duplicate, missing, unordered, empty, or cross-chapter
records. `NarrationPlan` rejects unknown fields, unknown units, noncontiguous
groups, duplication, omission, reordering, invalid ranges, stale source hashes,
and failed normalized reconstruction. `CharacterRegistry` accepts deterministic
additions but rejects automatic remapping. `GeneratedChapter` publishes masters
only after every segment fingerprint and FFmpeg output pass validation.

