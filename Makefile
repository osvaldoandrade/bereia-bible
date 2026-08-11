GO ?= go

.PHONY: build test lint verify packets clean

build:
	$(GO) build -o bin/ ./...

test:
	$(GO) test ./... -cover

lint:
	gofmt -l . && $(GO) vet ./...
	@command -v golangci-lint >/dev/null 2>&1 && golangci-lint run || echo "golangci-lint not installed; skipped (config: .golangci.yml)"

verify: lint build test
	@test ! -f go.sum || (echo "zero-dep policy violated: go.sum exists" && exit 1)
	cd sources && shasum -a 256 -c manifest.sha256

packets: build
	./bin/bvsrc -oshb sources/oshb/Gen.xml -osis Gen -chapter 1 -from 1 -to 5 \
	  -pericope Gen.1.1-5 \
	  -web sources/web/web.getbible.json -kjv sources/kjv/kjv.getbible.json \
	  -livre sources/pt-pd/livre.getbible.json -out pipeline/packets/gen-001-001-005.json

clean:
	rm -rf bin
