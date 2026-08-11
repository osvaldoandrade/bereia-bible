package oshb

import (
	"os"
	"strings"
	"testing"
)

const fixture = `<?xml version="1.0" encoding="UTF-8"?>
<osis><osisText><div type="book" osisID="Gen"><chapter osisID="Gen.1">
<verse osisID="Gen.1.1"><w lemma="b/7225" morph="HR/Ncfsa">בְּ/רֵאשִׁ֖ית</w><w lemma="1254 a" morph="HVqp3ms">בָּרָ֣א</w><note n="a">editorial note must be ignored</note><seg type="x-sof-pasuq">׃</seg></verse>
<verse osisID="Gen.1.2"><w lemma="5921 a" morph="HR">עַל</w><seg type="x-maqqef">־</seg><w lemma="6440" morph="HNcbpc">פְּנֵי</w><seg type="x-sof-pasuq">׃</seg></verse>
<verse osisID="Gen.1.3"><note n="b">only a note</note></verse>
</chapter></div></osisText></osis>`

func TestParseVerses(t *testing.T) {
	tests := []struct {
		name     string
		xml      string
		book     string
		chapter  int
		from, to int
		wantErr  string
		check    func(t *testing.T, vs []Verse)
	}{
		{
			name: "happy path with morphemes, note and sof pasuq",
			xml:  fixture, book: "Gen", chapter: 1, from: 1, to: 1,
			check: func(t *testing.T, vs []Verse) {
				v := vs[0]
				if len(v.Words) != 3 {
					t.Fatalf("want 3 tokens, got %d: %+v", len(v.Words), v.Words)
				}
				if v.Words[0].Surface != "בְּרֵאשִׁ֖ית" {
					t.Errorf("surface with '/' not joined: %q", v.Words[0].Surface)
				}
				if len(v.Words[0].Segments) != 2 || v.Words[0].Lemma != "b/7225" {
					t.Errorf("segments/lemma wrong: %+v", v.Words[0])
				}
				if strings.Contains(v.Text, "ignored") || strings.Contains(v.Text, "note") {
					t.Errorf("note leaked into text: %q", v.Text)
				}
				if !strings.HasSuffix(v.Text, "׃") {
					t.Errorf("sof pasuq not attached: %q", v.Text)
				}
			},
		},
		{
			name: "maqqef joins without space",
			xml:  fixture, book: "Gen", chapter: 1, from: 2, to: 2,
			check: func(t *testing.T, vs []Verse) {
				if vs[0].Text != "עַל־פְּנֵי׃" {
					t.Errorf("maqqef composition wrong: %q", vs[0].Text)
				}
			},
		},
		{
			name: "verse with no words fails",
			xml:  fixture, book: "Gen", chapter: 1, from: 3, to: 3,
			wantErr: "no words",
		},
		{
			name: "missing verse reported",
			xml:  fixture, book: "Gen", chapter: 1, from: 4, to: 5,
			wantErr: "not found: Gen.1.4, Gen.1.5",
		},
		{
			name: "invalid range rejected",
			xml:  fixture, book: "Gen", chapter: 1, from: 3, to: 1,
			wantErr: "invalid request",
		},
		{
			name: "empty book rejected",
			xml:  fixture, book: "", chapter: 1, from: 1, to: 1,
			wantErr: "invalid request",
		},
		{
			name: "malformed xml fails",
			xml:  `<osis><verse osisID="Gen.1.1"><w>אב`, book: "Gen", chapter: 1, from: 1, to: 1,
			wantErr: "unterminated",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			vs, err := ParseVerses(strings.NewReader(tt.xml), tt.book, tt.chapter, tt.from, tt.to)
			if tt.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
					t.Fatalf("want error containing %q, got %v", tt.wantErr, err)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if len(vs) != tt.to-tt.from+1 {
				t.Fatalf("want %d verses, got %d", tt.to-tt.from+1, len(vs))
			}
			tt.check(t, vs)
		})
	}
}

// TestParseRealGenesis pins the extraction against the actual pinned source:
// Gen 1:1 must have exactly 7 words and every verse must close with sof pasuq.
func TestParseRealGenesis(t *testing.T) {
	f, err := os.Open("../../sources/oshb/Gen.xml")
	if err != nil {
		t.Skip("pinned source not present:", err)
	}
	defer f.Close()
	vs, err := ParseVerses(f, "Gen", 1, 1, 5)
	if err != nil {
		t.Fatal(err)
	}
	if len(vs) != 5 {
		t.Fatalf("want 5 verses, got %d", len(vs))
	}
	words := 0
	for _, w := range vs[0].Words {
		if w.Type == "word" {
			words++
		}
	}
	if words != 7 {
		t.Errorf("Gen.1.1 must have 7 words, got %d", words)
	}
	// Pin by annotation, not by surface bytes: cantillation combining-mark
	// order makes byte comparison of pointed Hebrew brittle.
	first := vs[0].Words[0]
	if first.Lemma != "b/7225" || first.Morph != "HR/Ncfsa" || len(first.Segments) != 2 {
		t.Errorf("Gen.1.1 first word annotation: %+v", first)
	}
	for _, v := range vs {
		// Sof pasuq closes every verse; Gen.1.5 also carries the petuchah
		// marker after it, so Contains rather than HasSuffix.
		if !strings.Contains(v.Text, "׃") {
			t.Errorf("%s missing sof pasuq: %q", v.OSIS, v.Text)
		}
	}
}

func FuzzParseVerses(f *testing.F) {
	f.Add(fixture)
	f.Add(`<verse osisID="Gen.1.1"></verse>`)
	f.Add(`not xml at all`)
	f.Fuzz(func(t *testing.T, data string) {
		vs, err := ParseVerses(strings.NewReader(data), "Gen", 1, 1, 2)
		if err == nil {
			for _, v := range vs {
				if len(v.Words) == 0 {
					t.Errorf("%s: parsed verse with zero words and nil error", v.OSIS)
				}
			}
		}
	})
}
