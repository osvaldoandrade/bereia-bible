// Package nestle1904 parses the tab-delimited morphological edition of
// Eberhard Nestle's 1904 Greek New Testament published by Biblical Humanities.
// It is intentionally separate from internal/oshb: the two sources have
// different formats, licenses, morphology systems, and textual apparatus.
package nestle1904

import (
	"encoding/csv"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
	"unicode"
)

// Word is one annotated Greek word. Prefix/suffix punctuation is emitted as
// separate Token values so the lexical surface remains aligned to the lemma.
type Word struct {
	Surface           string
	Lemma             string
	Morph             string
	FunctionalMorph   string
	Strong            string
	Normalized        string
	MorphAlternatives []string
}

// Token is either an annotated word or punctuation/variant markup preserved
// from the source flow.
type Token struct {
	Word        *Word
	Punctuation string
}

// Verse is one source verse. Text preserves the exact row surfaces joined in
// source order; Tokens expose clean lexical forms plus punctuation separately.
type Verse struct {
	OSIS   string
	Number int
	Text   string
	Tokens []Token
}

var header = []string{"BCV", "text", "func_morph", "form_morph", "strongs", "lemma", "normalized"}

// ParseVerses returns every source verse present in the inclusive range. The
// Nestle text intentionally omits a small set of traditional verse numbers, so
// internal gaps are allowed; the requested endpoints must exist. The caller
// decides whether a non-canonical source reference such as Mark 16:99 is read
// as apparatus rather than emitted as a canonical verse.
func ParseVerses(r io.Reader, osisBook string, chapter, from, to int) ([]Verse, error) {
	if osisBook == "" || chapter < 1 || from < 1 || from > to {
		return nil, fmt.Errorf("nestle1904: invalid request %s.%d.%d-%d", osisBook, chapter, from, to)
	}

	cr := csv.NewReader(r)
	cr.Comma = '\t'
	// The upstream file has a documented seven-column schema but currently
	// writes one trailing empty tab on data rows. Accept only that harmless
	// eighth field; reject any non-empty or additional column.
	cr.FieldsPerRecord = -1
	record, err := cr.Read()
	if err != nil {
		return nil, fmt.Errorf("nestle1904: read header: %w", err)
	}
	record[0] = strings.TrimPrefix(record[0], "\ufeff")
	if len(record) != len(header) {
		return nil, fmt.Errorf("nestle1904: header has %d columns, want %d", len(record), len(header))
	}
	for i, want := range header {
		if record[i] != want {
			return nil, fmt.Errorf("nestle1904: header column %d is %q, want %q", i+1, record[i], want)
		}
	}

	verses := make(map[int]*Verse)
	var rawByVerse = make(map[int][]string)
	for {
		record, err = cr.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("nestle1904: read row: %w", err)
		}
		if len(record) < len(header) || len(record) > len(header)+2 {
			return nil, fmt.Errorf("nestle1904: row has %d columns, want %d plus the documented trailing field or two morphology alternatives", len(record), len(header))
		}
		book, ch, verse, err := parseBCV(record[0])
		if err != nil {
			return nil, err
		}
		if book != osisBook || ch != chapter || verse < from || verse > to {
			continue
		}
		v := verses[verse]
		if v == nil {
			v = &Verse{OSIS: fmt.Sprintf("%s.%d.%d", book, ch, verse), Number: verse}
			verses[verse] = v
		}
		raw := record[1]
		if strings.TrimSpace(raw) == "" {
			return nil, fmt.Errorf("nestle1904: %s: empty word surface", v.OSIS)
		}
		rawByVerse[verse] = append(rawByVerse[verse], raw)
		prefix, surface, suffix := splitSurface(raw)
		if prefix != "" {
			v.Tokens = append(v.Tokens, Token{Punctuation: prefix})
		}
		if surface == "" {
			return nil, fmt.Errorf("nestle1904: %s: no lexical surface in %q", v.OSIS, raw)
		}
		extras := record[len(header):]
		alternatives := make([]string, 0, 2)
		switch {
		case len(extras) == 0 || (len(extras) == 1 && extras[0] == ""):
		case len(extras) == 2 && extras[0] != "" && extras[1] != "" &&
			record[2] == strings.Join(extras, "@@") && record[3] == strings.Join(extras, "@@"):
			alternatives = append(alternatives, extras...)
		default:
			return nil, fmt.Errorf("nestle1904: %s: invalid trailing morphology columns %q", record[0], extras)
		}
		v.Tokens = append(v.Tokens, Token{Word: &Word{
			Surface:           surface,
			FunctionalMorph:   record[2],
			Morph:             record[3],
			Strong:            record[4],
			Lemma:             record[5],
			Normalized:        record[6],
			MorphAlternatives: alternatives,
		}})
		if suffix != "" {
			v.Tokens = append(v.Tokens, Token{Punctuation: suffix})
		}
	}

	if verses[from] == nil || verses[to] == nil {
		var missing []string
		if verses[from] == nil {
			missing = append(missing, fmt.Sprintf("%s.%d.%d", osisBook, chapter, from))
		}
		if to != from && verses[to] == nil {
			missing = append(missing, fmt.Sprintf("%s.%d.%d", osisBook, chapter, to))
		}
		return nil, fmt.Errorf("nestle1904: range endpoint not found: %s", strings.Join(missing, ", "))
	}

	numbers := make([]int, 0, len(verses))
	for n := range verses {
		numbers = append(numbers, n)
	}
	sort.Ints(numbers)
	out := make([]Verse, 0, len(numbers))
	for _, n := range numbers {
		v := verses[n]
		v.Text = strings.Join(rawByVerse[n], " ")
		out = append(out, *v)
	}
	return out, nil
}

func parseBCV(raw string) (string, int, int, error) {
	parts := strings.Fields(raw)
	if len(parts) != 2 {
		return "", 0, 0, fmt.Errorf("nestle1904: invalid BCV %q", raw)
	}
	cv := strings.Split(parts[1], ":")
	if len(cv) != 2 {
		return "", 0, 0, fmt.Errorf("nestle1904: invalid BCV %q", raw)
	}
	chapter, err := strconv.Atoi(cv[0])
	if err != nil || chapter < 1 {
		return "", 0, 0, fmt.Errorf("nestle1904: invalid BCV %q", raw)
	}
	verse, err := strconv.Atoi(cv[1])
	if err != nil || verse < 1 {
		return "", 0, 0, fmt.Errorf("nestle1904: invalid BCV %q", raw)
	}
	return parts[0], chapter, verse, nil
}

// splitSurface removes only leading/trailing typography. The right single
// quotation mark remains part of elided Greek words (for example δι’).
func splitSurface(raw string) (prefix, surface, suffix string) {
	runes := []rune(raw)
	start := 0
	for start < len(runes) && !isLexical(runes[start]) {
		start++
	}
	end := len(runes)
	for end > start && !isLexical(runes[end-1]) && runes[end-1] != '’' {
		end--
	}
	return string(runes[:start]), string(runes[start:end]), string(runes[end:])
}

func isLexical(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r)
}
