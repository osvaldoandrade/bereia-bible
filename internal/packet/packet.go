// Package packet builds the per-pericope input packet consumed by the
// multi-agent pipeline: WLC words with morphology plus PD/CC-BY control
// renderings for divergence detection (never for wording).
package packet

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"bereia.org/bible/internal/oshb"
)

type Source struct {
	ID        string `json:"id"`
	File      string `json:"arquivo"`
	GitCommit string `json:"git_commit,omitempty"`
}

type Controls struct {
	Web   string `json:"web,omitempty"`
	KJV   string `json:"kjv,omitempty"`
	Livre string `json:"livre,omitempty"`
}

type Verse struct {
	OSIS     string      `json:"osis"`
	Number   int         `json:"numero"`
	Hebrew   string      `json:"hebraico"`
	Words    []oshb.Word `json:"palavras"`
	Controls *Controls   `json:"controles,omitempty"`
}

type Packet struct {
	Unit   string  `json:"unidade"`
	Source Source  `json:"fonte"`
	Verses []Verse `json:"versos"`
}

// Request carries everything Build needs; control paths may be empty.
type Request struct {
	OSHBPath  string
	OSISBook  string
	BookNr    int
	Chapter   int
	From, To  int
	Pericope  string
	WebPath   string
	KJVPath   string
	LivrePath string
}

// Build extracts the verse range and attaches control renderings.
func Build(req Request) (*Packet, error) {
	f, err := os.Open(req.OSHBPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	verses, err := oshb.ParseVerses(f, req.OSISBook, req.Chapter, req.From, req.To)
	if err != nil {
		return nil, err
	}
	p := &Packet{
		Unit:   req.Pericope,
		Source: Source{ID: "oshb", File: req.OSHBPath, GitCommit: readCommit(req.OSHBPath)},
	}
	controls, err := loadControls(req)
	if err != nil {
		return nil, err
	}
	for i, v := range verses {
		n := req.From + i
		pv := Verse{OSIS: v.OSIS, Number: n, Hebrew: v.Text, Words: v.Words}
		if c := controls.forVerse(n); c != nil {
			pv.Controls = c
		}
		p.Verses = append(p.Verses, pv)
	}
	return p, nil
}

// readCommit picks up the pinned upstream commit stored by the fetch step
// next to the source file (sources/<id>/COMMIT), if present.
func readCommit(sourcePath string) string {
	raw, err := os.ReadFile(filepath.Join(filepath.Dir(sourcePath), "COMMIT"))
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(raw))
}

type controlSet struct {
	web, kjv, livre map[int]string // verse number -> text (single chapter)
}

func (c controlSet) forVerse(n int) *Controls {
	out := Controls{Web: c.web[n], KJV: c.kjv[n], Livre: c.livre[n]}
	if out == (Controls{}) {
		return nil
	}
	return &out
}

