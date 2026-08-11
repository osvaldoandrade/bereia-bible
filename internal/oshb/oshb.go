// Package oshb parses the OSIS XML dialect used by the Open Scriptures
// Hebrew Bible (WLC with morphology). It is the anti-corruption layer of the
// extraction context: OSIS structural details stay here; callers receive
// plain Verse/Word values (ADR-0001).
package oshb

import (
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"strings"
)

const maqqef = "־"

// Word is one annotated token of the WLC text, or a punctuation segment
// (sof pasuq, maqqef) kept in the verse flow.
type Word struct {
	Surface  string   `json:"surface"`
	Segments []string `json:"segments,omitempty"` // morpheme segments as split by '/' in the source
	Lemma    string   `json:"lemma,omitempty"`    // extended Strong's (e.g. "b/7225", "1254 a")
	Morph    string   `json:"morph,omitempty"`    // OSHB morphology code (e.g. "HR/Ncfsa")
	Seg      string   `json:"seg,omitempty"`      // OSIS seg type for punctuation (e.g. "x-maqqef")
	Type     string   `json:"type"`               // "word" or "punctuation"
}

// Verse is a parsed verse with its words in document order.
type Verse struct {
	OSIS  string `json:"osis"`
	Words []Word `json:"palavras"`
	Text  string `json:"hebraico"` // pointed text, maqqef joined without spaces
}

// ParseVerses extracts the inclusive verse range chapter:from-to of osisBook
// from an OSHB OSIS document. It fails if any requested verse is absent.
func ParseVerses(r io.Reader, osisBook string, chapter, from, to int) ([]Verse, error) {
	if osisBook == "" || chapter < 1 || from < 1 || from > to {
		return nil, fmt.Errorf("oshb: invalid request %s.%d.%d-%d", osisBook, chapter, from, to)
	}
	want := make(map[string]bool, to-from+1)
	for v := from; v <= to; v++ {
		want[fmt.Sprintf("%s.%d.%d", osisBook, chapter, v)] = true
	}
	dec := xml.NewDecoder(r)
	var out []Verse
	for len(want) > 0 {
		tok, err := dec.Token()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("oshb: %w", err)
		}
		se, ok := tok.(xml.StartElement)
		if !ok || se.Name.Local != "verse" {
			continue
		}
		id := attr(se, "osisID")
		if !want[id] {
			if err := dec.Skip(); err != nil {
				return nil, fmt.Errorf("oshb: %w", err)
			}
			continue
		}
		v, err := parseVerse(dec, id)
		if err != nil {
			return nil, err
		}
		out = append(out, v)
		delete(want, id)
	}
	if len(want) > 0 {
		missing := make([]string, 0, len(want))
		for id := range want {
			missing = append(missing, id)
		}
		return nil, fmt.Errorf("oshb: verses not found: %s", strings.Join(sorted(missing), ", "))
	}
	return out, nil
}

func parseVerse(dec *xml.Decoder, id string) (Verse, error) {
	v := Verse{OSIS: id}
	for {
		tok, err := dec.Token()
		if err != nil {
			return v, fmt.Errorf("oshb: %s: unterminated verse: %w", id, err)
		}
		switch t := tok.(type) {
		case xml.StartElement:
			w, err := parseChild(dec, t)
			if err != nil {
				return v, fmt.Errorf("oshb: %s: %w", id, err)
			}
			if w != nil {
				v.Words = append(v.Words, *w)
			}
		case xml.EndElement:
			if t.Name.Local != "verse" {
				continue
			}
			if len(v.Words) == 0 {
				return v, fmt.Errorf("oshb: %s: verse has no words", id)
			}
			v.Text = composeText(v.Words)
			return v, nil
		}
	}
}

// parseChild handles one child element of <verse>; nil means "ignored"
// (e.g. <note> commentary, which must never leak into the text).
func parseChild(dec *xml.Decoder, se xml.StartElement) (*Word, error) {
	switch se.Name.Local {
	case "w":
		raw, err := innerText(dec, se.Name.Local)
		if err != nil {
			return nil, err
		}
		w := Word{
			Surface: strings.ReplaceAll(raw, "/", ""),
			Lemma:   attr(se, "lemma"),
			Morph:   attr(se, "morph"),
			Type:    "word",
		}
		if segs := strings.Split(raw, "/"); len(segs) > 1 {
			w.Segments = segs
		}
		return &w, nil
	case "seg":
		raw, err := innerText(dec, se.Name.Local)
		if err != nil {
			return nil, err
		}
		return &Word{Surface: strings.TrimSpace(raw), Seg: attr(se, "type"), Type: "punctuation"}, nil
	default:
		return nil, dec.Skip()
	}
}

// innerText accumulates character data until the matching end element,
// skipping any nested markup.
func innerText(dec *xml.Decoder, name string) (string, error) {
	var b strings.Builder
	depth := 1
	for depth > 0 {
		tok, err := dec.Token()
		if err != nil {
			return "", fmt.Errorf("unterminated <%s>: %w", name, err)
		}
		switch t := tok.(type) {
		case xml.CharData:
			if depth == 1 {
				b.Write(t)
			}
		case xml.StartElement:
			depth++
		case xml.EndElement:
			depth--
		}
	}
	return strings.TrimSpace(b.String()), nil
}

// composeText joins words with spaces; punctuation attaches to the previous
// word, and after a maqqef the next word attaches without a space.
func composeText(words []Word) string {
	var b strings.Builder
	joinNext := true
	for _, w := range words {
		if w.Type == "punctuation" {
			b.WriteString(w.Surface)
			joinNext = w.Surface == maqqef
			continue
		}
		if !joinNext && b.Len() > 0 {
			b.WriteString(" ")
		}
		b.WriteString(w.Surface)
		joinNext = false
	}
	return b.String()
}

func attr(se xml.StartElement, name string) string {
	for _, a := range se.Attr {
		if a.Name.Local == name {
			return a.Value
		}
	}
	return ""
}

func sorted(s []string) []string {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
	return s
}
