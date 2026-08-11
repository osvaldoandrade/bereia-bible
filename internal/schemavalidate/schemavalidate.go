// Package schemavalidate is a deliberately small JSON Schema validator for
// the repo's own contracts (api/*.schema.json, lexicon/lexicon.schema.json).
// Zero-dependency policy (ADR-0001 §10) rules out third-party validators.
//
// Supported keywords: type (incl. union arrays), required, properties,
// additionalProperties=false, items (single schema), enum, const, pattern,
// minLength, minItems, minimum, maximum. NOT supported: $ref, oneOf/anyOf,
// allOf, propertyNames, format. The repo schemas must stay inside this
// subset; extending a schema beyond it requires extending this package in
// the same change.
package schemavalidate

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"reflect"
	"regexp"
)

// ValidateFile validates the JSON document at docPath against the JSON
// Schema at schemaPath and returns one error per violation.
func ValidateFile(schemaPath, docPath string) ([]error, error) {
	schema, err := readJSON(schemaPath)
	if err != nil {
		return nil, err
	}
	doc, err := readJSON(docPath)
	if err != nil {
		return nil, err
	}
	s, ok := schema.(map[string]any)
	if !ok {
		return nil, fmt.Errorf("schema %s: root is not an object", schemaPath)
	}
	return Validate(s, doc, "$"), nil
}

// Validate walks doc against schema, collecting violations under path.
func Validate(schema map[string]any, doc any, path string) []error {
	var errs []error
	errs = append(errs, checkType(schema, doc, path)...)
	errs = append(errs, checkEnumConst(schema, doc, path)...)
	errs = append(errs, checkString(schema, doc, path)...)
	errs = append(errs, checkNumber(schema, doc, path)...)
	errs = append(errs, checkObject(schema, doc, path)...)
	errs = append(errs, checkArray(schema, doc, path)...)
	return errs
}

func checkType(schema map[string]any, doc any, path string) []error {
	t, ok := schema["type"]
	if !ok {
		return nil
	}
	var allowed []string
	switch v := t.(type) {
	case string:
		allowed = []string{v}
	case []any:
		for _, x := range v {
			if s, ok := x.(string); ok {
				allowed = append(allowed, s)
			}
		}
	}
	actual := typeName(doc)
	for _, a := range allowed {
		if a == actual || (a == "number" && actual == "integer") {
			return nil
		}
	}
	return []error{fmt.Errorf("%s: expected type %v, got %s", path, allowed, actual)}
}

func typeName(doc any) string {
	switch v := doc.(type) {
	case nil:
		return "null"
	case bool:
		return "boolean"
	case string:
		return "string"
	case float64:
		if v == math.Trunc(v) {
			return "integer"
		}
		return "number"
	case []any:
		return "array"
	case map[string]any:
		return "object"
	default:
		return "unknown"
	}
}

func checkEnumConst(schema map[string]any, doc any, path string) []error {
	var errs []error
	if enum, ok := schema["enum"].([]any); ok {
		found := false
		for _, e := range enum {
			if reflect.DeepEqual(e, doc) {
				found = true
				break
			}
		}
		if !found {
			errs = append(errs, fmt.Errorf("%s: value %v not in enum %v", path, doc, enum))
		}
	}
	if c, ok := schema["const"]; ok && !reflect.DeepEqual(c, doc) {
		errs = append(errs, fmt.Errorf("%s: value %v != const %v", path, doc, c))
	}
	return errs
}

func checkString(schema map[string]any, doc any, path string) []error {
	s, ok := doc.(string)
	if !ok {
		return nil
	}
	var errs []error
	if min, ok := num(schema["minLength"]); ok && float64(len([]rune(s))) < min {
		errs = append(errs, fmt.Errorf("%s: shorter than minLength %v", path, min))
	}
	if p, ok := schema["pattern"].(string); ok {
		re, err := regexp.Compile(p)
		if err != nil {
			errs = append(errs, fmt.Errorf("%s: bad pattern %q: %v", path, p, err))
		} else if !re.MatchString(s) {
			errs = append(errs, fmt.Errorf("%s: %q does not match pattern %q", path, s, p))
		}
	}
	return errs
}

func checkNumber(schema map[string]any, doc any, path string) []error {
	n, ok := doc.(float64)
	if !ok {
		return nil
	}
	var errs []error
	if min, ok := num(schema["minimum"]); ok && n < min {
		errs = append(errs, fmt.Errorf("%s: %v below minimum %v", path, n, min))
	}
	if max, ok := num(schema["maximum"]); ok && n > max {
		errs = append(errs, fmt.Errorf("%s: %v above maximum %v", path, n, max))
	}
	return errs
}

func checkObject(schema map[string]any, doc any, path string) []error {
	obj, ok := doc.(map[string]any)
	if !ok {
		return nil
	}
	var errs []error
	props, _ := schema["properties"].(map[string]any)
	if req, ok := schema["required"].([]any); ok {
		for _, r := range req {
			key, _ := r.(string)
			if _, present := obj[key]; !present {
				errs = append(errs, fmt.Errorf("%s: missing required property %q", path, key))
			}
		}
	}
	if ap, ok := schema["additionalProperties"].(bool); ok && !ap {
		for k := range obj {
			if _, declared := props[k]; !declared {
				errs = append(errs, fmt.Errorf("%s: additional property %q not allowed", path, k))
			}
		}
	}
	for k, v := range obj {
		sub, ok := props[k].(map[string]any)
		if !ok {
			continue
		}
		errs = append(errs, Validate(sub, v, path+"."+k)...)
	}
	return errs
}

func checkArray(schema map[string]any, doc any, path string) []error {
	arr, ok := doc.([]any)
	if !ok {
		return nil
	}
	var errs []error
	if min, ok := num(schema["minItems"]); ok && float64(len(arr)) < min {
		errs = append(errs, fmt.Errorf("%s: fewer than minItems %v", path, min))
	}
	if items, ok := schema["items"].(map[string]any); ok {
		for i, v := range arr {
			errs = append(errs, Validate(items, v, fmt.Sprintf("%s[%d]", path, i))...)
		}
	}
	return errs
}

func num(v any) (float64, bool) {
	f, ok := v.(float64)
	return f, ok
}

func readJSON(path string) (any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var doc any
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return doc, nil
}
