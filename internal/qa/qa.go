// Package qa glues verse records to the similarity metrics: it reads BV
// verse records and compares texto_bv against the stored Portuguese control
// (Bíblia Livre). Alerts are signals for source-first re-evaluation, never
// automatic rewrite triggers (PIPELINE.md §QA).
package qa

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"bereia.org/bible/internal/similarity"
)

// Alert heuristics: contiguous 8-word identical run, or 60% of trigrams
// shared with the control, warrants a source-first re-evaluation.
const (
	AlertOverlap3 = 0.60
	AlertLCS      = 8
)

type VerseResult struct {
	OSIS     string  `json:"osis"`
	TextBV   string  `json:"texto_bv"`
	Control  string  `json:"controle"`
	Overlap3 float64 `json:"overlap_3gram"`
	Overlap4 float64 `json:"overlap_4gram"`
	Overlap5 float64 `json:"overlap_5gram"`
	LCS      int     `json:"maior_sequencia_comum"`
	Alert    bool    `json:"alerta"`
}

type record struct {
	Referencia struct {
		OSIS      string `json:"osis"`
		Capitulo  int    `json:"capitulo"`
		Versiculo int    `json:"versiculo"`
	} `json:"referencia"`
	TextoBV string `json:"texto_bv"`
}

// CompareDir evaluates every *.json record in dir against the control
// chapter map (verse number -> control text).
func CompareDir(dir string, control map[int]string) ([]VerseResult, error) {
	paths, err := filepath.Glob(filepath.Join(dir, "*.json"))
	if err != nil {
		return nil, err
	}
	if len(paths) == 0 {
		return nil, fmt.Errorf("qa: no records in %s", dir)
	}
	sort.Strings(paths)
	var out []VerseResult
	for _, p := range paths {
		raw, err := os.ReadFile(p)
		if err != nil {
			return nil, err
		}
		var r record
		if err := json.Unmarshal(raw, &r); err != nil {
			return nil, fmt.Errorf("qa: %s: %w", p, err)
		}
		out = append(out, Compare(r.Referencia.OSIS, r.TextoBV, control[r.Referencia.Versiculo]))
	}
	return out, nil
}

// Compare computes the similarity metrics for one verse pair.
func Compare(osis, textBV, control string) VerseResult {
	a := similarity.Normalize(textBV)
	b := similarity.Normalize(control)
	res := VerseResult{
		OSIS:     osis,
		TextBV:   textBV,
		Control:  control,
		Overlap3: similarity.NGramOverlap(a, b, 3),
		Overlap4: similarity.NGramOverlap(a, b, 4),
		Overlap5: similarity.NGramOverlap(a, b, 5),
		LCS:      similarity.LongestCommonRun(a, b),
	}
	res.Alert = res.Overlap3 >= AlertOverlap3 || res.LCS >= AlertLCS
	return res
}
