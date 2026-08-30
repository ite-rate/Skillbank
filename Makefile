# Skillbank Makefile — Go 静态二进制 + skill 分发包组装
#
#   make test    全量 Go 测试
#   make build   四平台交叉编译 → dist/skillbank-<os>-<arch>(真静态, 无 cgo)
#   make skill   组装 skill/ 分发包(拷 dist/ 二进制进 skill/bin/)

BINARY   := skillbank
VERSION  ?= 2.0.0
DIST     := dist
PLATFORMS := darwin/amd64 darwin/arm64 linux/amd64 linux/arm64
LDFLAGS  := -s -w

.PHONY: test build skill clean

test:
	go test ./...

build:
	@mkdir -p $(DIST)
	@for plat in $(PLATFORMS); do \
		os=$${plat%/*}; arch=$${plat#*/}; \
		echo "→ $(BINARY)-$$os-$$arch"; \
		CGO_ENABLED=0 GOOS=$$os GOARCH=$$arch \
		go build -trimpath -ldflags "$(LDFLAGS)" \
			-o $(DIST)/$(BINARY)-$$os-$$arch ./cmd/skillbank || exit 1; \
	done
	@ls -lh $(DIST)

# 组装 skill 分发包: SKILL.md + reference/ + config 模板 + 四平台二进制
skill: build
	@mkdir -p skill/bin
	@for plat in $(PLATFORMS); do \
		os=$${plat%/*}; arch=$${plat#*/}; \
		case $$os-$$arch in \
			darwin-arm64)  suffix=mac-arm64 ;; \
			darwin-amd64)  suffix=mac-amd64 ;; \
			linux-amd64)   suffix=linux-amd64 ;; \
			linux-arm64)   suffix=linux-arm64 ;; \
		esac; \
		cp $(DIST)/$(BINARY)-$$os-$$arch skill/bin/skillbank-$$suffix; \
	done
	@chmod +x skill/bin/skillbank-*
	@echo "skill/ 分发包已组装:"
	@find skill -type f | sort

clean:
	rm -rf $(DIST)