func loadControls(req Request) (controlSet, error) {
	var cs controlSet
	var err error
	if cs.web, err = OSHBChapterText(req.WebPath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	if cs.kjv, err = OSHBChapterText(req.KJVPath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	if cs.livre, err = OSHBChapterText(req.LivrePath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	return cs, nil
}

type verseSpan struct {
	sourceFrom, sourceTo        int
	controlChapter, controlFrom int
}

// OSHB uses the Hebrew versification, while the stored controls use the
// KJV/NRSV chapter boundaries. Each exceptional source chapter is mapped
// explicitly so a control can never be attached to the wrong Hebrew verse.
// A source verse may be intentionally absent when one control verse cannot be
// aligned without mixing text from multiple OSHB verses.
var controlSpans = map[[2]int][]verseSpan{
	{1, 32}:  {{1, 1, 31, 55}, {2, 33, 32, 1}},
	{2, 7}:   {{1, 25, 7, 1}, {26, 29, 8, 1}},
	{2, 8}:   {{1, 28, 8, 5}},
	{2, 21}:  {{1, 36, 21, 1}, {37, 37, 22, 1}},
	{2, 22}:  {{1, 30, 22, 2}},
	{3, 5}:   {{1, 19, 5, 1}, {20, 26, 6, 1}},
	{3, 6}:   {{1, 23, 6, 8}},
	{4, 17}:  {{1, 15, 16, 36}, {16, 28, 17, 1}},
	{4, 25}:  {{1, 18, 25, 1}, {19, 19, 26, 1}},
	{4, 30}:  {{1, 1, 29, 40}, {2, 17, 30, 1}},
	{5, 12}:  {{1, 31, 12, 1}},
	{5, 13}:  {{1, 1, 12, 32}, {2, 19, 13, 1}},
	{5, 22}:  {{1, 29, 22, 1}},
	{5, 23}:  {{1, 1, 22, 30}, {2, 26, 23, 1}},
	{5, 28}:  {{1, 68, 28, 1}, {69, 69, 29, 1}},
	{5, 29}:  {{1, 28, 29, 2}},
	{9, 21}:  {{1, 1, 20, 42}, {2, 16, 21, 1}},
	{9, 24}:  {{1, 1, 23, 29}, {2, 23, 24, 1}},
	{10, 19}: {{1, 1, 18, 33}, {2, 44, 19, 1}},
	{11, 5}:  {{1, 14, 4, 21}, {15, 32, 5, 1}},
	// KJV, WEB, and Livre 1Kgs 22:43 combine the material that OSHB divides
	// between 22:43-44. Both OSHB verses are intentionally left without a
	// control rather than attaching the same mixed control text to either one.
	{11, 22}: {{1, 42, 22, 1}, {45, 54, 22, 44}},
	// KJV, WEB, and Livre place OSHB 2Kgs 12:1 at 11:21, then number
	// OSHB 12:2-22 as 12:1-21. Truncate chapter 11 so its trailing control
	// cannot appear as a nonexistent OSHB 11:21.
	{12, 11}: {{1, 20, 11, 1}},
	{12, 12}: {{1, 1, 11, 21}, {2, 22, 12, 1}},
	// KJV, WEB, and Livre number OSHB 1Chr 5:27-41 as 6:1-15 and
	// OSHB 6:1-66 as 6:16-81. Their 12:4 combines OSHB 12:4-5, so both
	// source verses are intentionally left without a mixed control.
	{13, 5}:  {{1, 26, 5, 1}, {27, 41, 6, 1}},
	{13, 6}:  {{1, 66, 6, 16}},
	{13, 12}: {{1, 3, 12, 1}, {6, 41, 12, 5}},
	// KJV, WEB, and Livre number OSHB 2Chr 1:18 as 2:1 and OSHB
	// 2:1-17 as 2:2-18. The same boundary shift occurs at 13:23/14:1:
	// OSHB 13:23 is control 14:1 and OSHB 14:1-14 are controls 14:2-15.
	{14, 1}:  {{1, 17, 1, 1}, {18, 18, 2, 1}},
	{14, 2}:  {{1, 17, 2, 2}},
	{14, 13}: {{1, 22, 13, 1}, {23, 23, 14, 1}},
	{14, 14}: {{1, 14, 14, 2}},
	// KJV, WEB, and Livre move OSHB Neh 3:33-38 to 4:1-6 and number
	// OSHB 4:1-17 as 4:7-23. Their 7:68 (horses and mules) has no OSHB
	// source verse, so it is deliberately not attached. They also place OSHB
	// 10:1 at 9:38 and number OSHB 10:2-40 as 10:1-39.
	{16, 3}:  {{1, 32, 3, 1}, {33, 38, 4, 1}},
	{16, 4}:  {{1, 17, 4, 7}},
	{16, 7}:  {{1, 67, 7, 1}, {68, 72, 7, 69}},
	{16, 9}:  {{1, 37, 9, 1}},
	{16, 10}: {{1, 1, 9, 38}, {2, 40, 10, 1}},
	// KJV, WEB, and Livre number OSHB Job 40:25-32 as 41:1-8 and
	// OSHB 41:1-26 as 41:9-34.
	{18, 40}: {{1, 24, 40, 1}, {25, 32, 41, 1}},
	{18, 41}: {{1, 26, 41, 9}},
	// KJV, WEB, and Livre number OSHB Eccl 4:17 as 5:1 and OSHB
	// 5:1-19 as 5:2-20.
	{21, 4}: {{1, 16, 4, 1}, {17, 17, 5, 1}},
	{21, 5}: {{1, 19, 5, 2}},
	// KJV, WEB, and Livre place OSHB Song 7:1 at 6:13, then number
	// OSHB 7:2-14 as 7:1-13. Truncate chapter 6 so its trailing control
	// cannot appear as a nonexistent OSHB 6:13.
	{22, 6}: {{1, 12, 6, 1}},
	{22, 7}: {{1, 1, 6, 13}, {2, 14, 7, 1}},
}

// OSHBChapterText returns control text keyed by the OSHB verse number.
func OSHBChapterText(path string, bookNr, chapter int) (map[int]string, error) {
	if path == "" {
		return nil, nil
	}
	spans, exceptional := controlSpans[[2]int{bookNr, chapter}]
	if !exceptional {
		return ChapterText(path, bookNr, chapter)
	}
	out := make(map[int]string)
	chapters := make(map[int]map[int]string)
	for _, span := range spans {
		control, ok := chapters[span.controlChapter]
		if !ok {
			var err error
			control, err = ChapterText(path, bookNr, span.controlChapter)
			if err != nil {
				return nil, err
			}
			chapters[span.controlChapter] = control
		}
		for sourceVerse := span.sourceFrom; sourceVerse <= span.sourceTo; sourceVerse++ {
			controlVerse := span.controlFrom + sourceVerse - span.sourceFrom
			text, ok := control[controlVerse]
			if !ok {
				return nil, fmt.Errorf(
					"control %s: mapped book %d %d:%d not found for OSHB %d:%d",
					path, bookNr, span.controlChapter, controlVerse, chapter, sourceVerse,
				)
			}
			out[sourceVerse] = text
		}
	}
	return out, nil
}

// getBible v2 whole-Bible JSON shape (books[].nr, chapters[].chapter,
// verses[].verse/text).
type gbBible struct {
	Books []struct {
		Nr       int `json:"nr"`
		Chapters []struct {
			Chapter int `json:"chapter"`
			Verses  []struct {
				Verse int    `json:"verse"`
				Text  string `json:"text"`
			} `json:"verses"`
		} `json:"chapters"`
	} `json:"books"`
}

func ChapterText(path string, bookNr, chapter int) (map[int]string, error) {
	if path == "" {
		return nil, nil
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var b gbBible
	if err := json.Unmarshal(raw, &b); err != nil {
		return nil, fmt.Errorf("control %s: %w", path, err)
	}
	for _, book := range b.Books {
		if book.Nr != bookNr {
			continue
		}
		for _, ch := range book.Chapters {
			if ch.Chapter != chapter {
				continue
			}
			out := make(map[int]string, len(ch.Verses))
			for _, v := range ch.Verses {
				out[v.Verse] = strings.TrimSpace(v.Text)
			}
			return out, nil
		}
	}
	return nil, fmt.Errorf("control %s: book %d chapter %d not found", path, bookNr, chapter)
}
