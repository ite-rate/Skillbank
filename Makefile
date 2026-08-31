# Skillbank Makefile — Go 静态二进制 + skill 分发包
#
#   make test    全量 Go 测试
#   make build   四平台交叉编译 → dist/skillbank-<os>-<arch>(真静态, 无 cgo)
#   make skill   校验 skill/ 分发包(二进制已移居 GitHub Releases, 走 scripts/install.sh)

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

# 校验 skill 分发包: SKILL.md + reference/ + config 模板(v2.1 起二进制不入库,
# 安装走 scripts/install.sh 拉 GitHub Releases)
skill:
	@test -f skill/SKILL.md || (echo "✗ 缺 skill/SKILL.md"; exit 1)
	@test -d skill/reference || (echo "✗ 缺 skill/reference/"; exit 1)
	@sh -n scripts/install.sh
	@echo "skill/ 分发包内容:"
	@find skill -type f | sort
	@echo "(二进制安装: scripts/install.sh 或 GitHub Releases 手动下载)"

clean:
	rm -rf $(DIST)