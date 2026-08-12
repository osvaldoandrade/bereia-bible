package packet

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const miniOSHB = `<?xml version="1.0" encoding="UTF-8"?>
<osis><osisText><chapter osisID="Gen.1">
<verse osisID="Gen.1.1"><w lemma="b/7225" morph="HR/Ncfsa">בְּ/רֵאשִׁית</w><seg type="x-sof-pasuq">׃</seg></verse>
<verse osisID="Gen.1.2"><w lemma="776" morph="HNcbsa">אֶרֶץ</w><seg type="x-sof-pasuq">׃</seg></verse>
</chapter></osisText></osis>`

const miniGetBible = `{"books":[{"nr":1,"chapters":[{"chapter":1,"verses":[
{"verse":1,"text":"No princípio... "},{"verse":2,"text":"E a terra... "}]}]}]}`

func write(t *testing.T, dir, name, content string) string {
	t.Helper()
	p := filepath.Join(dir, name)
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestBuild(t *testing.T) {
	dir := t.TempDir()
	oshbPath := write(t, dir, "Gen.xml", miniOSHB)
	write(t, dir, "COMMIT", "abc123\n")
	livre := write(t, dir, "livre.json", miniGetBible)

	p, err := Build(Request{
		OSHBPath: oshbPath, OSISBook: "Gen", BookNr: 1, Chapter: 1,
		From: 1, To: 2, Pericope: "Gen.1.1-2", LivrePath: livre,
	})
	if err != nil {
		t.Fatal(err)
	}
	if p.Unit != "Gen.1.1-2" || p.Source.GitCommit != "abc123" {
		t.Errorf("unit/commit wrong: %+v", p)
	}
	if len(p.Verses) != 2 || p.Verses[0].Number != 1 || p.Verses[1].Number != 2 {
		t.Fatalf("verses wrong: %+v", p.Verses)
	}
	if p.Verses[0].Controls == nil || !strings.HasPrefix(p.Verses[0].Controls.Livre, "No princípio") {
		t.Errorf("livre control missing/wrong: %+v", p.Verses[0].Controls)
	}
	if p.Verses[0].Controls.Livre != strings.TrimSpace(p.Verses[0].Controls.Livre) {
		t.Errorf("control text not trimmed")
	}
	if p.Verses[0].Controls.Web != "" {
		t.Errorf("web control should be empty when path not given")
	}
}

func TestBuildNoControls(t *testing.T) {
	dir := t.TempDir()
	oshbPath := write(t, dir, "Gen.xml", miniOSHB)
	p, err := Build(Request{
		OSHBPath: oshbPath, OSISBook: "Gen", BookNr: 1, Chapter: 1,
		From: 1, To: 1, Pericope: "Gen.1.1-1",
	})
	if err != nil {
		t.Fatal(err)
	}
	if p.Verses[0].Controls != nil {
		t.Errorf("controls should be nil without control paths")
	}
	if p.Source.GitCommit != "" {
		t.Errorf("commit should be empty without COMMIT file")
	}
}

func TestBuildErrors(t *testing.T) {
	dir := t.TempDir()
	oshbPath := write(t, dir, "Gen.xml", miniOSHB)
	livre := write(t, dir, "livre.json", miniGetBible)

	if _, err := Build(Request{OSHBPath: filepath.Join(dir, "nope.xml"), OSISBook: "Gen", Chapter: 1, From: 1, To: 1}); err == nil {
		t.Error("want error for missing oshb file")
	}
	if _, err := Build(Request{OSHBPath: oshbPath, OSISBook: "Gen", Chapter: 1, From: 1, To: 9, Pericope: "x"}); err == nil {
		t.Error("want error for missing verses")
	}
	if _, err := Build(Request{OSHBPath: oshbPath, OSISBook: "Gen", BookNr: 42, Chapter: 1, From: 1, To: 1, Pericope: "x", LivrePath: livre}); err == nil {
		t.Error("want error for unknown book in control")
	}
	bad := write(t, dir, "bad.json", "{")
	if _, err := Build(Request{OSHBPath: oshbPath, OSISBook: "Gen", BookNr: 1, Chapter: 1, From: 1, To: 1, Pericope: "x", WebPath: bad}); err == nil {
		t.Error("want error for malformed control json")
	}
}

func TestChapterTextEmptyPath(t *testing.T) {
	m, err := ChapterText("", 1, 1)
	if err != nil || m != nil {
		t.Errorf("empty path must be a no-op, got %v %v", m, err)
	}
}

func TestOSHBChapterTextMapsHebrewVersification(t *testing.T) {
	dir := t.TempDir()
	control := `{"books":[{"nr":3,"chapters":[
{"chapter":5,"verses":[{"verse":19,"text":"Levítico cinco dezenove"}]},
{"chapter":6,"verses":[
{"verse":1,"text":"Levítico seis um"},{"verse":2,"text":"Levítico seis dois"},
{"verse":3,"text":"Levítico seis três"},{"verse":4,"text":"Levítico seis quatro"},
{"verse":5,"text":"Levítico seis cinco"},{"verse":6,"text":"Levítico seis seis"},
{"verse":7,"text":"Levítico seis sete"}]}]}]}`
	path := write(t, dir, "lev.json", control)

	got, err := OSHBChapterText(path, 3, 5)
	if err == nil {
		t.Fatal("want error when a mapped control verse is missing")
	}

	var verses strings.Builder
	for i := 1; i <= 19; i++ {
		if i > 1 {
			verses.WriteByte(',')
		}
		fmt.Fprintf(&verses, `{"verse":%d,"text":"five-%d"}`, i, i)
	}
	control = fmt.Sprintf(`{"books":[{"nr":3,"chapters":[
{"chapter":5,"verses":[%s]},
{"chapter":6,"verses":[
{"verse":1,"text":"six-1"},{"verse":2,"text":"six-2"},{"verse":3,"text":"six-3"},
{"verse":4,"text":"six-4"},{"verse":5,"text":"six-5"},{"verse":6,"text":"six-6"},
{"verse":7,"text":"six-7"}]}]}]}`, verses.String())
	path = write(t, dir, "complete.json", control)
	got, err = OSHBChapterText(path, 3, 5)
	if err != nil {
		t.Fatal(err)
	}
	if got[19] != "five-19" || got[20] != "six-1" || got[26] != "six-7" {
		t.Fatalf("wrong mapping: 19=%q 20=%q 26=%q", got[19], got[20], got[26])
	}
}

func TestOSHBChapterTextMapsNumbersVersification(t *testing.T) {
	dir := t.TempDir()
	var c16, c17, c25, c30 strings.Builder
	for i := 36; i <= 50; i++ {
		if i > 36 {
			c16.WriteByte(',')
		}
		fmt.Fprintf(&c16, `{"verse":%d,"text":"sixteen-%d"}`, i, i)
	}
	for i := 1; i <= 13; i++ {
		if i > 1 {
			c17.WriteByte(',')
		}
		fmt.Fprintf(&c17, `{"verse":%d,"text":"seventeen-%d"}`, i, i)
	}
	for i := 1; i <= 18; i++ {
		if i > 1 {
			c25.WriteByte(',')
		}
		fmt.Fprintf(&c25, `{"verse":%d,"text":"twenty-five-%d"}`, i, i)
	}
	for i := 1; i <= 16; i++ {
		if i > 1 {
			c30.WriteByte(',')
		}
		fmt.Fprintf(&c30, `{"verse":%d,"text":"thirty-%d"}`, i, i)
	}
	control := fmt.Sprintf(`{"books":[{"nr":4,"chapters":[
{"chapter":16,"verses":[%s]},
{"chapter":17,"verses":[%s]},
{"chapter":25,"verses":[%s]},
{"chapter":26,"verses":[{"verse":1,"text":"twenty-six-1"}]},
{"chapter":29,"verses":[{"verse":40,"text":"twenty-nine-40"}]},
{"chapter":30,"verses":[%s]}]}]}`, c16.String(), c17.String(), c25.String(), c30.String())
	path := write(t, dir, "numbers.json", control)

	got, err := OSHBChapterText(path, 4, 17)
	if err != nil {
		t.Fatal(err)
	}
	if got[1] != "sixteen-36" || got[15] != "sixteen-50" ||
		got[16] != "seventeen-1" || got[28] != "seventeen-13" {
		t.Fatalf("wrong Numbers 17 mapping: 1=%q 15=%q 16=%q 28=%q",
			got[1], got[15], got[16], got[28])
	}

	got, err = OSHBChapterText(path, 4, 25)
	if err != nil {
		t.Fatal(err)
	}
	if got[18] != "twenty-five-18" || got[19] != "twenty-six-1" {
		t.Fatalf("wrong Numbers 25 mapping: 18=%q 19=%q", got[18], got[19])
	}

	got, err = OSHBChapterText(path, 4, 30)
	if err != nil {
		t.Fatal(err)
	}
	if got[1] != "twenty-nine-40" || got[2] != "thirty-1" || got[17] != "thirty-16" {
		t.Fatalf("wrong Numbers 30 mapping: 1=%q 2=%q 17=%q", got[1], got[2], got[17])
	}
}
