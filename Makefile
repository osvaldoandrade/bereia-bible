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

# Pericope parameters (defaults reproduce the pilot packet byte-for-byte)
CHAPTER ?= 1
FROM ?= 1
TO ?= 5
PERICOPE ?= Gen.$(CHAPTER).$(FROM)-$(TO)
CH_PAD := $(shell printf '%03d' $(CHAPTER))
FROM_PAD := $(shell printf '%03d' $(FROM))
TO_PAD := $(shell printf '%03d' $(TO))
PACKET_OUT ?= pipeline/packets/gen-$(CH_PAD)-$(FROM_PAD)-$(TO_PAD).json
BLIND_OUT ?= pipeline/packets/gen-$(CH_PAD)-$(FROM_PAD)-$(TO_PAD).blind.json

packets: build
	./bin/bvsrc -oshb sources/oshb/Gen.xml -osis Gen -chapter $(CHAPTER) -from $(FROM) -to $(TO) \
	  -pericope $(PERICOPE) \
	  -web sources/web/web.getbible.json -kjv sources/kjv/kjv.getbible.json \
	  -livre sources/pt-pd/livre.getbible.json -out $(PACKET_OUT)

packets-blind: build
	./bin/bvsrc -oshb sources/oshb/Gen.xml -osis Gen -chapter $(CHAPTER) -from $(FROM) -to $(TO) \
	  -pericope $(PERICOPE) -out $(BLIND_OUT)

clean:
	rm -rf bin
