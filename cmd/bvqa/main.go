// bvqa runs the mechanical contamination check: BV verse records vs. the
// stored Portuguese public-domain control (composition root only).
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"bereia.org/bible/internal/packet"
	"bereia.org/bible/internal/qa"
)

func main() {
	var records, livre, out string
	var bookNr, chapter int
	flag.StringVar(&records, "records", "", "directory with verse-record *.json (required)")
	flag.StringVar(&livre, "livre", "", "Bíblia Livre control (getBible JSON, required)")
	flag.IntVar(&bookNr, "booknr", 1, "book number in the control")
	flag.IntVar(&chapter, "chapter", 1, "chapter in the control")
	flag.StringVar(&out, "out", "", "write JSON report to file (default: stdout table)")
	flag.Parse()
	if records == "" || livre == "" {
		flag.Usage()
		os.Exit(2)
	}
	control, err := packet.OSHBChapterText(livre, bookNr, chapter)
	if err != nil {
		fmt.Fprintln(os.Stderr, "bvqa:", err)
		os.Exit(1)
	}
	results, err := qa.CompareDir(records, control)
	if err != nil {
		fmt.Fprintln(os.Stderr, "bvqa:", err)
		os.Exit(1)
	}
	if out != "" {
		enc, _ := json.MarshalIndent(results, "", "  ")
		if err := os.WriteFile(out, append(enc, '\n'), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, "bvqa:", err)
			os.Exit(1)
		}
	}
	alerts := 0
	for _, r := range results {
		mark := " "
		if r.Alert {
			mark = "!"
			alerts++
		}
		fmt.Printf("%s %-10s 3g=%.2f 4g=%.2f 5g=%.2f lcs=%d\n",
			mark, r.OSIS, r.Overlap3, r.Overlap4, r.Overlap5, r.LCS)
	}
	fmt.Printf("verses=%d alerts=%d (alert => source-first re-evaluation, PIPELINE.md §QA)\n",
		len(results), alerts)
}
