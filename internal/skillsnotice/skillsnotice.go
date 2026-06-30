package skillsnotice

import (
	"fmt"
	"os"
	"strings"
	"sync/atomic"

	"github.com/dptech-corp/bohrium-skills/internal/syncer"
	"github.com/dptech-corp/bohrium-skills/internal/updatecheck"
)

type StaleNotice struct {
	Current string `json:"current"`
	Target  string `json:"target"`
}

var pending atomic.Pointer[StaleNotice]

func (s *StaleNotice) Message() string {
	return fmt.Sprintf("bohrium-skills-cli skills %s out of sync with binary %s, run: bohrium-skills-cli update", s.Current, s.Target)
}

func SetPending(notice *StaleNotice) { pending.Store(notice) }

func GetPending() *StaleNotice { return pending.Load() }

func Check(currentVersion, configDir string) *StaleNotice {
	if shouldSkip() {
		return nil
	}
	state, readable, err := syncer.ReadState(configDir)
	if err != nil || !readable || state == nil || strings.TrimSpace(state.Version) == "" {
		return nil
	}
	current := normalizeVersion(state.Version)
	target := normalizeVersion(currentVersion)
	if current == target {
		return nil
	}
	return &StaleNotice{Current: current, Target: target}
}

func shouldSkip() bool {
	return updatecheck.IsCIEnv() || strings.TrimSpace(os.Getenv("BOHRIUM_SKILLS_CLI_NO_SKILLS_NOTIFIER")) != ""
}

func normalizeVersion(version string) string {
	version = strings.TrimSpace(version)
	version = strings.TrimPrefix(version, "v")
	return strings.TrimPrefix(version, "V")
}
