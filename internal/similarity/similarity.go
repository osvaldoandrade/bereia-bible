// Package similarity implements the mechanical contamination checks of the
// QA context: word n-gram overlap and longest common contiguous word run
// between a BV text and a stored public-domain control (PIPELINE.md §QA).
package similarity

import (
	"strings"
	"unicode"
)

// Normalize lowercases the text, strips punctuation (keeping letters with
// diacritics and digits) and returns the word sequence.
func Normalize(s string) []string {
	clean := strings.Map(func(r rune) rune {
		switch {
		case unicode.IsLetter(r), unicode.IsDigit(r):
			return unicode.ToLower(r)
		default:
			return ' '
		}
	}, s)
	return strings.Fields(clean)
}

// NGramOverlap returns the fraction of a's n-grams that also occur in b.
// It is asymmetric on purpose: a is the BV text under suspicion, b the
// control. Returns 0 when a has no n-grams.
func NGramOverlap(a, b []string, n int) float64 {
	if n < 1 || len(a) < n {
		return 0
	}
	set := make(map[string]bool)
	for i := 0; i+n <= len(b); i++ {
		set[strings.Join(b[i:i+n], " ")] = true
	}
	total := len(a) - n + 1
	hits := 0
	for i := 0; i+n <= len(a); i++ {
		if set[strings.Join(a[i:i+n], " ")] {
			hits++
		}
	}
	return float64(hits) / float64(total)
}

// LongestCommonRun returns the length in words of the longest contiguous
// word sequence shared by a and b.
func LongestCommonRun(a, b []string) int {
	if len(a) == 0 || len(b) == 0 {
		return 0
	}
	prev := make([]int, len(b)+1)
	cur := make([]int, len(b)+1)
	best := 0
	for i := 1; i <= len(a); i++ {
		for j := 1; j <= len(b); j++ {
			if a[i-1] == b[j-1] {
				cur[j] = prev[j-1] + 1
				if cur[j] > best {
					best = cur[j]
				}
			} else {
				cur[j] = 0
			}
		}
		prev, cur = cur, prev
	}
	return best
}
