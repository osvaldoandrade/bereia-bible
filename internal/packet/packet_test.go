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
