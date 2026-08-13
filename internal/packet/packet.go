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
	allowedMissingLivreSourceVerse := 0
	if req.BookNr == 19 && req.Chapter == 46 {
		allowedMissingLivreSourceVerse = 4
	}
	if cs.livre, err = oshbChapterText(req.LivrePath, req.BookNr, req.Chapter, allowedMissingLivreSourceVerse); err != nil {
		return cs, err
	}
	// Livre Ps 46:2 merges the material that WEB/KJV divide between verses
	// 2-3 (OSHB 46:3-4). Do not attach that mixed control to either source
	// verse; the other controls remain independently aligned.
	if req.BookNr == 19 && req.Chapter == 46 {
		delete(cs.livre, 3)
		delete(cs.livre, 4)
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
	// Most Hebrew Psalm titles are numbered as source verses but omitted from
	// the controls. Psalms 51, 52, 54, and 60 have two numbered title verses.
	// Psalm 13:6 combines material split between control verses 5-6, so that
	// source verse is deliberately left without a mixed control.
	{19, 3}:   {{2, 9, 3, 1}},
	{19, 4}:   {{2, 9, 4, 1}},
	{19, 5}:   {{2, 13, 5, 1}},
	{19, 6}:   {{2, 11, 6, 1}},
	{19, 7}:   {{2, 18, 7, 1}},
	{19, 8}:   {{2, 10, 8, 1}},
	{19, 9}:   {{2, 21, 9, 1}},
	{19, 12}:  {{2, 9, 12, 1}},
	{19, 13}:  {{2, 5, 13, 1}},
	{19, 18}:  {{2, 51, 18, 1}},
	{19, 19}:  {{2, 15, 19, 1}},
	{19, 20}:  {{2, 10, 20, 1}},
	{19, 21}:  {{2, 14, 21, 1}},
	{19, 22}:  {{2, 32, 22, 1}},
	{19, 30}:  {{2, 13, 30, 1}},
	{19, 31}:  {{2, 25, 31, 1}},
	{19, 34}:  {{2, 23, 34, 1}},
	{19, 36}:  {{2, 13, 36, 1}},
	{19, 38}:  {{2, 23, 38, 1}},
	{19, 39}:  {{2, 14, 39, 1}},
	{19, 40}:  {{2, 18, 40, 1}},
	{19, 41}:  {{2, 14, 41, 1}},
	{19, 42}:  {{2, 12, 42, 1}},
	{19, 44}:  {{2, 27, 44, 1}},
	{19, 45}:  {{2, 18, 45, 1}},
	{19, 46}:  {{2, 12, 46, 1}},
	{19, 47}:  {{2, 10, 47, 1}},
	{19, 48}:  {{2, 15, 48, 1}},
	{19, 49}:  {{2, 21, 49, 1}},
	{19, 51}:  {{3, 21, 51, 1}},
	{19, 52}:  {{3, 11, 52, 1}},
	{19, 53}:  {{2, 7, 53, 1}},
	{19, 54}:  {{3, 9, 54, 1}},
	{19, 55}:  {{2, 24, 55, 1}},
	{19, 56}:  {{2, 14, 56, 1}},
	{19, 57}:  {{2, 12, 57, 1}},
	{19, 58}:  {{2, 12, 58, 1}},
	{19, 59}:  {{2, 18, 59, 1}},
	{19, 60}:  {{3, 14, 60, 1}},
	{19, 61}:  {{2, 9, 61, 1}},
	{19, 62}:  {{2, 13, 62, 1}},
	{19, 63}:  {{2, 12, 63, 1}},
	{19, 64}:  {{2, 11, 64, 1}},
	{19, 65}:  {{2, 14, 65, 1}},
	{19, 67}:  {{2, 8, 67, 1}},
	{19, 68}:  {{2, 36, 68, 1}},
	{19, 69}:  {{2, 37, 69, 1}},
	{19, 70}:  {{2, 6, 70, 1}},
	{19, 75}:  {{2, 11, 75, 1}},
	{19, 76}:  {{2, 13, 76, 1}},
	{19, 77}:  {{2, 21, 77, 1}},
	{19, 80}:  {{2, 20, 80, 1}},
	{19, 81}:  {{2, 17, 81, 1}},
	{19, 83}:  {{2, 19, 83, 1}},
	{19, 84}:  {{2, 13, 84, 1}},
	{19, 85}:  {{2, 14, 85, 1}},
	{19, 88}:  {{2, 19, 88, 1}},
	{19, 89}:  {{2, 53, 89, 1}},
	{19, 92}:  {{2, 16, 92, 1}},
	{19, 102}: {{2, 29, 102, 1}},
	{19, 108}: {{2, 14, 108, 1}},
	{19, 140}: {{2, 14, 140, 1}},
	{19, 142}: {{2, 8, 142, 1}},
	// KJV, WEB, and Livre number OSHB Eccl 4:17 as 5:1 and OSHB
	// 5:1-19 as 5:2-20.
	{21, 4}: {{1, 16, 4, 1}, {17, 17, 5, 1}},
	{21, 5}: {{1, 19, 5, 2}},
	// KJV, WEB, and Livre place OSHB Song 7:1 at 6:13, then number
	// OSHB 7:2-14 as 7:1-13. Truncate chapter 6 so its trailing control
	// cannot appear as a nonexistent OSHB 6:13.
	{22, 6}: {{1, 12, 6, 1}},
	{22, 7}: {{1, 1, 6, 13}, {2, 14, 7, 1}},
	// KJV, WEB, and Livre number OSHB Isa 8:23 as 9:1 and OSHB
	// 9:1-20 as 9:2-21.
	{23, 8}: {{1, 22, 8, 1}, {23, 23, 9, 1}},
	{23, 9}: {{1, 20, 9, 2}},
	// Their Isa 63:19 and 64:1 split the single OSHB 63:19 at an
	// intraverse boundary. Leave that source verse without a mixed control;
	// OSHB 64:1-11 then map to controls 64:2-12.
	{23, 63}: {{1, 18, 63, 1}},
	{23, 64}: {{1, 11, 64, 2}},
	// KJV, WEB, and Livre number OSHB Jer 8:23 as 9:1 and OSHB
	// 9:1-25 as 9:2-26.
	{24, 8}: {{1, 22, 8, 1}, {23, 23, 9, 1}},
	{24, 9}: {{1, 25, 9, 2}},
	// KJV, WEB, and Livre number OSHB Ezek 21:1-5 as 20:45-49 and
	// OSHB 21:6-37 as 21:1-32. Truncate chapter 20 so its trailing
	// controls cannot be attached to nonexistent OSHB verses there.
	{26, 20}: {{1, 44, 20, 1}},
	{26, 21}: {{1, 5, 20, 45}, {6, 37, 21, 1}},
	// KJV, WEB, and Livre number OSHB Dan 3:31-33 as 4:1-3 and
	// OSHB 4:1-34 as 4:4-37. They place OSHB 6:1 at 5:31 and number
	// OSHB 6:2-29 as 6:1-28, so chapter 5 is truncated at source v30.
	{27, 3}: {{1, 30, 3, 1}, {31, 33, 4, 1}},
	{27, 4}: {{1, 34, 4, 4}},
	{27, 5}: {{1, 30, 5, 1}},
	{27, 6}: {{1, 1, 5, 31}, {2, 29, 6, 1}},
	// Hosea's Hebrew chapter boundaries differ at 1/2, 11/12, and 13/14.
	{28, 1}:  {{1, 9, 1, 1}},
	{28, 2}:  {{1, 2, 1, 10}, {3, 25, 2, 1}},
	{28, 11}: {{1, 11, 11, 1}},
	{28, 12}: {{1, 1, 11, 12}, {2, 15, 12, 1}},
	{28, 13}: {{1, 15, 13, 1}},
	{28, 14}: {{1, 1, 13, 16}, {2, 10, 14, 1}},
	// KJV, WEB, and Livre append OSHB Joel 3:1-5 to control chapter 2
	// and number OSHB chapter 4 as control chapter 3.
	{29, 2}: {{1, 27, 2, 1}},
	{29, 3}: {{1, 5, 2, 28}},
	{29, 4}: {{1, 21, 3, 1}},
	// OSHB Jonah 2:1 is the final verse of control chapter 1.
	{32, 1}: {{1, 16, 1, 1}},
	{32, 2}: {{1, 1, 1, 17}, {2, 11, 2, 1}},
	// OSHB Mic 4:14 is control 5:1; the remaining chapter shifts by one.
	{33, 4}: {{1, 13, 4, 1}, {14, 14, 5, 1}},
	{33, 5}: {{1, 14, 5, 2}},
	// OSHB Nah 2:1 is the final verse of control chapter 1.
	{34, 1}: {{1, 14, 1, 1}},
	{34, 2}: {{1, 1, 1, 15}, {2, 14, 2, 1}},
	// OSHB Zech 2:1-4 are controls 1:18-21; 2:5-17 are controls 2:1-13.
	{38, 1}: {{1, 17, 1, 1}},
	{38, 2}: {{1, 4, 1, 18}, {5, 17, 2, 1}},
	// KJV, WEB, and Livre number OSHB Mal 3:19-24 as chapter 4:1-6.
	{39, 3}: {{1, 18, 3, 1}, {19, 24, 4, 1}},
}

// OSHBChapterText returns control text keyed by the OSHB verse number.
func OSHBChapterText(path string, bookNr, chapter int) (map[int]string, error) {
	return oshbChapterText(path, bookNr, chapter, 0)
}

func oshbChapterText(path string, bookNr, chapter, allowedMissingSourceVerse int) (map[int]string, error) {
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
				if sourceVerse == allowedMissingSourceVerse {
					continue
				}
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
