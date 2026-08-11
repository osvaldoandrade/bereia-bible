package similarity

import (
	"reflect"
	"testing"
)

func TestNormalize(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want []string
	}{
		{"lowercase and punctuation", `E disse Deus: "Haja luz".`, []string{"e", "disse", "deus", "haja", "luz"}},
		{"diacritics preserved", "princípio criação", []string{"princípio", "criação"}},
		{"digits kept", "Gênesis 1", []string{"gênesis", "1"}},
		{"empty", "  ...  ", []string{}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Normalize(tt.in)
			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("Normalize(%q) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}
}

func TestNGramOverlap(t *testing.T) {
	a := []string{"no", "princípio", "criou", "deus", "os", "céus"}
	tests := []struct {
		name string
		a, b []string
		n    int
		want float64
	}{
		{"identical", a, a, 3, 1.0},
		{"disjoint", a, []string{"x", "y", "z", "w"}, 3, 0.0},
		{"partial", []string{"a", "b", "c", "d"}, []string{"a", "b", "c", "x"}, 3, 0.5},
		{"n larger than a", []string{"a", "b"}, a, 3, 0.0},
		{"n zero", a, a, 0, 0.0},
		{"empty control", a, nil, 3, 0.0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := NGramOverlap(tt.a, tt.b, tt.n); got != tt.want {
				t.Errorf("NGramOverlap = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestLongestCommonRun(t *testing.T) {
	tests := []struct {
		name string
		a, b []string
		want int
	}{
		{"identical", []string{"a", "b", "c"}, []string{"a", "b", "c"}, 3},
		{"middle run", []string{"x", "a", "b", "y"}, []string{"z", "a", "b", "w"}, 2},
		{"no overlap", []string{"a"}, []string{"b"}, 0},
		{"empty", nil, []string{"a"}, 0},
		{"repeated words", []string{"a", "a", "a"}, []string{"a", "a"}, 2},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := LongestCommonRun(tt.a, tt.b); got != tt.want {
				t.Errorf("LongestCommonRun = %d, want %d", got, tt.want)
			}
		})
	}
}

func FuzzNormalize(f *testing.F) {
	f.Add("E disse Deus: “Haja luz”. וַיֹּאמֶר")
	f.Fuzz(func(t *testing.T, s string) {
		for _, w := range Normalize(s) {
			if w == "" {
				t.Error("Normalize produced empty word")
			}
		}
	})
}

func FuzzLongestCommonRun(f *testing.F) {
	f.Add("no princípio criou", "no princípio deus criou")
	f.Fuzz(func(t *testing.T, x, y string) {
		a, b := Normalize(x), Normalize(y)
		got := LongestCommonRun(a, b)
		if got < 0 || got > len(a) || got > len(b) {
			t.Errorf("LongestCommonRun out of bounds: %d for %d/%d", got, len(a), len(b))
		}
	})
}
