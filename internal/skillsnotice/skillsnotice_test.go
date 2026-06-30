package skillsnotice

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/dptech-corp/bohrium-skills/internal/syncer"
)

func TestCheckReturnsNoticeWhenSkillsStateDrifts(t *testing.T) {
	clearSkipEnv(t)
	home := t.TempDir()
	configDir := filepath.Join(home, ".config", "bohrium-skills-cli")
	if err := syncer.WriteState(configDir, syncer.State{Version: "0.1.0"}); err != nil {
		t.Fatal(err)
	}

	notice := Check("0.2.0", configDir)
	if notice == nil {
		t.Fatal("Check returned nil, want stale notice")
	}
	if got, want := notice.Message(), "bohrium-skills-cli skills 0.1.0 out of sync with binary 0.2.0, run: bohrium-skills-cli update"; got != want {
		t.Fatalf("Message() = %q, want %q", got, want)
	}
}

func TestCheckSilentForInSyncMissingBadStateAndOptOut(t *testing.T) {
	clearSkipEnv(t)
	home := t.TempDir()
	configDir := filepath.Join(home, ".config", "bohrium-skills-cli")
	if err := syncer.WriteState(configDir, syncer.State{Version: "0.2.0"}); err != nil {
		t.Fatal(err)
	}
	if got := Check("0.2.0", configDir); got != nil {
		t.Fatalf("Check(in sync) = %+v, want nil", got)
	}
	if got := Check("0.2.0", filepath.Join(home, "missing")); got != nil {
		t.Fatalf("Check(missing) = %+v, want nil", got)
	}
	badDir := filepath.Join(home, "bad")
	if err := os.MkdirAll(badDir, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(badDir, syncer.StateFileName), []byte("{"), 0o644); err != nil {
		t.Fatal(err)
	}
	if got := Check("0.2.0", badDir); got != nil {
		t.Fatalf("Check(bad json) = %+v, want nil", got)
	}
	t.Setenv("BOHRIUM_SKILLS_CLI_NO_SKILLS_NOTIFIER", "1")
	if got := Check("0.3.0", configDir); got != nil {
		t.Fatalf("Check(opt-out) = %+v, want nil", got)
	}
}

func clearSkipEnv(t *testing.T) {
	t.Helper()
	for _, key := range []string{"CI", "BUILD_NUMBER", "RUN_ID", "BOHRIUM_SKILLS_CLI_NO_SKILLS_NOTIFIER"} {
		t.Setenv(key, "")
	}
}
