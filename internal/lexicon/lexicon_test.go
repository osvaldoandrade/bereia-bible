package lexicon

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// The real lexicon must always satisfy its own invariants (curator DoD).
func TestRealLexiconValid(t *testing.T) {
	l, err := Load("../../lexicon/lexicon.json")
	if err != nil {
		t.Fatal(err)
	}
	if errs := l.Validate(); len(errs) != 0 {
		t.Errorf("repo lexicon violates invariants: %v", errs)
	}
	if len(l.Entries) == 0 || l.Owner == "" {
		t.Error("repo lexicon must have entries and an owner")
	}
}

func entry(mut func(*Entry)) Entry {
	e := Entry{
		Lemma: "H1254a", Original: "ברא", Translit: "bara", Gloss: "criar",
		Domain: "verbo de criação", Justification: "x", Status: "APPROVED",
		Owner: "maintainer", FirstOccurrences: []string{"Gen.1.1"},
	}
	if mut != nil {
		mut(&e)
	}
	return e
}

func TestValidateInvariants(t *testing.T) {
	tests := []struct {
		name    string
		lex     Lexicon
		wantErr string
	}{
		{
			"valid entry passes",
			Lexicon{Entries: []Entry{entry(nil)}},
			"",
		},
		{
			"I-1 duplicate active lemma+domain",
			Lexicon{Entries: []Entry{entry(nil), entry(func(e *Entry) { e.Gloss = "outra" })}},
			"I-1",
		},
		{
			"I-5 superseded without pointer",
			Lexicon{Entries: []Entry{entry(func(e *Entry) { e.Status = "SUPERSEDED" })}},
			"I-5",
		},
		{
			"I-5 pointer to missing entry",
			Lexicon{Entries: []Entry{entry(func(e *Entry) { e.SupersededBy = "H9999" })}},
			"I-5",
		},
		{
			"I-6 divine name without policy",
			Lexicon{Entries: []Entry{entry(func(e *Entry) { e.Domain = "nome divino" })}},
			"I-6",
		},
		{
			"I-6 policy ref undeclared",
			Lexicon{Entries: []Entry{entry(func(e *Entry) { e.PolicyRef = "fantasma" })}},
			"I-6",
		},
		{
			"I-7 bad OSIS occurrence",
			Lexicon{Entries: []Entry{entry(func(e *Entry) { e.FirstOccurrences = []string{"Gênesis 1:1"} })}},
			"I-7",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			errs := tt.lex.Validate()
			if tt.wantErr == "" {
				if len(errs) != 0 {
					t.Fatalf("want valid, got %v", errs)
				}
				return
			}
			joined := ""
			for _, e := range errs {
				joined += e.Error() + "\n"
			}
			if !strings.Contains(joined, tt.wantErr) {
				t.Fatalf("want %q violation, got:\n%s", tt.wantErr, joined)
			}
		})
	}
}

func TestLoadErrors(t *testing.T) {
	if _, err := Load("missing.json"); err == nil {
		t.Error("want error for missing file")
	}
	bad := filepath.Join(t.TempDir(), "bad.json")
	if err := os.WriteFile(bad, []byte("{"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(bad); err == nil {
		t.Error("want error for malformed json")
	}
}
