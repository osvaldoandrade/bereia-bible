"""Pinned runtime and artifact constants."""

PACKAGE_VERSION = "0.1.0"
NARRATION_SCHEMA_VERSION = "1.0.0"
METADATA_SCHEMA_VERSION = "1.0.0"
REGISTRY_SCHEMA_VERSION = "1.0.0"
NARRATION_PROMPT_VERSION = "1.0.0"
DEFAULT_NARRATION_MODEL = "gpt-5.6-sol"
DEFAULT_SEED = 1234

TTS_PACKAGE = "mlx-audio"
TTS_PACKAGE_VERSION = "0.5.3"
TTS_MODEL = "mlx-community/chatterbox-fp16"
TTS_MODEL_REVISION = "4923fcca09086356aeab5191a2348c5a17a23694"
TTS_TOKENIZER = "mlx-community/S3TokenizerV2"
TTS_TOKENIZER_REVISION = "e0c9886f0e1c35ae85b1f27277416fb19fc72bec"
TTS_LANGUAGE = "pt"
TTS_SAMPLE_RATE = 24_000

ALLOWED_MODEL_FILES = (
    "Cangjie5_TC.json",
    "conds.safetensors",
    "config.json",
    "model.safetensors",
    "tokenizer.json",
)
ALLOWED_TOKENIZER_FILES = ("config.json", "model.safetensors")

TONE_VALUES = frozenset(
    {
        "narrative",
        "solemn",
        "commanding",
        "dialogue",
        "lament",
        "joy",
        "warning",
        "prophetic",
        "contemplative",
    }
)
LITERARY_TYPE_VALUES = frozenset(
    {
        "narrative",
        "law",
        "poetry",
        "wisdom",
        "prophecy",
        "gospel",
        "epistle",
        "apocalyptic",
        "genealogy",
    }
)
EMOTION_VALUES = frozenset(
    {"neutral", "awe", "tenderness", "grief", "joy", "urgency", "warning", "resolve"}
)
PITCH_VALUES = frozenset({"low", "neutral", "high"})
CADENCE_VALUES = frozenset({"flowing", "measured", "deliberate", "firm", "gentle"})
