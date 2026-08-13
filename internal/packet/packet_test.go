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

const miniNestle = "\ufeffBCV\ttext\tfunc_morph\tform_morph\tstrongs\tlemma\tnormalized\n" +
	"Matt 1:1\tΒίβλος,\tN-NSF\tN-NSF\t976\tβίβλος\tΒίβλος\n" +
	"Matt 1:1\tγενέσεως.\tN-GSF\tN-GSF\t1078\tγένεσις\tγενέσεως\n" +
	"Matt 1:3\tἸησοῦ.\tN-GSM\tN-GSM\t2424\tἸησοῦς\tἸησοῦ\n"

const miniNTControl = `{"books":[{"nr":40,"chapters":[{"chapter":1,"verses":[
{"verse":1,"text":"Book of genealogy"},{"verse":2,"text":"traditional extra"},
{"verse":3,"text":"of Jesus"}]}]}]}`

const miniNestleMark = "BCV\ttext\tfunc_morph\tform_morph\tstrongs\tlemma\tnormalized\n" +
	"Mark 16:20\tσημείων.]]\tN-GPN\tN-GPN\t4592\tσημεῖον\tσημείων\n" +
	"Mark 16:99\t[[Πάντα\tA-APN\tA-APN\t3956\tπᾶς\tΠάντα\n" +
	"Mark 16:99\tσωτηρίας.]]\tN-GSF\tN-GSF\t4991\tσωτηρία\tσωτηρίας\n"

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

func TestBuildNestleAllowsSourceGapAndPreservesAnnotations(t *testing.T) {
	dir := t.TempDir()
	nestlePath := write(t, dir, "Nestle1904.csv", miniNestle)
	write(t, dir, "COMMIT", "deadbeef\n")
	control := write(t, dir, "web.json", miniNTControl)
	p, err := BuildNestle(NestleRequest{
		NestlePath: nestlePath, OSISBook: "Matt", BookNr: 40, Chapter: 1,
		From: 1, To: 3, Pericope: "Matt.1.1-3", WebPath: control,
	})
	if err != nil {
		t.Fatal(err)
	}
	if p.Source.ID != "nestle1904" || p.Source.GitCommit != "deadbeef" {
		t.Fatalf("source pin wrong: %+v", p.Source)
	}
	if len(p.Verses) != 2 || p.Verses[0].OSIS != "Matt.1.1" || p.Verses[1].OSIS != "Matt.1.3" {
		t.Fatalf("source gap was not preserved: %+v", p.Verses)
	}
	if p.Verses[0].Hebrew != "" || p.Verses[0].Greek != "Βίβλος, γενέσεως." {
		t.Fatalf("wrong original-language field: %+v", p.Verses[0])
	}
	word := p.Verses[0].Words[0]
	if word.Surface != "Βίβλος" || word.Morph != "N-NSF" || word.FunctionalMorph != "N-NSF" || word.Strong != "976" {
		t.Fatalf("Greek word annotations lost: %+v", word)
	}
	if p.Verses[0].Controls == nil || p.Verses[0].Controls.Web != "Book of genealogy" {
		t.Fatalf("direct control missing: %+v", p.Verses[0].Controls)
	}
}

func TestNestleControlsHandleCriticalVerseBoundaries(t *testing.T) {
	acts := controlSet{
		web:   map[int]string{40: "web-40", 41: "web-41"},
		kjv:   map[int]string{40: "kjv-40", 41: "kjv-41"},
		livre: map[int]string{40: "livre-40", 41: "livre-41"},
	}
	got := nestleControlsForVerse(acts, 44, 19, 40)
	if got == nil || got.Web != "web-40 web-41" || got.KJV != "kjv-40 kjv-41" || got.Livre != "livre-40 livre-41" {
		t.Fatalf("Acts 19:40 mapping: %+v", got)
	}

	cs := controlSet{
		web:   map[int]string{12: "web-12", 13: "web-13", 14: "web-14"},
		kjv:   map[int]string{12: "kjv-12", 13: "kjv-13", 14: "kjv-14"},
		livre: map[int]string{12: "livre-12", 13: "livre-13", 14: "livre-14"},
	}
	got = nestleControlsForVerse(cs, 47, 13, 12)
	if got == nil || got.Web != "web-12 web-13" || got.KJV != "kjv-12 kjv-13" || got.Livre != "livre-12 livre-13" {
		t.Fatalf("2Cor 13:12 mapping: %+v", got)
	}
	got = nestleControlsForVerse(cs, 47, 13, 13)
	if got == nil || got.Web != "web-14" || got.KJV != "kjv-14" || got.Livre != "livre-14" {
		t.Fatalf("2Cor 13:13 mapping: %+v", got)
	}

	cs = controlSet{
		web: map[int]string{14: "web mixed"}, kjv: map[int]string{14: "kjv mixed"}, livre: map[int]string{14: "livre mixed"},
	}
	if got := nestleControlsForVerse(cs, 64, 1, 14); got != nil {
		t.Fatalf("3John 1:14 mixed control must be omitted: %+v", got)
	}
	if got := nestleControlsForVerse(cs, 64, 1, 15); got != nil {
		t.Fatalf("3John 1:15 mixed control must be omitted: %+v", got)
	}

	cs = controlSet{
		web: map[int]string{1: "web mixed"}, kjv: map[int]string{1: "kjv mixed"}, livre: map[int]string{1: "livre exact"},
	}
	got = nestleControlsForVerse(cs, 66, 13, 1)
	if got == nil || got.Web != "" || got.KJV != "" || got.Livre != "livre exact" {
		t.Fatalf("Rev 13:1 controls: %+v", got)
	}
}

