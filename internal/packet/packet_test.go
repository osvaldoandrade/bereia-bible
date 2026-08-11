package packet

import (
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
