package schemavalidate

import (
	"strings"
	"testing"
)

func mustValidate(t *testing.T, schema map[string]any, doc any) []error {
	t.Helper()
	return Validate(schema, doc, "$")
}

func TestValidateKeywords(t *testing.T) {
	tests := []struct {
		name    string
		schema  map[string]any
		doc     any
		wantErr string // empty = valid
	}{
		{"type ok", map[string]any{"type": "string"}, "x", ""},
		{"type mismatch", map[string]any{"type": "string"}, 1.0, "expected type"},
		{"type union with null", map[string]any{"type": []any{"string", "null"}}, nil, ""},
		{"integer accepted as number", map[string]any{"type": "number"}, 3.0, ""},
		{"float rejected as integer", map[string]any{"type": "integer"}, 3.5, "expected type"},
		{"enum ok", map[string]any{"enum": []any{"A", "B"}}, "A", ""},
		{"enum fail", map[string]any{"enum": []any{"A", "B"}}, "C", "not in enum"},
		{"const ok", map[string]any{"const": "v1"}, "v1", ""},
		{"const fail", map[string]any{"const": "v1"}, "v2", "!= const"},
		{"pattern ok", map[string]any{"pattern": "^ER-[0-9]{4}$"}, "ER-0002", ""},
		{"pattern fail", map[string]any{"pattern": "^ER-[0-9]{4}$"}, "D-2", "does not match"},
		{"bad pattern reported", map[string]any{"pattern": "("}, "x", "bad pattern"},
		{"minLength fail", map[string]any{"minLength": 2.0}, "x", "minLength"},
		{"minimum fail", map[string]any{"minimum": 0.0}, -1.0, "below minimum"},
		{"maximum fail", map[string]any{"maximum": 1.0}, 1.5, "above maximum"},
		{"required fail", map[string]any{"type": "object", "required": []any{"a"}}, map[string]any{}, "missing required"},
		{
			"additionalProperties fail",
			map[string]any{"type": "object", "additionalProperties": false, "properties": map[string]any{"a": map[string]any{}}},
			map[string]any{"a": 1.0, "b": 2.0}, `additional property "b"`,
		},
		{
			"nested property error path",
			map[string]any{"type": "object", "properties": map[string]any{"a": map[string]any{"type": "string"}}},
			map[string]any{"a": 1.0}, "$.a",
		},
		{"minItems fail", map[string]any{"type": "array", "minItems": 1.0}, []any{}, "minItems"},
		{
			"items validated with index",
			map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
			[]any{"ok", 2.0}, "$[1]",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			errs := mustValidate(t, tt.schema, tt.doc)
			if tt.wantErr == "" {
				if len(errs) != 0 {
					t.Fatalf("want valid, got %v", errs)
				}
				return
			}
			if len(errs) == 0 {
				t.Fatalf("want error containing %q, got none", tt.wantErr)
			}
			joined := ""
			for _, e := range errs {
				joined += e.Error() + "\n"
			}
			if !strings.Contains(joined, tt.wantErr) {
				t.Fatalf("want error containing %q, got:\n%s", tt.wantErr, joined)
			}
		})
	}
}

// Contract tests (herald B3): the repo's own artifacts must validate against
// the repo's own schemas, and the deliberately broken example must fail.
func TestRepoContracts(t *testing.T) {
	valid := [][2]string{
		{"../../api/verse-record.schema.json", "../../api/examples/verse-record.valid.example.json"},
		{"../../api/manifest.schema.json", "../../sources/manifest.json"},
		{"../../lexicon/lexicon.schema.json", "../../lexicon/lexicon.json"},
	}
	for _, pair := range valid {
		errs, err := ValidateFile(pair[0], pair[1])
		if err != nil {
			t.Fatalf("%s: %v", pair[1], err)
		}
		if len(errs) != 0 {
			t.Errorf("%s must validate against %s, got: %v", pair[1], pair[0], errs)
		}
	}

	errs, err := ValidateFile("../../api/verse-record.schema.json", "../../api/examples/verse-record.invalid.example.json")
	if err != nil {
		t.Fatal(err)
	}
	joined := ""
	for _, e := range errs {
		joined += e.Error() + "\n"
	}
	for _, want := range []string{`missing required property "texto_bv"`, "not in enum", "campo_inventado", "above maximum", "does not match pattern"} {
		if !strings.Contains(joined, want) {
			t.Errorf("invalid example must fail with %q; got:\n%s", want, joined)
		}
	}
}

func TestValidateFileErrors(t *testing.T) {
	if _, err := ValidateFile("missing.json", "also-missing.json"); err == nil {
		t.Error("want error for missing schema file")
	}
	if _, err := ValidateFile("../../api/manifest.schema.json", "missing.json"); err == nil {
		t.Error("want error for missing doc file")
	}
}
