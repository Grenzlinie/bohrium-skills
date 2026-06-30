package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/dptech-corp/bohrium-skills/internal/build"
	"github.com/dptech-corp/bohrium-skills/internal/syncer"
)

func TestInstallWritesBundledSkillsToThreeTargets(t *testing.T) {
	home := t.TempDir()
	var stdout, stderr bytes.Buffer
	code := run([]string{"install", "--home", home, "--json"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("run install exit = %d, stdout = %s, stderr = %s", code, stdout.String(), stderr.String())
	}

	var out struct {
		Lang        string   `json:"lang"`
		Official    []string `json:"official"`
		Updated     []string `json:"updated"`
		TargetDirs  []string `json:"target_dirs"`
		BackupCount int      `json:"backup_count"`
	}
	if err := json.Unmarshal(stdout.Bytes(), &out); err != nil {
		t.Fatalf("install output is not JSON: %v\n%s", err, stdout.String())
	}
	if out.Lang != "zh" {
		t.Fatalf("lang = %q, want zh", out.Lang)
	}
	if got, want := len(out.Official), 17; got != want {
		t.Fatalf("official count = %d, want %d", got, want)
	}
	if got, want := len(out.TargetDirs), 3; got != want {
		t.Fatalf("target dir count = %d, want %d", got, want)
	}
	for _, dir := range out.TargetDirs {
		if _, err := os.Stat(filepath.Join(dir, "bohrium-job", "SKILL.md")); err != nil {
			t.Fatalf("bohrium-job not installed in %s: %v", dir, err)
		}
	}
}

func TestTextCommandEmitsNoticeOnStderrOnly(t *testing.T) {
	clearNoticeEnv(t)
	home := t.TempDir()
	t.Setenv("HOME", home)
	withVersion(t, "0.1.0")
	writeUpdateState(t, home, "0.2.0")

	var stdout, stderr bytes.Buffer
	code := run([]string{"list"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("run list exit = %d, stdout = %s, stderr = %s", code, stdout.String(), stderr.String())
	}
	if !strings.Contains(stdout.String(), "bohrium-job") {
		t.Fatalf("stdout missing list output: %s", stdout.String())
	}
	if !strings.Contains(stderr.String(), "bohrium-skills-cli 0.2.0 available, current 0.1.0, run: bohrium-skills-cli update") {
		t.Fatalf("stderr missing update notice: %s", stderr.String())
	}
}

func TestJSONCommandIncludesNoticeObject(t *testing.T) {
	clearNoticeEnv(t)
	home := t.TempDir()
	t.Setenv("HOME", home)
	withVersion(t, "0.2.0")
	writeUpdateState(t, home, "0.3.0")
	configDir := filepath.Join(home, ".config", "bohrium-skills-cli")
	if err := syncer.WriteState(configDir, syncer.State{Version: "0.1.0"}); err != nil {
		t.Fatal(err)
	}

	var stdout, stderr bytes.Buffer
	code := run([]string{"status", "--home", home, "--json"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("run status exit = %d, stdout = %s, stderr = %s", code, stdout.String(), stderr.String())
	}
	if stderr.Len() != 0 {
		t.Fatalf("json command wrote stderr notice: %s", stderr.String())
	}
	var out map[string]interface{}
	if err := json.Unmarshal(stdout.Bytes(), &out); err != nil {
		t.Fatalf("stdout is not JSON: %v\n%s", err, stdout.String())
	}
	notice, ok := out["_notice"].(map[string]interface{})
	if !ok {
		t.Fatalf("_notice missing from JSON: %s", stdout.String())
	}
	if _, ok := notice["update"].(map[string]interface{}); !ok {
		t.Fatalf("_notice.update missing: %#v", notice)
	}
	if _, ok := notice["skills"].(map[string]interface{}); !ok {
		t.Fatalf("_notice.skills missing: %#v", notice)
	}
}

func TestVersionJSONDoesNotIncludeNotice(t *testing.T) {
	clearNoticeEnv(t)
	home := t.TempDir()
	t.Setenv("HOME", home)
	withVersion(t, "0.1.0")
	writeUpdateState(t, home, "0.2.0")

	var stdout, stderr bytes.Buffer
	code := run([]string{"version", "--json"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("run version exit = %d, stdout = %s, stderr = %s", code, stdout.String(), stderr.String())
	}
	var out map[string]interface{}
	if err := json.Unmarshal(stdout.Bytes(), &out); err != nil {
		t.Fatalf("stdout is not JSON: %v\n%s", err, stdout.String())
	}
	if _, ok := out["_notice"]; ok {
		t.Fatalf("version JSON included _notice: %s", stdout.String())
	}
}

func withVersion(t *testing.T, version string) {
	t.Helper()
	old := build.Version
	build.Version = version
	t.Cleanup(func() { build.Version = old })
}

func writeUpdateState(t *testing.T, home, latest string) {
	t.Helper()
	dir := filepath.Join(home, ".config", "bohrium-skills-cli")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	data := []byte(`{"latest_version":"` + latest + `","checked_at":` + strconv.FormatInt(time.Now().Unix(), 10) + `}`)
	if err := os.WriteFile(filepath.Join(dir, "update-state.json"), data, 0o644); err != nil {
		t.Fatal(err)
	}
}

func clearNoticeEnv(t *testing.T) {
	t.Helper()
	for _, key := range []string{
		"CI",
		"BUILD_NUMBER",
		"RUN_ID",
		"BOHRIUM_SKILLS_CLI_NO_UPDATE_NOTIFIER",
		"BOHRIUM_SKILLS_CLI_NO_SKILLS_NOTIFIER",
	} {
		t.Setenv(key, "")
	}
}
