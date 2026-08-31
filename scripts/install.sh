#!/bin/sh
# Skillbank installer — 从 GitHub Releases 下载静态二进制并校验后安装。
#
#   curl -fsSL https://raw.githubusercontent.com/ite-rate/Skillbank/main/scripts/install.sh | sh
#
# 只支持 macOS / Linux;Windows 请自行 go build(见 README)。
# 环境变量:
#   SKILLBANK_INSTALL_DIR  覆盖安装目录(默认 /usr/local/bin, 无权限则 $HOME/.local/bin)
#   SKILLBANK_NO_VERIFY=1  跳过 SHA256 校验(不推荐; 会打警告)
#   VERSION= vX.Y.Z        安装指定版本(默认 latest)
set -eu

REPO="ite-rate/Skillbank"
BIN_NAME="skillbank"

BASE="https://github.com/$REPO/releases"
if [ "${VERSION:-}" != "" ]; then
    BASE="$BASE/download/$VERSION"
else
    BASE="$BASE/latest/download"
fi

# --- 平台映射(uname → Go 命名) ---
OS=$(uname -s)
ARCH=$(uname -m)
case "$OS" in
    Darwin) os=darwin ;;
    Linux)  os=linux ;;
    *) echo "✗ 不支持的系统: $OS(只支持 macOS/Linux; Windows 请自行构建)" >&2; exit 1 ;;
esac
case "$ARCH" in
    arm64|aarch64) arch=arm64 ;;
    x86_64|amd64)  arch=amd64 ;;
    *) echo "✗ 不支持的架构: $ARCH" >&2; exit 1 ;;
esac
ASSET="skillbank-$os-$arch"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fetch() {
    # fetch <url> <out> — curl 优先, wget 兜底
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --retry 3 "$1" -o "$2"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$2" "$1"
    else
        echo "✗ 需要 curl 或 wget" >&2
        exit 1
    fi
}

echo "→ 下载 $BASE/$ASSET"
fetch "$BASE/$ASSET" "$TMP/$ASSET"
chmod +x "$TMP/$ASSET"

# --- SHA256 校验(发布链无校验和 = 产品级短板, 默认 fail closed) ---
if [ "${SKILLBANK_NO_VERIFY:-}" = "1" ]; then
    echo "⚠ SKILLBANK_NO_VERIFY=1: 跳过 SHA256 校验 —— 往 agent 目录写盘的工具, 建议别跳" >&2
else
    fetch "$BASE/SHA256SUMS" "$TMP/SHA256SUMS"
    # SHA256SUMS 行格式: <hash>  skillbank-<os>-<arch>; 在 TMP 里直接 -c 对得上文件名
    if command -v sha256sum >/dev/null 2>&1; then
        grep " $ASSET\$" "$TMP/SHA256SUMS" | (cd "$TMP" && sha256sum -c -)
    elif command -v shasum >/dev/null 2>&1; then
        expected=$(grep " $ASSET\$" "$TMP/SHA256SUMS" | cut -d' ' -f1)
        actual=$(shasum -a 256 "$TMP/$ASSET" | cut -d' ' -f1)
        [ "$actual" = "$expected" ] || {
            echo "✗ SHA256 不匹配: 期望 $expected, 实际 $actual" >&2
            exit 1
        }
        echo "SHA256 校验通过: $actual"
    else
        echo "✗ 找不到 sha256sum/shasum, 无法校验。设 SKILLBANK_NO_VERIFY=1 可跳(自担风险)" >&2
        exit 1
    fi
fi

# --- 安装目录 ---
PREFIX=""
if [ -n "${SKILLBANK_INSTALL_DIR:-}" ]; then
    PREFIX="$SKILLBANK_INSTALL_DIR"
elif [ -w /usr/local/bin ] || [ "$(id -u)" = 0 ]; then
    PREFIX="/usr/local/bin"
elif [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    PREFIX="$HOME/.local/bin"
else
    echo "✗ 找不到可写安装目录(试 SKILLBANK_INSTALL_DIR=...)" >&2
    exit 1
fi

mv "$TMP/$ASSET" "$PREFIX/$BIN_NAME"
echo "✓ 已安装 $PREFIX/$BIN_NAME"
command -v "$BIN_NAME" >/dev/null 2>&1 || \
    echo "  提示: $PREFIX 不在 PATH, 加到 shell 配置: export PATH=\"$PREFIX:\$PATH\""
echo "  下一步: skillbank bootstrap --repo-url <中心仓 git URL> --machine <本机别名>"