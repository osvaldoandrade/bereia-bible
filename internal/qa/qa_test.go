package qa

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCompare(t *testing.T) {
	tests := []struct {
		name      string
		bv, ctrl  string
		wantAlert bool
	}{
		{
			"identical long text alerts",
			"No princípio criou Deus os céus e a terra e tudo",
			"No princípio criou Deus os céus e a terra e tudo",
			true,
		},
		{
			"disjoint text does not alert",
			"A palavra estava com Deus desde o começo absoluto",
			"Outro conteúdo totalmente diferente sem relação nenhuma aqui",
			false,
		},
		{
			"short natural coincidence does not alert",
			"E disse Deus que a luz era boa naquele dia",
			"E disse Deus outra coisa sobre as águas do mar",
			false,
		},
		{
			"empty control does not alert",
			"Texto qualquer da BV", "", false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			r := Compare("Gen.1.1", tt.bv, tt.ctrl)
			if r.Alert != tt.wantAlert {
				t.Errorf("alert = %v (3g=%.2f lcs=%d), want %v", r.Alert, r.Overlap3, r.LCS, tt.wantAlert)
			}
		})
	}
}

func TestCompareDir(t *testing.T) {
	dir := t.TempDir()
	rec := `{"referencia":{"osis":"Gen.1.1","capitulo":1,"versiculo":1},"texto_bv":"No princípio Deus criou os céus e a terra."}`
	if err := os.WriteFile(filepath.Join(dir, "Gen.1.1.json"), []byte(rec), 0o644); err != nil {
		t.Fatal(err)
	}
	control := map[int]string{1: "No princípio criou Deus os céus e a terra."}
	rs, err := CompareDir(dir, control)
	if err != nil {
		t.Fatal(err)
	}
	if len(rs) != 1 || rs[0].OSIS != "Gen.1.1" {
		t.Fatalf("unexpected results: %+v", rs)
	}
	if rs[0].Overlap3 == 0 {
		t.Error("similar sentences must have nonzero trigram overlap")
	}
}

func TestCompareDirErrors(t *testing.T) {
	if _, err := CompareDir(t.TempDir(), nil); err == nil {
		t.Error("want error for empty dir")
	}
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "bad.json"), []byte("{"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := CompareDir(dir, nil); err == nil {
		t.Error("want error for malformed record")
	}
}
