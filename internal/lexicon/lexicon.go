// Package lexicon loads and enforces the invariants of the BV terminology
// lexicon (lexicon/lexicon.json). The invariant list I-1..I-10 is normative
// in lexicon/lexicon.schema.json; the structural half is checked by
// schemavalidate, the relational half here.
package lexicon

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
)

var osisRef = regexp.MustCompile(`^[1-4]?[A-Z][a-z]+\.[0-9]+\.[0-9]+$`)

type Policy struct {
	ID            string `json:"id"`
	Rule          string `json:"regra"`
	Justification string `json:"justificativa"`
	RulingRef     string `json:"diretriz_ref"`
	File          string `json:"arquivo,omitempty"`
	PolicyVersion string `json:"versao_politica,omitempty"`
}

type Entry struct {
	Lemma            string   `json:"lemma"`
	Original         string   `json:"original"`
	Translit         string   `json:"translit"`
	Gloss            string   `json:"glosa_bv"`
	Domain           string   `json:"dominio"`
	Justification    string   `json:"justificativa"`
	Status           string   `json:"status"`
	Owner            string   `json:"owner"`
	FirstOccurrences []string `json:"primeiras_ocorrencias"`
	PolicyRef        string   `json:"politica_ref,omitempty"`
	RulingRef        string   `json:"diretriz_ref,omitempty"`
	SupersededBy     string   `json:"superseded_por,omitempty"`
	Note             string   `json:"observacao,omitempty"`
}

type Lexicon struct {
	SchemaVersion string   `json:"schema_version"`
	Version       string   `json:"versao"`
	Owner         string   `json:"owner"`
	Policies      []Policy `json:"politicas"`
	Entries       []Entry  `json:"entradas"`
}

// Load reads and decodes the lexicon file without validating it.
func Load(path string) (*Lexicon, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var l Lexicon
	if err := json.Unmarshal(raw, &l); err != nil {
		return nil, fmt.Errorf("lexicon %s: %w", path, err)
	}
	return &l, nil
}

// Validate enforces the relational invariants; one error per violation.
func (l *Lexicon) Validate() []error {
	var errs []error
	policies := make(map[string]bool, len(l.Policies))
	for _, p := range l.Policies {
		policies[p.ID] = true
	}
	glossByKey := make(map[string]string, len(l.Entries))
	entryKeys := make(map[string]bool, len(l.Entries))
	for _, e := range l.Entries {
		key := e.Lemma + "|" + e.Domain
		entryKeys[key] = true
		if e.Status != "SUPERSEDED" {
			if _, dup := glossByKey[key]; dup {
				errs = append(errs, fmt.Errorf("I-1: duplicate active entry for %s", key))
			}
			glossByKey[key] = e.Gloss
		}
	}
	for _, e := range l.Entries {
		id := e.Lemma + "/" + e.Domain
		if e.Status == "SUPERSEDED" && e.SupersededBy == "" {
			errs = append(errs, fmt.Errorf("I-5: %s SUPERSEDED without superseded_por", id))
		}
		if e.SupersededBy != "" && !entryKeys[e.SupersededBy+"|"+e.Domain] {
			errs = append(errs, fmt.Errorf("I-5: %s superseded_por %q has no entry in same domain", id, e.SupersededBy))
		}
		if e.Domain == "nome divino" && (e.PolicyRef == "" || e.RulingRef == "") {
			errs = append(errs, fmt.Errorf("I-6: %s divine-name entry requires politica_ref and diretriz_ref", id))
		}
		if e.PolicyRef != "" && !policies[e.PolicyRef] {
			errs = append(errs, fmt.Errorf("I-6: %s politica_ref %q not declared", id, e.PolicyRef))
		}
		for _, occ := range e.FirstOccurrences {
			if !osisRef.MatchString(occ) {
				errs = append(errs, fmt.Errorf("I-7: %s occurrence %q is not an OSIS ref", id, occ))
			}
		}
	}
	return errs
}