func TestBuildNestlePreservesMarkShortEndingAsSourceVariant(t *testing.T) {
	dir := t.TempDir()
	nestlePath := write(t, dir, "Nestle1904.csv", miniNestleMark)
	p, err := BuildNestle(NestleRequest{
		NestlePath: nestlePath, OSISBook: "Mark", BookNr: 41, Chapter: 16,
		From: 20, To: 20, Pericope: "Mark.16.20",
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Verses) != 1 || len(p.Verses[0].SourceVariants) != 1 {
		t.Fatalf("short ending apparatus missing: %+v", p.Verses)
	}
	variant := p.Verses[0].SourceVariants[0]
	if variant.Reference != "Mark.16.99" || variant.Greek != "[[Πάντα σωτηρίας.]]" {
		t.Fatalf("short ending source changed: %+v", variant)
	}
	if len(variant.Words) != 4 || variant.Words[1].Surface != "Πάντα" || variant.Words[2].Lemma != "σωτηρία" {
		t.Fatalf("short ending annotations lost: %+v", variant.Words)
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

func TestOSHBChapterTextMapsDeuteronomyVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":5,"chapters":[%s,%s,%s,%s,%s,%s]}]}`,
		chapter(12, 1, 32), chapter(13, 1, 18),
		chapter(22, 1, 30), chapter(23, 1, 25),
		chapter(28, 1, 68), chapter(29, 1, 29))
	path := write(t, dir, "deuteronomy.json", control)

	tests := []struct {
		chapter int
		want    map[int]string
	}{
		{12, map[int]string{1: "chapter-12-verse-1", 31: "chapter-12-verse-31"}},
		{13, map[int]string{1: "chapter-12-verse-32", 2: "chapter-13-verse-1", 19: "chapter-13-verse-18"}},
		{22, map[int]string{1: "chapter-22-verse-1", 29: "chapter-22-verse-29"}},
		{23, map[int]string{1: "chapter-22-verse-30", 2: "chapter-23-verse-1", 26: "chapter-23-verse-25"}},
		{28, map[int]string{1: "chapter-28-verse-1", 68: "chapter-28-verse-68", 69: "chapter-29-verse-1"}},
		{29, map[int]string{1: "chapter-29-verse-2", 28: "chapter-29-verse-29"}},
	}
	for _, tt := range tests {
		got, err := OSHBChapterText(path, 5, tt.chapter)
		if err != nil {
			t.Fatalf("chapter %d: %v", tt.chapter, err)
		}
		for verse, want := range tt.want {
			if got[verse] != want {
				t.Errorf("chapter %d verse %d: got %q, want %q", tt.chapter, verse, got[verse], want)
			}
		}
	}
}

func TestOSHBChapterTextMapsSamuelVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	firstSamuel := fmt.Sprintf(`{"books":[{"nr":9,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(20, 1, 42), chapter(21, 1, 15),
		chapter(23, 1, 29), chapter(24, 1, 22))
	firstPath := write(t, dir, "first-samuel.json", firstSamuel)

	firstTests := []struct {
		chapter int
		wantLen int
		want    map[int]string
	}{
		{21, 16, map[int]string{1: "chapter-20-verse-42", 2: "chapter-21-verse-1", 16: "chapter-21-verse-15"}},
		{24, 23, map[int]string{1: "chapter-23-verse-29", 2: "chapter-24-verse-1", 23: "chapter-24-verse-22"}},
	}
	for _, tt := range firstTests {
		got, err := OSHBChapterText(firstPath, 9, tt.chapter)
		if err != nil {
			t.Fatalf("1 Samuel %d: %v", tt.chapter, err)
		}
		if len(got) != tt.wantLen {
			t.Fatalf("wrong 1 Samuel %d control count: got %d, want %d", tt.chapter, len(got), tt.wantLen)
		}
		for verse, want := range tt.want {
			if got[verse] != want {
				t.Errorf("1 Samuel %d:%d: got %q, want %q", tt.chapter, verse, got[verse], want)
			}
		}
	}

	secondSamuel := fmt.Sprintf(`{"books":[{"nr":10,"chapters":[%s,%s]}]}`,
		chapter(18, 1, 33), chapter(19, 1, 43))
	secondPath := write(t, dir, "second-samuel.json", secondSamuel)

	got, err := OSHBChapterText(secondPath, 10, 19)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 44 {
		t.Fatalf("wrong 2 Samuel 19 control count: got %d, want 44", len(got))
	}
	if got[1] != "chapter-18-verse-33" || got[2] != "chapter-19-verse-1" ||
		got[44] != "chapter-19-verse-43" {
		t.Fatalf("wrong 2 Samuel 19 mapping: 1=%q 2=%q 44=%q", got[1], got[2], got[44])
	}
}

func TestOSHBChapterTextMapsKingsVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":11,"chapters":[%s,%s,%s]}]}`,
		chapter(4, 1, 34), chapter(5, 1, 18), chapter(22, 1, 53))
	path := write(t, dir, "first-kings.json", control)

	chapter5, err := OSHBChapterText(path, 11, 5)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter5) != 32 {
		t.Fatalf("wrong 1 Kings 5 control count: got %d, want 32", len(chapter5))
	}
	for sourceVerse := 1; sourceVerse <= 32; sourceVerse++ {
		controlChapter := 4
		controlVerse := sourceVerse + 20
		if sourceVerse >= 15 {
			controlChapter = 5
			controlVerse = sourceVerse - 14
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if got := chapter5[sourceVerse]; got != want {
			t.Errorf("1 Kings 5:%d: got %q, want %q", sourceVerse, got, want)
		}
	}
	for _, verse := range []int{0, 33} {
		if _, ok := chapter5[verse]; ok {
			t.Errorf("unexpected 1 Kings 5:%d control", verse)
		}
	}

	chapter22, err := OSHBChapterText(path, 11, 22)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter22) != 52 {
		t.Fatalf("wrong 1 Kings 22 control count: got %d, want 52", len(chapter22))
	}
	for sourceVerse := 1; sourceVerse <= 54; sourceVerse++ {
		if sourceVerse == 43 || sourceVerse == 44 {
			if _, ok := chapter22[sourceVerse]; ok {
				t.Errorf("1 Kings 22:%d must not have a mixed 22:43 control", sourceVerse)
			}
			continue
		}
		controlVerse := sourceVerse
		if sourceVerse >= 45 {
			controlVerse--
		}
		want := fmt.Sprintf("chapter-22-verse-%d", controlVerse)
		if got := chapter22[sourceVerse]; got != want {
			t.Errorf("1 Kings 22:%d: got %q, want %q", sourceVerse, got, want)
		}
	}
	for _, verse := range []int{0, 55} {
		if _, ok := chapter22[verse]; ok {
			t.Errorf("unexpected 1 Kings 22:%d control", verse)
		}
	}

	controls, err := loadControls(Request{
		BookNr: 11, Chapter: 22,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, verse := range []int{43, 44} {
		if got := controls.forVerse(verse); got != nil {
			t.Errorf("1 Kings 22:%d controls must be omitted, got %+v", verse, got)
		}
	}
	for _, verse := range []int{42, 45} {
		got := controls.forVerse(verse)
		if got == nil || got.Web == "" || got.KJV == "" || got.Livre == "" {
			t.Errorf("1 Kings 22:%d must retain all controls, got %+v", verse, got)
		}
	}
}

func TestOSHBChapterTextMapsSecondKingsVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":12,"chapters":[%s,%s]}]}`,
		chapter(11, 1, 21), chapter(12, 1, 21))
	path := write(t, dir, "second-kings.json", control)

	chapter11, err := OSHBChapterText(path, 12, 11)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter11) != 20 {
		t.Fatalf("wrong 2 Kings 11 control count: got %d, want 20", len(chapter11))
	}
	for sourceVerse := 1; sourceVerse <= 20; sourceVerse++ {
		want := fmt.Sprintf("chapter-11-verse-%d", sourceVerse)
		if chapter11[sourceVerse] != want {
			t.Errorf("2 Kings 11:%d: got %q, want %q", sourceVerse, chapter11[sourceVerse], want)
		}
	}
	for _, verse := range []int{0, 21} {
		if _, ok := chapter11[verse]; ok {
			t.Errorf("unexpected 2 Kings 11:%d control", verse)
		}
	}

	got, err := OSHBChapterText(path, 12, 12)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 22 {
		t.Fatalf("wrong 2 Kings 12 control count: got %d, want 22", len(got))
	}
	for sourceVerse := 1; sourceVerse <= 22; sourceVerse++ {
		controlChapter := 11
		controlVerse := 21
		if sourceVerse >= 2 {
			controlChapter = 12
			controlVerse = sourceVerse - 1
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if got[sourceVerse] != want {
			t.Errorf("2 Kings 12:%d: got %q, want %q", sourceVerse, got[sourceVerse], want)
		}
	}
	for _, verse := range []int{0, 23} {
		if _, ok := got[verse]; ok {
			t.Errorf("unexpected 2 Kings 12:%d control", verse)
		}
	}

	controls, err := loadControls(Request{
		BookNr: 12, Chapter: 12,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, verse := range []int{1, 2, 22} {
		got := controls.forVerse(verse)
		controlChapter := 11
		controlVerse := 21
		if verse >= 2 {
			controlChapter = 12
			controlVerse = verse - 1
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("2 Kings 12:%d: got %+v, want all controls %q", verse, got, want)
		}
	}
}

func TestOSHBChapterTextMapsFirstChroniclesVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":13,"chapters":[%s,%s,%s]}]}`,
		chapter(5, 1, 26), chapter(6, 1, 81), chapter(12, 1, 40))
	path := write(t, dir, "first-chronicles.json", control)

	tests := []struct {
		chapter int
		wantLen int
		want    func(int) string
	}{
		{5, 41, func(sourceVerse int) string {
			if sourceVerse <= 26 {
				return fmt.Sprintf("chapter-5-verse-%d", sourceVerse)
			}
			return fmt.Sprintf("chapter-6-verse-%d", sourceVerse-26)
		}},
		{6, 66, func(sourceVerse int) string {
			return fmt.Sprintf("chapter-6-verse-%d", sourceVerse+15)
		}},
		{12, 39, func(sourceVerse int) string {
			if sourceVerse == 4 || sourceVerse == 5 {
				return ""
			}
			if sourceVerse <= 3 {
				return fmt.Sprintf("chapter-12-verse-%d", sourceVerse)
			}
			return fmt.Sprintf("chapter-12-verse-%d", sourceVerse-1)
		}},
	}
	for _, tt := range tests {
		got, err := OSHBChapterText(path, 13, tt.chapter)
		if err != nil {
			t.Fatalf("1 Chronicles %d: %v", tt.chapter, err)
		}
		if len(got) != tt.wantLen {
			t.Fatalf("wrong 1 Chronicles %d control count: got %d, want %d", tt.chapter, len(got), tt.wantLen)
		}
		lastVerse := map[int]int{5: 41, 6: 66, 12: 41}[tt.chapter]
		for sourceVerse := 1; sourceVerse <= lastVerse; sourceVerse++ {
			want := tt.want(sourceVerse)
			if got[sourceVerse] != want {
				t.Errorf("1 Chronicles %d:%d: got %q, want %q", tt.chapter, sourceVerse, got[sourceVerse], want)
			}
		}
	}

	controls, err := loadControls(Request{
		BookNr: 13, Chapter: 12,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, verse := range []int{4, 5} {
		if got := controls.forVerse(verse); got != nil {
			t.Errorf("1 Chronicles 12:%d controls must be omitted, got %+v", verse, got)
		}
	}
	for _, verse := range []int{3, 6, 41} {
		got := controls.forVerse(verse)
		if got == nil || got.Web == "" || got.KJV == "" || got.Livre == "" {
			t.Errorf("1 Chronicles 12:%d must retain all controls, got %+v", verse, got)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":13,"chapters":[%s]}]}`, chapter(6, 1, 80))
	missingPath := write(t, dir, "first-chronicles-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 13, 6); err == nil {
		t.Fatal("want error when mapped 1 Chronicles 6:81 control is missing")
	}
}

func TestOSHBChapterTextMapsSecondChroniclesVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":14,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(1, 1, 17), chapter(2, 1, 18), chapter(13, 1, 22), chapter(14, 1, 15))
	path := write(t, dir, "second-chronicles.json", control)

	tests := []struct {
		chapter int
		wantLen int
		want    func(int) string
	}{
		{1, 18, func(sourceVerse int) string {
			if sourceVerse <= 17 {
				return fmt.Sprintf("chapter-1-verse-%d", sourceVerse)
			}
			return "chapter-2-verse-1"
		}},
		{2, 17, func(sourceVerse int) string {
			return fmt.Sprintf("chapter-2-verse-%d", sourceVerse+1)
		}},
		{13, 23, func(sourceVerse int) string {
			if sourceVerse <= 22 {
				return fmt.Sprintf("chapter-13-verse-%d", sourceVerse)
			}
			return "chapter-14-verse-1"
		}},
		{14, 14, func(sourceVerse int) string {
			return fmt.Sprintf("chapter-14-verse-%d", sourceVerse+1)
		}},
	}
	lastVerse := map[int]int{1: 18, 2: 17, 13: 23, 14: 14}
	for _, tt := range tests {
		got, err := OSHBChapterText(path, 14, tt.chapter)
		if err != nil {
			t.Fatalf("2 Chronicles %d: %v", tt.chapter, err)
		}
		if len(got) != tt.wantLen {
			t.Fatalf("wrong 2 Chronicles %d control count: got %d, want %d", tt.chapter, len(got), tt.wantLen)
		}
		for sourceVerse := 1; sourceVerse <= lastVerse[tt.chapter]; sourceVerse++ {
			want := tt.want(sourceVerse)
			if got[sourceVerse] != want {
				t.Errorf("2 Chronicles %d:%d: got %q, want %q", tt.chapter, sourceVerse, got[sourceVerse], want)
			}
		}

		controls, err := loadControls(Request{
			BookNr: 14, Chapter: tt.chapter,
			WebPath: path, KJVPath: path, LivrePath: path,
		})
		if err != nil {
			t.Fatal(err)
		}
		for sourceVerse := 1; sourceVerse <= lastVerse[tt.chapter]; sourceVerse++ {
			want := tt.want(sourceVerse)
			got := controls.forVerse(sourceVerse)
			if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
				t.Errorf("2 Chronicles %d:%d: got %+v, want all controls %q", tt.chapter, sourceVerse, got, want)
			}
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":14,"chapters":[%s]}]}`, chapter(14, 1, 14))
	missingPath := write(t, dir, "second-chronicles-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 14, 14); err == nil {
		t.Fatal("want error when mapped 2 Chronicles 14:15 control is missing")
	}
}

func TestOSHBChapterTextMapsNehemiahVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":16,"chapters":[%s,%s,%s,%s,%s,%s]}]}`,
		chapter(3, 1, 32), chapter(4, 1, 23), chapter(7, 1, 73),
		chapter(9, 1, 38), chapter(10, 1, 39), chapter(13, 1, 31))
	path := write(t, dir, "nehemiah.json", control)

	tests := []struct {
		chapter int
		wantLen int
		last    int
		want    func(int) string
	}{
		{3, 38, 38, func(sourceVerse int) string {
			if sourceVerse <= 32 {
				return fmt.Sprintf("chapter-3-verse-%d", sourceVerse)
			}
			return fmt.Sprintf("chapter-4-verse-%d", sourceVerse-32)
		}},
		{4, 17, 17, func(sourceVerse int) string {
			return fmt.Sprintf("chapter-4-verse-%d", sourceVerse+6)
		}},
		{7, 72, 72, func(sourceVerse int) string {
			if sourceVerse <= 67 {
				return fmt.Sprintf("chapter-7-verse-%d", sourceVerse)
			}
			return fmt.Sprintf("chapter-7-verse-%d", sourceVerse+1)
		}},
		{9, 37, 37, func(sourceVerse int) string {
			return fmt.Sprintf("chapter-9-verse-%d", sourceVerse)
		}},
		{10, 40, 40, func(sourceVerse int) string {
			if sourceVerse == 1 {
				return "chapter-9-verse-38"
			}
			return fmt.Sprintf("chapter-10-verse-%d", sourceVerse-1)
		}},
	}
	for _, tt := range tests {
		got, err := OSHBChapterText(path, 16, tt.chapter)
		if err != nil {
			t.Fatalf("Nehemiah %d: %v", tt.chapter, err)
		}
		if len(got) != tt.wantLen {
			t.Fatalf("wrong Nehemiah %d control count: got %d, want %d", tt.chapter, len(got), tt.wantLen)
		}
		for sourceVerse := 1; sourceVerse <= tt.last; sourceVerse++ {
			want := tt.want(sourceVerse)
			if got[sourceVerse] != want {
				t.Errorf("Nehemiah %d:%d: got %q, want %q", tt.chapter, sourceVerse, got[sourceVerse], want)
			}
		}
	}

	controls, err := loadControls(Request{
		BookNr: 16, Chapter: 7,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, verse := range []int{67, 68, 72} {
		wantVerse := verse
		if verse >= 68 {
			wantVerse++
		}
		want := fmt.Sprintf("chapter-7-verse-%d", wantVerse)
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Nehemiah 7:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":16,"chapters":[%s]}]}`, chapter(10, 1, 38))
	missingPath := write(t, dir, "nehemiah-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 16, 10); err == nil {
		t.Fatal("want error when mapped Nehemiah 10:39 control is missing")
	}
}

func TestOSHBChapterTextMapsJobVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":18,"chapters":[%s,%s]}]}`,
		chapter(40, 1, 24), chapter(41, 1, 34))
	path := write(t, dir, "job.json", control)

	chapter40, err := OSHBChapterText(path, 18, 40)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter40) != 32 {
		t.Fatalf("wrong Job 40 control count: got %d, want 32", len(chapter40))
	}
	for sourceVerse := 1; sourceVerse <= 32; sourceVerse++ {
		want := fmt.Sprintf("chapter-40-verse-%d", sourceVerse)
		if sourceVerse >= 25 {
			want = fmt.Sprintf("chapter-41-verse-%d", sourceVerse-24)
		}
		if chapter40[sourceVerse] != want {
			t.Errorf("Job 40:%d: got %q, want %q", sourceVerse, chapter40[sourceVerse], want)
		}
	}

	chapter41, err := OSHBChapterText(path, 18, 41)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter41) != 26 {
		t.Fatalf("wrong Job 41 control count: got %d, want 26", len(chapter41))
	}
	for sourceVerse := 1; sourceVerse <= 26; sourceVerse++ {
		want := fmt.Sprintf("chapter-41-verse-%d", sourceVerse+8)
		if chapter41[sourceVerse] != want {
			t.Errorf("Job 41:%d: got %q, want %q", sourceVerse, chapter41[sourceVerse], want)
		}
	}

	controls, err := loadControls(Request{
		BookNr: 18, Chapter: 40,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, verse := range []int{24, 25, 32} {
		want := fmt.Sprintf("chapter-40-verse-%d", verse)
		if verse >= 25 {
			want = fmt.Sprintf("chapter-41-verse-%d", verse-24)
		}
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Job 40:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":18,"chapters":[%s]}]}`, chapter(41, 1, 33))
	missingPath := write(t, dir, "job-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 18, 41); err == nil {
		t.Fatal("want error when mapped Job 41:34 control is missing")
	}
}

func TestOSHBChapterTextMapsPsalmsVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, count int, missing map[int]bool) string {
		var verses strings.Builder
		first := true
		for i := 1; i <= count; i++ {
			if missing[i] {
				continue
			}
			if !first {
				verses.WriteByte(',')
			}
			first = false
			fmt.Fprintf(&verses, `{"verse":%d,"text":"psalm-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":19,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(3, 8, nil), chapter(13, 6, nil), chapter(46, 11, nil), chapter(51, 19, nil))
	path := write(t, dir, "psalms.json", control)

	cases := []struct {
		chapter int
		from    int
		to      int
		offset  int
	}{
		{chapter: 3, from: 2, to: 9, offset: 1},
		{chapter: 51, from: 3, to: 21, offset: 2},
	}
	for _, tc := range cases {
		got, err := OSHBChapterText(path, 19, tc.chapter)
		if err != nil {
			t.Fatal(err)
		}
		if len(got) != tc.to-tc.from+1 {
			t.Fatalf("Psalm %d: got %d controls", tc.chapter, len(got))
		}
		for sourceVerse := tc.from; sourceVerse <= tc.to; sourceVerse++ {
			controlVerse := sourceVerse - tc.offset
			want := fmt.Sprintf("psalm-%d-verse-%d", tc.chapter, controlVerse)
			if got[sourceVerse] != want {
				t.Errorf("Psalm %d:%d: got %q, want %q", tc.chapter, sourceVerse, got[sourceVerse], want)
			}
		}
		for sourceVerse := 1; sourceVerse < tc.from; sourceVerse++ {
			if _, ok := got[sourceVerse]; ok {
				t.Errorf("Psalm %d title verse %d unexpectedly has a control", tc.chapter, sourceVerse)
			}
		}
	}

	chapter13, err := OSHBChapterText(path, 19, 13)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter13) != 4 || chapter13[2] != "psalm-13-verse-1" || chapter13[5] != "psalm-13-verse-4" {
		t.Fatalf("wrong Psalm 13 controls: %+v", chapter13)
	}
	if _, ok := chapter13[1]; ok {
		t.Fatal("Psalm 13 title unexpectedly has a control")
	}
	if _, ok := chapter13[6]; ok {
		t.Fatal("Psalm 13:6 must not receive either half of the split control")
	}

	livre := fmt.Sprintf(`{"books":[{"nr":19,"chapters":[%s]}]}`,
		chapter(46, 11, map[int]bool{3: true}))
	livrePath := write(t, dir, "livre.json", livre)
	controls, err := loadControls(Request{
		BookNr: 19, Chapter: 46,
		WebPath: path, KJVPath: path, LivrePath: livrePath,
	})
	if err != nil {
		t.Fatal(err)
	}
	if got := controls.forVerse(2); got == nil || got.Web == "" || got.KJV == "" || got.Livre == "" {
		t.Fatalf("Psalm 46:2 should retain all three independent controls: %+v", got)
	}
	for _, sourceVerse := range []int{3, 4} {
		got := controls.forVerse(sourceVerse)
		if got == nil || got.Web == "" || got.KJV == "" || got.Livre != "" {
			t.Errorf("Psalm 46:%d: mixed Livre control not isolated: %+v", sourceVerse, got)
		}
	}
	if got := controls.forVerse(5); got == nil || got.Livre != "psalm-46-verse-4" {
		t.Fatalf("Psalm 46:5 mapping after Livre gap is wrong: %+v", got)
	}
	for missingControl := 1; missingControl <= 11; missingControl++ {
		if missingControl == 3 {
			continue
		}
		badLivre := fmt.Sprintf(`{"books":[{"nr":19,"chapters":[%s]}]}`,
			chapter(46, 11, map[int]bool{3: true, missingControl: true}))
		badLivrePath := write(t, dir, fmt.Sprintf("livre-extra-gap-%d.json", missingControl), badLivre)
		if _, err := loadControls(Request{
			BookNr: 19, Chapter: 46,
			WebPath: path, KJVPath: path, LivrePath: badLivrePath,
		}); err == nil {
			t.Errorf("want error for unapproved missing Livre Psalm 46:%d", missingControl)
		}
	}

	// Exercise all 150 source chapters against the pinned OSHB verse counts,
	// rather than testing only representative one- and two-title cases.
	sourceCounts := []int{
		6, 12, 9, 9, 13, 11, 18, 10, 21, 18, 7, 9, 6, 7, 5,
		11, 15, 51, 15, 10, 14, 32, 6, 10, 22, 12, 14, 9, 11, 13,
		25, 11, 22, 23, 28, 13, 40, 23, 14, 18, 14, 12, 5, 27, 18,
		12, 10, 15, 21, 23, 21, 11, 7, 9, 24, 14, 12, 12, 18, 14,
		9, 13, 12, 11, 14, 20, 8, 36, 37, 6, 24, 20, 28, 23, 11,
		13, 21, 72, 13, 20, 17, 8, 19, 13, 14, 17, 7, 19, 53, 17,
		16, 16, 5, 23, 11, 13, 12, 9, 9, 5, 8, 29, 22, 35, 45,
		48, 43, 14, 31, 7, 10, 10, 9, 8, 18, 19, 2, 29, 176, 7,
		8, 9, 4, 8, 5, 6, 5, 6, 8, 8, 3, 18, 3, 3, 21,
		26, 9, 8, 24, 14, 10, 8, 12, 15, 21, 10, 20, 14, 9, 6,
	}
	titleVerses := map[int]int{
		3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 12: 1,
		18: 1, 19: 1, 20: 1, 21: 1, 22: 1, 30: 1, 31: 1, 34: 1,
		36: 1, 38: 1, 39: 1, 40: 1, 41: 1, 42: 1, 44: 1, 45: 1,
		46: 1, 47: 1, 48: 1, 49: 1, 51: 2, 52: 2, 53: 1, 54: 2,
		55: 1, 56: 1, 57: 1, 58: 1, 59: 1, 60: 2, 61: 1, 62: 1,
		63: 1, 64: 1, 65: 1, 67: 1, 68: 1, 69: 1, 70: 1, 75: 1,
		76: 1, 77: 1, 80: 1, 81: 1, 83: 1, 84: 1, 85: 1, 88: 1,
		89: 1, 92: 1, 102: 1, 108: 1, 140: 1, 142: 1,
	}
	var allChapters strings.Builder
	controlTotal := 0
	for i, sourceCount := range sourceCounts {
		chapterNumber := i + 1
		controlCount := sourceCount - titleVerses[chapterNumber]
		if chapterNumber == 13 {
			controlCount = 6 // controls 5-6 split the single source verse 13:6
		}
		if i > 0 {
			allChapters.WriteByte(',')
		}
		allChapters.WriteString(chapter(chapterNumber, controlCount, nil))
		controlTotal += controlCount
	}
	allControl := fmt.Sprintf(`{"books":[{"nr":19,"chapters":[%s]}]}`, allChapters.String())
	allPath := write(t, dir, "all-psalms.json", allControl)
	mappedTotal := 0
	seenControls := make(map[string]bool)
	for i, sourceCount := range sourceCounts {
		chapterNumber := i + 1
		got, err := OSHBChapterText(allPath, 19, chapterNumber)
		if err != nil {
			t.Fatalf("Psalm %d: %v", chapterNumber, err)
		}
		from, to := 1, sourceCount
		offset := 0
		if titleCount := titleVerses[chapterNumber]; titleCount > 0 {
			from, offset = titleCount+1, titleCount
		}
		if chapterNumber == 13 {
			from, to, offset = 2, 5, 1
		}
		if len(got) != to-from+1 {
			t.Errorf("Psalm %d: got %d mappings, want %d", chapterNumber, len(got), to-from+1)
		}
		for sourceVerse := from; sourceVerse <= to; sourceVerse++ {
			controlVerse := sourceVerse - offset
			want := fmt.Sprintf("psalm-%d-verse-%d", chapterNumber, controlVerse)
			if got[sourceVerse] != want {
				t.Errorf("Psalm %d:%d: got %q, want %q", chapterNumber, sourceVerse, got[sourceVerse], want)
			}
			if seenControls[want] {
				t.Errorf("control used more than once: %s", want)
			}
			seenControls[want] = true
			mappedTotal++
		}
	}
	if controlTotal != 2461 || mappedTotal != 2459 || len(seenControls) != 2459 {
		t.Fatalf("Psalm totals: controls=%d mapped=%d unique=%d", controlTotal, mappedTotal, len(seenControls))
	}

	missing := fmt.Sprintf(`{"books":[{"nr":19,"chapters":[%s]}]}`, chapter(3, 7, nil))
	missingPath := write(t, dir, "psalms-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 19, 3); err == nil {
		t.Fatal("want error when mapped Psalm 3:8 control is missing")
	}
}

func TestOSHBChapterTextMapsEcclesiastesAndSongVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}

	eccl := fmt.Sprintf(`{"books":[{"nr":21,"chapters":[%s,%s]}]}`,
		chapter(4, 1, 16), chapter(5, 1, 20))
	ecclPath := write(t, dir, "ecclesiastes.json", eccl)
	chapter4, err := OSHBChapterText(ecclPath, 21, 4)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter4) != 17 || chapter4[16] != "chapter-4-verse-16" || chapter4[17] != "chapter-5-verse-1" {
		t.Fatalf("wrong Ecclesiastes 4 mapping: len=%d 16=%q 17=%q", len(chapter4), chapter4[16], chapter4[17])
	}
	chapter5, err := OSHBChapterText(ecclPath, 21, 5)
	if err != nil {
		t.Fatal(err)
	}
	for sourceVerse := 1; sourceVerse <= 19; sourceVerse++ {
		want := fmt.Sprintf("chapter-5-verse-%d", sourceVerse+1)
		if chapter5[sourceVerse] != want {
			t.Errorf("Ecclesiastes 5:%d: got %q, want %q", sourceVerse, chapter5[sourceVerse], want)
		}
	}

	song := fmt.Sprintf(`{"books":[{"nr":22,"chapters":[%s,%s]}]}`,
		chapter(6, 1, 13), chapter(7, 1, 13))
	songPath := write(t, dir, "song.json", song)
	chapter6, err := OSHBChapterText(songPath, 22, 6)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter6) != 12 {
		t.Fatalf("wrong Song 6 control count: got %d, want 12", len(chapter6))
	}
	if _, ok := chapter6[13]; ok {
		t.Fatal("Song 6:13 control belongs to OSHB 7:1")
	}
	chapter7, err := OSHBChapterText(songPath, 22, 7)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter7) != 14 || chapter7[1] != "chapter-6-verse-13" ||
		chapter7[2] != "chapter-7-verse-1" || chapter7[14] != "chapter-7-verse-13" {
		t.Fatalf("wrong Song 7 mapping: len=%d 1=%q 2=%q 14=%q",
			len(chapter7), chapter7[1], chapter7[2], chapter7[14])
	}

	controls, err := loadControls(Request{
		BookNr: 22, Chapter: 7,
		WebPath: songPath, KJVPath: songPath, LivrePath: songPath,
	})
	if err != nil {
		t.Fatal(err)
	}
	for verse, want := range map[int]string{
		1: "chapter-6-verse-13", 2: "chapter-7-verse-1", 14: "chapter-7-verse-13",
	} {
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Song 7:%d: got %+v, want all controls %q", verse, got, want)
		}
	}
}

func TestOSHBChapterTextMapsIsaiahVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":23,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(8, 1, 22), chapter(9, 1, 21), chapter(63, 1, 19), chapter(64, 1, 12))
	path := write(t, dir, "isaiah.json", control)

	chapter8, err := OSHBChapterText(path, 23, 8)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter8) != 23 || chapter8[22] != "chapter-8-verse-22" || chapter8[23] != "chapter-9-verse-1" {
		t.Fatalf("wrong Isaiah 8 mapping: len=%d 22=%q 23=%q", len(chapter8), chapter8[22], chapter8[23])
	}

	chapter9, err := OSHBChapterText(path, 23, 9)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter9) != 20 || chapter9[1] != "chapter-9-verse-2" || chapter9[20] != "chapter-9-verse-21" {
		t.Fatalf("wrong Isaiah 9 mapping: len=%d 1=%q 20=%q", len(chapter9), chapter9[1], chapter9[20])
	}

	chapter63, err := OSHBChapterText(path, 23, 63)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter63) != 18 || chapter63[18] != "chapter-63-verse-18" {
		t.Fatalf("wrong Isaiah 63 mapping: len=%d 18=%q", len(chapter63), chapter63[18])
	}
	if _, ok := chapter63[19]; ok {
		t.Fatal("Isaiah 63:19 crosses a control-verse boundary and must have no mixed control")
	}

	chapter64, err := OSHBChapterText(path, 23, 64)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter64) != 11 || chapter64[1] != "chapter-64-verse-2" || chapter64[11] != "chapter-64-verse-12" {
		t.Fatalf("wrong Isaiah 64 mapping: len=%d 1=%q 11=%q", len(chapter64), chapter64[1], chapter64[11])
	}

	controls, err := loadControls(Request{
		BookNr: 23, Chapter: 64,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for verse, want := range map[int]string{
		1: "chapter-64-verse-2", 11: "chapter-64-verse-12",
	} {
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Isaiah 64:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	controls63, err := loadControls(Request{
		BookNr: 23, Chapter: 63,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	if got := controls63.forVerse(19); got != nil {
		t.Fatalf("unexpected mixed control for Isaiah 63:19: %+v", got)
	}

	missing := fmt.Sprintf(`{"books":[{"nr":23,"chapters":[%s]}]}`, chapter(64, 1, 11))
	missingPath := write(t, dir, "isaiah-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 23, 64); err == nil {
		t.Fatal("want error when mapped Isaiah 64:12 control is missing")
	}
}

func TestOSHBChapterTextMapsJeremiahVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":24,"chapters":[%s,%s]}]}`,
		chapter(8, 1, 22), chapter(9, 1, 26))
	path := write(t, dir, "jeremiah.json", control)

	chapter8, err := OSHBChapterText(path, 24, 8)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter8) != 23 || chapter8[22] != "chapter-8-verse-22" || chapter8[23] != "chapter-9-verse-1" {
		t.Fatalf("wrong Jeremiah 8 mapping: len=%d 22=%q 23=%q", len(chapter8), chapter8[22], chapter8[23])
	}

	chapter9, err := OSHBChapterText(path, 24, 9)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter9) != 25 || chapter9[1] != "chapter-9-verse-2" || chapter9[25] != "chapter-9-verse-26" {
		t.Fatalf("wrong Jeremiah 9 mapping: len=%d 1=%q 25=%q", len(chapter9), chapter9[1], chapter9[25])
	}

	controls, err := loadControls(Request{
		BookNr: 24, Chapter: 8,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for verse, want := range map[int]string{
		22: "chapter-8-verse-22", 23: "chapter-9-verse-1",
	} {
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Jeremiah 8:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":24,"chapters":[%s]}]}`, chapter(9, 1, 25))
	missingPath := write(t, dir, "jeremiah-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 24, 9); err == nil {
		t.Fatal("want error when mapped Jeremiah 9:26 control is missing")
	}
}

func TestOSHBChapterTextMapsEzekielVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":26,"chapters":[%s,%s]}]}`,
		chapter(20, 1, 49), chapter(21, 1, 32))
	path := write(t, dir, "ezekiel.json", control)

	chapter20, err := OSHBChapterText(path, 26, 20)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter20) != 44 {
		t.Fatalf("wrong Ezekiel 20 control count: got %d, want 44", len(chapter20))
	}
	for sourceVerse := 1; sourceVerse <= 44; sourceVerse++ {
		want := fmt.Sprintf("chapter-20-verse-%d", sourceVerse)
		if chapter20[sourceVerse] != want {
			t.Errorf("Ezekiel 20:%d: got %q, want %q", sourceVerse, chapter20[sourceVerse], want)
		}
	}
	if _, ok := chapter20[45]; ok {
		t.Fatal("Ezekiel 20:45 control belongs to OSHB 21:1")
	}

	chapter21, err := OSHBChapterText(path, 26, 21)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter21) != 37 {
		t.Fatalf("wrong Ezekiel 21 control count: got %d, want 37", len(chapter21))
	}
	for sourceVerse := 1; sourceVerse <= 37; sourceVerse++ {
		controlChapter, controlVerse := 21, sourceVerse-5
		if sourceVerse <= 5 {
			controlChapter, controlVerse = 20, sourceVerse+44
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if chapter21[sourceVerse] != want {
			t.Errorf("Ezekiel 21:%d: got %q, want %q", sourceVerse, chapter21[sourceVerse], want)
		}
	}

	controls, err := loadControls(Request{
		BookNr: 26, Chapter: 21,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for verse, want := range map[int]string{
		1: "chapter-20-verse-45", 5: "chapter-20-verse-49",
		6: "chapter-21-verse-1", 37: "chapter-21-verse-32",
	} {
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Ezekiel 21:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":26,"chapters":[%s,%s]}]}`,
		chapter(20, 1, 49), chapter(21, 1, 31))
	missingPath := write(t, dir, "ezekiel-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 26, 21); err == nil {
		t.Fatal("want error when mapped Ezekiel 21:32 control is missing")
	}
}

func TestOSHBChapterTextMapsDanielVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, from, to int) string {
		var verses strings.Builder
		for i := from; i <= to; i++ {
			if i > from {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	control := fmt.Sprintf(`{"books":[{"nr":27,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(3, 1, 30), chapter(4, 1, 37), chapter(5, 1, 31), chapter(6, 1, 28))
	path := write(t, dir, "daniel.json", control)

	chapter3, err := OSHBChapterText(path, 27, 3)
	if err != nil {
		t.Fatal(err)
	}
	for sourceVerse := 1; sourceVerse <= 33; sourceVerse++ {
		controlChapter, controlVerse := 3, sourceVerse
		if sourceVerse >= 31 {
			controlChapter, controlVerse = 4, sourceVerse-30
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if chapter3[sourceVerse] != want {
			t.Errorf("Daniel 3:%d: got %q, want %q", sourceVerse, chapter3[sourceVerse], want)
		}
	}

	chapter4, err := OSHBChapterText(path, 27, 4)
	if err != nil {
		t.Fatal(err)
	}
	for sourceVerse := 1; sourceVerse <= 34; sourceVerse++ {
		want := fmt.Sprintf("chapter-4-verse-%d", sourceVerse+3)
		if chapter4[sourceVerse] != want {
			t.Errorf("Daniel 4:%d: got %q, want %q", sourceVerse, chapter4[sourceVerse], want)
		}
	}

	chapter5, err := OSHBChapterText(path, 27, 5)
	if err != nil {
		t.Fatal(err)
	}
	if len(chapter5) != 30 || chapter5[30] != "chapter-5-verse-30" {
		t.Fatalf("wrong Daniel 5 mapping: len=%d 30=%q", len(chapter5), chapter5[30])
	}
	if _, ok := chapter5[31]; ok {
		t.Fatal("Daniel 5:31 control belongs to OSHB 6:1")
	}

	chapter6, err := OSHBChapterText(path, 27, 6)
	if err != nil {
		t.Fatal(err)
	}
	for sourceVerse := 1; sourceVerse <= 29; sourceVerse++ {
		controlChapter, controlVerse := 6, sourceVerse-1
		if sourceVerse == 1 {
			controlChapter, controlVerse = 5, 31
		}
		want := fmt.Sprintf("chapter-%d-verse-%d", controlChapter, controlVerse)
		if chapter6[sourceVerse] != want {
			t.Errorf("Daniel 6:%d: got %q, want %q", sourceVerse, chapter6[sourceVerse], want)
		}
	}

	controls, err := loadControls(Request{
		BookNr: 27, Chapter: 6,
		WebPath: path, KJVPath: path, LivrePath: path,
	})
	if err != nil {
		t.Fatal(err)
	}
	for verse, want := range map[int]string{
		1: "chapter-5-verse-31", 2: "chapter-6-verse-1", 29: "chapter-6-verse-28",
	} {
		got := controls.forVerse(verse)
		if got == nil || got.Web != want || got.KJV != want || got.Livre != want {
			t.Errorf("Daniel 6:%d: got %+v, want all controls %q", verse, got, want)
		}
	}

	missing := fmt.Sprintf(`{"books":[{"nr":27,"chapters":[%s,%s]}]}`,
		chapter(5, 1, 31), chapter(6, 1, 27))
	missingPath := write(t, dir, "daniel-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 27, 6); err == nil {
		t.Fatal("want error when mapped Daniel 6:28 control is missing")
	}
}

func TestOSHBChapterTextMapsMinorProphetsVersification(t *testing.T) {
	dir := t.TempDir()
	chapter := func(number, count int) string {
		var verses strings.Builder
		for i := 1; i <= count; i++ {
			if i > 1 {
				verses.WriteByte(',')
			}
			fmt.Fprintf(&verses, `{"verse":%d,"text":"chapter-%d-verse-%d"}`, i, number, i)
		}
		return fmt.Sprintf(`{"chapter":%d,"verses":[%s]}`, number, verses.String())
	}
	type bookCase struct {
		name          string
		bookNr        int
		controlCounts []int
		spans         map[int][]verseSpan
	}
	cases := []bookCase{
		{
			name: "hosea", bookNr: 28,
			controlCounts: []int{11, 23, 5, 19, 15, 11, 16, 14, 17, 15, 12, 14, 16, 9},
			spans: map[int][]verseSpan{
				1:  {{1, 9, 1, 1}},
				2:  {{1, 2, 1, 10}, {3, 25, 2, 1}},
				11: {{1, 11, 11, 1}},
				12: {{1, 1, 11, 12}, {2, 15, 12, 1}},
				13: {{1, 15, 13, 1}},
				14: {{1, 1, 13, 16}, {2, 10, 14, 1}},
			},
		},
		{
			name: "joel", bookNr: 29,
			controlCounts: []int{20, 32, 21},
			spans: map[int][]verseSpan{
				2: {{1, 27, 2, 1}},
				3: {{1, 5, 2, 28}},
				4: {{1, 21, 3, 1}},
			},
		},
		{
			name: "jonah", bookNr: 32,
			controlCounts: []int{17, 10, 10, 11},
			spans: map[int][]verseSpan{
				1: {{1, 16, 1, 1}},
				2: {{1, 1, 1, 17}, {2, 11, 2, 1}},
			},
		},
		{
			name: "micah", bookNr: 33,
			controlCounts: []int{16, 13, 12, 13, 15, 16, 20},
			spans: map[int][]verseSpan{
				4: {{1, 13, 4, 1}, {14, 14, 5, 1}},
				5: {{1, 14, 5, 2}},
			},
		},
		{
			name: "nahum", bookNr: 34,
			controlCounts: []int{15, 13, 19},
			spans: map[int][]verseSpan{
				1: {{1, 14, 1, 1}},
				2: {{1, 1, 1, 15}, {2, 14, 2, 1}},
			},
		},
		{
			name: "zechariah", bookNr: 38,
			controlCounts: []int{21, 13, 10, 14, 11, 15, 14, 23, 17, 12, 17, 14, 9, 21},
			spans: map[int][]verseSpan{
				1: {{1, 17, 1, 1}},
				2: {{1, 4, 1, 18}, {5, 17, 2, 1}},
			},
		},
		{
			name: "malachi", bookNr: 39,
			controlCounts: []int{14, 17, 18, 6},
			spans: map[int][]verseSpan{
				3: {{1, 18, 3, 1}, {19, 24, 4, 1}},
			},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var chapters strings.Builder
			for i, count := range tc.controlCounts {
				if i > 0 {
					chapters.WriteByte(',')
				}
				chapters.WriteString(chapter(i+1, count))
			}
			control := fmt.Sprintf(`{"books":[{"nr":%d,"chapters":[%s]}]}`, tc.bookNr, chapters.String())
			path := write(t, dir, tc.name+".json", control)

			for sourceChapter, spans := range tc.spans {
				got, err := OSHBChapterText(path, tc.bookNr, sourceChapter)
				if err != nil {
					t.Fatal(err)
				}
				expected := make(map[int]string)
				for _, span := range spans {
					for sourceVerse := span.sourceFrom; sourceVerse <= span.sourceTo; sourceVerse++ {
						controlVerse := span.controlFrom + sourceVerse - span.sourceFrom
						expected[sourceVerse] = fmt.Sprintf("chapter-%d-verse-%d", span.controlChapter, controlVerse)
					}
				}
				if len(got) != len(expected) {
					t.Fatalf("chapter %d: got %d controls, want %d", sourceChapter, len(got), len(expected))
				}
				for verse, want := range expected {
					if got[verse] != want {
						t.Errorf("chapter %d verse %d: got %q, want %q", sourceChapter, verse, got[verse], want)
					}
				}

				controls, err := loadControls(Request{
					BookNr: tc.bookNr, Chapter: sourceChapter,
					WebPath: path, KJVPath: path, LivrePath: path,
				})
				if err != nil {
					t.Fatal(err)
				}
				for verse, want := range expected {
					entry := controls.forVerse(verse)
					if entry == nil || entry.Web != want || entry.KJV != want || entry.Livre != want {
						t.Errorf("chapter %d verse %d: got %+v, want all controls %q", sourceChapter, verse, entry, want)
					}
				}
			}
		})
	}

	missing := fmt.Sprintf(`{"books":[{"nr":39,"chapters":[%s,%s,%s,%s]}]}`,
		chapter(1, 14), chapter(2, 17), chapter(3, 18), chapter(4, 5))
	missingPath := write(t, dir, "malachi-missing.json", missing)
	if _, err := OSHBChapterText(missingPath, 39, 3); err == nil {
		t.Fatal("want error when mapped Malachi 4:6 control is missing")
	}
}
