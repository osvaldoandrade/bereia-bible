package nestle1904

import (
	"os"
	"strings"
	"testing"
)

const fixture = "\ufeffBCV\ttext\tfunc_morph\tform_morph\tstrongs\tlemma\tnormalized\n" +
	"Matt 1:1\t[Βίβλος,\tN-NSF\tN-NSF\t976\tβίβλος\tΒίβλος\n" +
	"Matt 1:1\tγενέσεως]\tN-GSF\tN-GSF\t1078\tγένεσις\tγενέσεως\n" +
	"Matt 1:3\tδι’\tPREP\tPREP\t1223\tδιά\tδι’\n" +
	"Matt 1:3\tαὐτοῦ.\tP-GSM\tP-GSM\t846\tαὐτός\tαὐτοῦ\n" +
	"Mark 16:20\tσημείων.]]\tN-GPN\tN-GPN\t4592\tσημεῖον\tσημείων\n" +
	"Mark 16:99\t[[Πάντα\tA-APN\tA-APN\t3956\tπᾶς\tΠάντα\n"

func TestParseVersesAllowsIntentionalInternalGap(t *testing.T) {
	verses, err := ParseVerses(strings.NewReader(fixture), "Matt", 1, 1, 3)
	if err != nil {
		t.Fatal(err)
	}
	if len(verses) != 2 || verses[0].Number != 1 || verses[1].Number != 3 {
		t.Fatalf("unexpected verses: %+v", verses)
	}
	if verses[0].Text != "[Βίβλος, γενέσεως]" {
		t.Fatalf("source text changed: %q", verses[0].Text)
	}
	if len(verses[0].Tokens) != 5 {
		t.Fatalf("want preserved prefix/words/suffixes, got %+v", verses[0].Tokens)
	}
	first := verses[0].Tokens[1].Word
	if first == nil || first.Surface != "Βίβλος" || first.Lemma != "βίβλος" || first.Morph != "N-NSF" {
		t.Fatalf("first word annotations: %+v", first)
	}
	if got := verses[1].Tokens[0].Word.Surface; got != "δι’" {
		t.Fatalf("elision apostrophe must remain lexical: %q", got)
	}
}

func TestParseVersesRejectsMissingEndpoint(t *testing.T) {
	_, err := ParseVerses(strings.NewReader(fixture), "Matt", 1, 1, 4)
	if err == nil || !strings.Contains(err.Error(), "Matt.1.4") {
		t.Fatalf("want missing endpoint error, got %v", err)
	}
}

func TestParseVersesRejectsBadHeaderAndRow(t *testing.T) {
	badHeader := strings.Replace(fixture, "func_morph", "morph", 1)
	if _, err := ParseVerses(strings.NewReader(badHeader), "Matt", 1, 1, 1); err == nil {
		t.Fatal("want header error")
	}
	badRow := "BCV\ttext\tfunc_morph\tform_morph\tstrongs\tlemma\tnormalized\nMatt-one\tλόγος\tN\tN\t3056\tλόγος\tλόγος\n"
	if _, err := ParseVerses(strings.NewReader(badRow), "Matt", 1, 1, 1); err == nil {
		t.Fatal("want BCV error")
	}
	badExtra := "BCV\ttext\tfunc_morph\tform_morph\tstrongs\tlemma\tnormalized\nMatt 1:1\tλόγος\tN-NSM\tN-NSM\t3056\tλόγος\tλόγος\tcorruption\n"
	if _, err := ParseVerses(strings.NewReader(badExtra), "Matt", 1, 1, 1); err == nil {
		t.Fatal("want trailing-column error")
	}
}

func TestParseCanonicalMarkExcludesPseudoVerse99(t *testing.T) {
	verses, err := ParseVerses(strings.NewReader(fixture), "Mark", 16, 20, 20)
	if err != nil {
		t.Fatal(err)
	}
	if len(verses) != 1 || verses[0].OSIS != "Mark.16.20" {
		t.Fatalf("pseudo-verse leaked: %+v", verses)
	}
}

func TestParseRealNestle1904(t *testing.T) {
	f, err := os.Open("../../sources/nestle1904/Nestle1904.csv")
	if err != nil {
		t.Skip("pinned source not present:", err)
	}
	defer f.Close()
	verses, err := ParseVerses(f, "Matt", 17, 1, 27)
	if err != nil {
		t.Fatal(err)
	}
	if len(verses) != 26 {
		t.Fatalf("Matthew 17 must expose 26 source verses, got %d", len(verses))
	}
	for _, verse := range verses {
		if verse.Number == 21 {
			t.Fatal("traditional verse 21 must remain absent from the pinned source")
		}
	}

	if _, err := f.Seek(0, 0); err != nil {
		t.Fatal(err)
	}
	ambiguous, err := ParseVerses(f, "Matt", 10, 28, 28)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, token := range ambiguous[0].Tokens {
		if token.Word != nil && token.Word.Surface == "φοβεῖσθε" && len(token.Word.MorphAlternatives) == 2 {
			found = token.Word.MorphAlternatives[0] == "V-PEM-2P" && token.Word.MorphAlternatives[1] == "V-PNM-2P"
		}
	}
	if !found {
		t.Fatal("Matthew 10:28 morphology alternatives were not preserved")
	}
}
