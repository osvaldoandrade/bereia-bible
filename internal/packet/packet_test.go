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
