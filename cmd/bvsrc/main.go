// bvsrc extracts a pericope from a pinned original-language source into the
// pipeline input packet (composition root only; logic in internal/packet).
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"bereia.org/bible/internal/packet"
)

func main() {
	req := packet.Request{}
	var nestlePath string
	var out string
	flag.StringVar(&req.OSHBPath, "oshb", "", "path to OSHB OSIS XML")
	flag.StringVar(&nestlePath, "nestle1904", "", "path to Nestle 1904 morphology TSV/CSV")
	flag.StringVar(&req.OSISBook, "osis", "", "OSIS book id, e.g. Gen (required)")
	flag.IntVar(&req.BookNr, "booknr", 1, "book number in getBible controls")
	flag.IntVar(&req.Chapter, "chapter", 0, "chapter (required)")
	flag.IntVar(&req.From, "from", 0, "first verse (required)")
	flag.IntVar(&req.To, "to", 0, "last verse (required)")
	flag.StringVar(&req.Pericope, "pericope", "", "pericope aggregate id, e.g. Gen.1.1-5 (required)")
	flag.StringVar(&req.WebPath, "web", "", "WEB control (getBible JSON)")
	flag.StringVar(&req.KJVPath, "kjv", "", "KJV control (getBible JSON)")
	flag.StringVar(&req.LivrePath, "livre", "", "Bíblia Livre control (getBible JSON)")
	flag.StringVar(&out, "out", "", "output file (default stdout)")
	flag.Parse()
	if (req.OSHBPath == "") == (nestlePath == "") || req.OSISBook == "" || req.Chapter < 1 || req.From < 1 || req.To < 1 || req.Pericope == "" {
		flag.Usage()
		os.Exit(2)
	}
	var p *packet.Packet
	var err error
	if nestlePath != "" {
		p, err = packet.BuildNestle(packet.NestleRequest{
			NestlePath: nestlePath, OSISBook: req.OSISBook, BookNr: req.BookNr,
			Chapter: req.Chapter, From: req.From, To: req.To, Pericope: req.Pericope,
			WebPath: req.WebPath, KJVPath: req.KJVPath, LivrePath: req.LivrePath,
		})
	} else {
		p, err = packet.Build(req)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "bvsrc:", err)
		os.Exit(1)
	}
	enc, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, "bvsrc:", err)
		os.Exit(1)
	}
	enc = append(enc, '\n')
	if out == "" {
		os.Stdout.Write(enc)
		return
	}
	if err := os.WriteFile(out, enc, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, "bvsrc:", err)
		os.Exit(1)
	}
}
