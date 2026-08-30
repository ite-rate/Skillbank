// bootstrap 模块测试 — config 往返 + InitRepo 脚手架(幂等)。
package bootstrap_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/bootstrap"
	"github.com/ite-rate/skillbank/internal/config"
)

// 用户级 config 在真实 HOME 下读写, 测试用 HOME 重定向隔离。
func withFakeHome(t *testing.T) string {
	t.Helper()
	home := filepath.Join(t.TempDir(), "home")
	if err := os.MkdirAll(home, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HOME", home)
	return home
}

func TestConfigSaveLoadRoundtrip(t *testing.T) {
	withFakeHome(t)
	if _, p, err := bootstrap.LoadConfig(); err != nil {
		t.Fatal(err)
	} else if _, err := os.Stat(p); !os.IsNotExist(err) {
		t.Fatalf("空 HOME 下 config 应不存在: %s", p)
	}

	p, err := bootstrap.SaveConfig(bootstrap.AppConfig{
		RepoPath: "/home/u/Skillbank", RepoURL: "git@example.com:u/skillbank.git",
	})
	if err != nil {
		t.Fatal(err)
	}
	cfg, _, err := bootstrap.LoadConfig()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.RepoPath != "/home/u/Skillbank" || cfg.RepoURL != "git@example.com:u/skillbank.git" {
		t.Fatalf("roundtrip: %+v", cfg)
	}
	raw, _ := os.ReadFile(p)
	if !strings.Contains(string(raw), "skillbank 用户级配置") {
		t.Fatalf("config 应有头注释:\n%s", raw)
	}
	if strings.Contains(string(raw), ".tmp") {
		t.Fatal("原子写不应留 tmp")
	}
}

func TestInitRepoScaffoldIdempotent(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "my-skillbank")
	created, err := bootstrap.InitRepo(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(created) == 0 {
		t.Fatal("首次 init 应产出脚手架")
	}
	for _, want := range []string{"skills/.gitkeep", "manifests/.gitkeep",
		"agents.toml", "machines.toml", ".gitignore", "(git init)"} {
		found := false
		for _, c := range created {
			if c == want {
				found = true
			}
		}
		if !found {
			t.Fatalf("缺 %s: %v", want, created)
		}
	}
	// agents.toml 模板可被 config 加载(7 agent)
	if _, err := os.Stat(filepath.Join(dir, ".git")); err != nil {
		t.Fatal("git init 应生效")
	}

	// 幂等: 已存在的文件不覆盖
	if err := os.WriteFile(filepath.Join(dir, "agents.toml"),
		[]byte("# 用户改过"), 0o644); err != nil {
		t.Fatal(err)
	}
	created2, err := bootstrap.InitRepo(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, c := range created2 {
		if c == "agents.toml" {
			t.Fatal("已存在的 agents.toml 不应被覆盖")
		}
	}
	raw, _ := os.ReadFile(filepath.Join(dir, "agents.toml"))
	if string(raw) != "# 用户改过" {
		t.Fatal("用户改动必须保留")
	}
}

func TestInitRepoAgentsTomlParsable(t *testing.T) {
	// 脚手架出的 agents.toml 与 config 加载器兼容(7 agent 全量)
	dir := filepath.Join(t.TempDir(), "r")
	if _, err := bootstrap.InitRepo(dir); err != nil {
		t.Fatal(err)
	}
	agents, err := config.LoadAgents(filepath.Join(dir, "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	if len(agents.Names()) != 7 {
		t.Fatalf("模板应含 7 agent: %v", agents.Names())
	}
}