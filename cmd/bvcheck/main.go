// bvcheck validates repo artifacts against their contracts: verse records
// and manifest against api/*.schema.json, lexicon against schema+invariants
// (composition root only).
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"bereia.org/bible/internal/lexicon"
	"bereia.org/bible/internal/schemavalidate"
)

func main() {
	var schema, doc, records, lex string
	flag.StringVar(&schema, "schema", "", "schema path (with -doc)")
	flag.StringVar(&doc, "doc", "", "document to validate against -schema")
	flag.StringVar(&records, "records", "", "directory of verse records to validate against api/verse-record.schema.json")
	flag.StringVar(&lex, "lexicon", "", "lexicon.json to validate (schema + invariants)")
	flag.Parse()
	fail := 0
	if schema != "" && doc != "" {
		fail += report(doc, validate(schema, doc))
	}
	if records != "" {
		paths, _ := filepath.Glob(filepath.Join(records, "*.json"))
		if len(paths) == 0 {
			fmt.Fprintln(os.Stderr, "bvcheck: no records in", records)
			os.Exit(2)
		}
		for _, p := range paths {
			fail += report(p, validate("api/verse-record.schema.json", p))
		}
	}
	if lex != "" {
		errs := validate("lexicon/lexicon.schema.json", lex)
		if l, err := lexicon.Load(lex); err != nil {
			errs = append(errs, err)
		} else {
			errs = append(errs, l.Validate()...)
		}
		fail += report(lex, errs)
	}
	if fail > 0 {
		os.Exit(1)
	}
}

func validate(schemaPath, docPath string) []error {
	errs, err := schemavalidate.ValidateFile(schemaPath, docPath)
	if err != nil {
		return []error{err}
	}
	return errs
}

func report(target string, errs []error) int {
	if len(errs) == 0 {
		fmt.Printf("OK   %s\n", target)
		return 0
	}
	fmt.Printf("FAIL %s\n", target)
	for _, e := range errs {
		fmt.Printf("     - %v\n", e)
	}
	return 1
}
