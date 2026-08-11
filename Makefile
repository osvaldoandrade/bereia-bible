GO ?= go

.PHONY: build test lint verify packets packets-blind clean

build:
	$(GO) build -o bin/ ./...

test:
	$(GO) test ./... -cover

lint:
	@test -z "$$(gofmt -l .)" || { gofmt -l .; echo "gofmt: files above are unformatted"; exit 1; }
	$(GO) vet ./...
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run || echo "WARNING: golangci-lint is installed but FAILED (known toolchain mismatch, see F-0012 in decisions/DECISOES.md); gofmt+vet remain the hard gate"; \
	else \
		echo "golangci-lint not installed; skipped (config: .golangci.yml)"; \
	fi

verify: lint build test
	@test ! -f go.sum || { echo "zero-dep policy violated: go.sum exists"; exit 1; }
	./bin/bvcheck -records translation/01-gn/001 -lexicon lexicon/lexicon.json
	cd sources && shasum -a 256 -c manifest.sha256

packets: build
	./bin/bvsrc -oshb sources/oshb/Gen.xml -osis Gen -chapter 1 -from 1 -to 5 \
	  -pericope Gen.1.1-5 \
	  -web sources/web/web.getbible.json -kjv sources/kjv/kjv.getbible.json \
	  -livre sources/pt-pd/livre.getbible.json -out pipeline/packets/gen-001-001-005.json

packets-blind: build
	./bin/bvsrc -oshb sources/oshb/Gen.xml -osis Gen -chapter 1 -from 1 -to 5 \
	  -pericope Gen.1.1-5 -out pipeline/packets/gen-001-001-005.blind.json

clean:
	rm -rf bin
