package syncer

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"testing/fstest"
	"time"
)

func TestPlanSyncPreservesDeletedAndAddsNew(t *testing.T) {
	got := PlanSync(PlanInput{
		Version:        "1.2.3",
		OfficialSkills: []string{"bohrium-job", "bohrium-node", "bohrium-new"},
		LocalSkills:    []string{"bohrium-job", "custom-skill"},
		PreviousState:  &State{OfficialSkills: []string{"bohrium-job", "bohrium-node"}},
		StateReadable:  true,
	})

	assertStrings(t, got.ToUpdate, []string{"bohrium-job", "bohrium-new"})
	assertStrings(t, got.Added, []string{"bohrium-new"})
	assertStrings(t, got.SkippedDeleted, []string{"bohrium-node"})
}

func TestPlanSyncForceRestoresAllOfficial(t *testing.T) {
	got := PlanSync(PlanInput{
		Version:        "1.2.3",
		OfficialSkills: []string{"bohrium-job", "bohrium-node"},
		LocalSkills:    []string{"bohrium-job"},
		PreviousState:  &State{OfficialSkills: []string{"bohrium-job", "bohrium-node"}},
		StateReadable:  true,
		Force:          true,
	})

	assertStrings(t, got.ToUpdate, []string{"bohrium-job", "bohrium-node"})
	assertStrings(t, got.SkippedDeleted, []string{})
}

func TestSyncWritesThreeTargetsAndBacksUpExistingSkill(t *testing.T) {
	home := t.TempDir()
	targets := []string{
		filepath.Join(home, ".agents", "skills"),
		filepath.Join(home, ".claude", "skills"),
		filepath.Join(home, ".codex", "skills"),
	}
	for _, target := range targets {
		existing := filepath.Join(target, "bohrium-job")
		if err := os.MkdirAll(existing, 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(existing, "SKILL.md"), []byte("old"), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	source := fstest.MapFS{
		"zh/bohrium-job/SKILL.md":  {Data: []byte("---\nname: bohrium-job\n---\nnew\n")},
		"zh/bohrium-job/script.py": {Data: []byte("print('ok')\n")},
		"zh/bohrium-node/SKILL.md": {Data: []byte("---\nname: bohrium-node\n---\nnode\n")},
	}
	result, err := Sync(SyncOptions{
		Version:   "1.2.3",
		Lang:      "zh",
		HomeDir:   home,
		ConfigDir: filepath.Join(home, ".config", "bohrium-skills-cli"),
		Targets:   targets,
		SourceFS:  source,
		Now:       fixedNow,
	})
	if err != nil {
		t.Fatalf("Sync() error = %v", err)
	}

	assertStrings(t, result.Updated, []string{"bohrium-job", "bohrium-node"})
	if got, want := result.BackupCount, 3; got != want {
		t.Fatalf("BackupCount = %d, want %d", got, want)
	}
	for _, target := range targets {
		got, err := os.ReadFile(filepath.Join(target, "bohrium-job", "SKILL.md"))
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(got), "new") {
			t.Fatalf("%s was not updated: %q", target, string(got))
		}
		if _, err := os.Stat(filepath.Join(target, "bohrium-node", "SKILL.md")); err != nil {
			t.Fatalf("new skill missing in %s: %v", target, err)
		}
	}
	if _, err := os.Stat(filepath.Join(home, ".config", "bohrium-skills-cli", "skills-state.json")); err != nil {
		t.Fatalf("state file missing: %v", err)
	}
}

func TestSyncPreservesDeletedOfficialSkillUnlessForced(t *testing.T) {
	home := t.TempDir()
	target := filepath.Join(home, ".agents", "skills")
	source := fstest.MapFS{
		"zh/bohrium-job/SKILL.md":  {Data: []byte("---\nname: bohrium-job\n---\njob\n")},
		"zh/bohrium-node/SKILL.md": {Data: []byte("---\nname: bohrium-node\n---\nnode\n")},
	}

	first, err := Sync(SyncOptions{
		Version:   "1.0.0",
		Lang:      "zh",
		HomeDir:   home,
		ConfigDir: filepath.Join(home, ".config", "bohrium-skills-cli"),
		Targets:   []string{target},
		SourceFS:  source,
		Now:       fixedNow,
	})
	if err != nil {
		t.Fatalf("first Sync() error = %v", err)
	}
	assertStrings(t, first.Updated, []string{"bohrium-job", "bohrium-node"})
	if err := os.RemoveAll(filepath.Join(target, "bohrium-node")); err != nil {
		t.Fatal(err)
	}

	second, err := Sync(SyncOptions{
		Version:   "1.0.1",
		Lang:      "zh",
		HomeDir:   home,
		ConfigDir: filepath.Join(home, ".config", "bohrium-skills-cli"),
		Targets:   []string{target},
		SourceFS:  source,
		Now:       fixedNow,
	})
	if err != nil {
		t.Fatalf("second Sync() error = %v", err)
	}
	assertStrings(t, second.SkippedDeleted, []string{"bohrium-node"})
	if _, err := os.Stat(filepath.Join(target, "bohrium-node")); !os.IsNotExist(err) {
		t.Fatalf("deleted skill restored without force, stat err = %v", err)
	}

	forced, err := Sync(SyncOptions{
		Version:   "1.0.2",
		Lang:      "zh",
		HomeDir:   home,
		ConfigDir: filepath.Join(home, ".config", "bohrium-skills-cli"),
		Targets:   []string{target},
		SourceFS:  source,
		Force:     true,
		Now:       fixedNow,
	})
	if err != nil {
		t.Fatalf("forced Sync() error = %v", err)
	}
	assertStrings(t, forced.Updated, []string{"bohrium-job", "bohrium-node"})
	if _, err := os.Stat(filepath.Join(target, "bohrium-node", "SKILL.md")); err != nil {
		t.Fatalf("force did not restore deleted skill: %v", err)
	}
}

func assertStrings(t *testing.T, got, want []string) {
	t.Helper()
	if got == nil {
		got = []string{}
	}
	if want == nil {
		want = []string{}
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

func fixedNow() time.Time {
	return time.Date(2026, 6, 30, 12, 0, 0, 0, time.UTC)
}
