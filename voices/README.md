# Voice references

Place an approved native Brazilian Portuguese narrator reference here as a
16-bit PCM WAV. Generation fails when `narrator.wav` is absent. This prevents
the TTS model's foreign-accented built-in voice from reaching a chapter output.

Additional character references may use stable `voice_id` names:

```text
voices/
├── narrator.wav
├── god.wav
├── adam.wav
├── eve.wav
└── serpent.wav
```

Each clip must be mono or stereo, 8–96 kHz, and between 1 and 30 seconds. Keep
speech clean and free of music, effects, long silence, or rights restrictions.
Reference WAV files are intentionally ignored by Git. Use only recordings for
which Bereia has the narrator's explicit voice-use permission. When a
character-specific file is absent, generation uses the approved narrator
reference and records the fallback. It never uses the model's built-in voice.
