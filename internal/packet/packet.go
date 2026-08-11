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
	if cs.web, err = ChapterText(req.WebPath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	if cs.kjv, err = ChapterText(req.KJVPath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	if cs.livre, err = ChapterText(req.LivrePath, req.BookNr, req.Chapter); err != nil {
		return cs, err
	}
	return cs, nil
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
