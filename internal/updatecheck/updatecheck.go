package updatecheck

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

const (
	defaultRegistryURL = "https://registry.npmjs.org/bohrium-skills-cli/latest"
	cacheTTL           = 24 * time.Hour
	fetchTimeout       = 5 * time.Second
	StateFile          = "update-state.json"
	maxBody            = 256 << 10
)

var (
	RegistryURL   = defaultRegistryURL
	DefaultClient *http.Client
	pending       atomic.Pointer[UpdateInfo]
)

type UpdateInfo struct {
	Current string `json:"current"`
	Latest  string `json:"latest"`
}

func (u *UpdateInfo) Message() string {
	return fmt.Sprintf("bohrium-skills-cli %s available, current %s, run: bohrium-skills-cli update", u.Latest, u.Current)
}

type updateState struct {
	LatestVersion string `json:"latest_version"`
	CheckedAt     int64  `json:"checked_at"`
}

type npmLatestResponse struct {
	Version string `json:"version"`
}

func SetPending(info *UpdateInfo) { pending.Store(info) }

func GetPending() *UpdateInfo { return pending.Load() }

func CheckCached(currentVersion string) *UpdateInfo {
	if shouldSkip(currentVersion) {
		return nil
	}
	state, _ := loadState()
	if state == nil || state.LatestVersion == "" {
		return nil
	}
	if !IsNewer(state.LatestVersion, currentVersion) {
		return nil
	}
	return &UpdateInfo{Current: normalizeVersion(currentVersion), Latest: normalizeVersion(state.LatestVersion)}
}

func NeedsRefresh(currentVersion string) bool {
	if shouldSkip(currentVersion) {
		return false
	}
	state, err := loadState()
	if err != nil || state == nil {
		return true
	}
	return time.Since(time.Unix(state.CheckedAt, 0)) >= cacheTTL
}

func RefreshCache(currentVersion string) {
	if !NeedsRefresh(currentVersion) {
		return
	}
	latest, err := FetchLatest()
	if err != nil {
		return
	}
	_ = saveState(&updateState{LatestVersion: latest, CheckedAt: time.Now().Unix()})
}

func FetchLatest() (string, error) {
	client := DefaultClient
	if client == nil {
		client = &http.Client{Timeout: fetchTimeout}
	}
	resp, err := client.Get(RegistryURL)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("npm registry: HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, maxBody+1))
	if err != nil {
		return "", err
	}
	if len(body) > maxBody {
		return "", fmt.Errorf("npm registry response exceeds %d bytes", maxBody)
	}
	var result npmLatestResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return "", err
	}
	version := strings.TrimSpace(result.Version)
	if version == "" {
		return "", fmt.Errorf("npm registry: empty version")
	}
	return version, nil
}

func IsCIEnv() bool {
	for _, key := range []string{"CI", "BUILD_NUMBER", "RUN_ID"} {
		if os.Getenv(key) != "" {
			return true
		}
	}
	return false
}

func IsRelease(version string) bool {
	version = normalizeVersion(version)
	if version == "" || version == "dev" || version == "DEV" || version == "0.0.0-dev" {
		return false
	}
	if gitDescribePattern.MatchString(version) {
		return false
	}
	return parseVersionDetail(version) != nil
}

func IsNewer(candidate, current string) bool {
	ap := parseVersionDetail(candidate)
	bp := parseVersionDetail(current)
	if ap == nil {
		return false
	}
	if bp == nil {
		return true
	}
	for i := 0; i < 3; i++ {
		if ap.core[i] > bp.core[i] {
			return true
		}
		if ap.core[i] < bp.core[i] {
			return false
		}
	}
	return comparePrerelease(ap.prerelease, bp.prerelease) > 0
}

func shouldSkip(version string) bool {
	if os.Getenv("BOHRIUM_SKILLS_CLI_NO_UPDATE_NOTIFIER") != "" {
		return true
	}
	if IsCIEnv() {
		return true
	}
	return !IsRelease(version)
}

func statePath() string {
	return filepath.Join(configDir(), StateFile)
}

func configDir() string {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		return filepath.Join(".", ".config", "bohrium-skills-cli")
	}
	return filepath.Join(home, ".config", "bohrium-skills-cli")
}

func loadState() (*updateState, error) {
	data, err := os.ReadFile(statePath())
	if err != nil {
		return nil, err
	}
	var state updateState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, err
	}
	return &state, nil
}

func saveState(state *updateState) error {
	dir := configDir()
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	data, err := json.Marshal(state)
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, ".update-state-*.json")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmpName, statePath())
}

var (
	gitDescribePattern = regexp.MustCompile(`-\d+-g[0-9a-f]{7,}`)
	versionPattern     = regexp.MustCompile(`^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$`)
)

type parsedVersion struct {
	core       [3]int
	prerelease string
}

func parseVersionDetail(version string) *parsedVersion {
	version = normalizeVersion(version)
	matches := versionPattern.FindStringSubmatch(version)
	if matches == nil {
		return nil
	}
	var parsed parsedVersion
	for i := 0; i < 3; i++ {
		n, err := strconv.Atoi(matches[i+1])
		if err != nil {
			return nil
		}
		parsed.core[i] = n
	}
	parsed.prerelease = matches[4]
	if parsed.prerelease != "" && !validPrerelease.MatchString(parsed.prerelease) {
		return nil
	}
	return &parsed
}

var validPrerelease = regexp.MustCompile(`^(?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*$`)

func comparePrerelease(a, b string) int {
	if a == "" && b == "" {
		return 0
	}
	if a == "" {
		return 1
	}
	if b == "" {
		return -1
	}
	ap := strings.Split(a, ".")
	bp := strings.Split(b, ".")
	for i := 0; i < len(ap) || i < len(bp); i++ {
		if i >= len(ap) {
			return -1
		}
		if i >= len(bp) {
			return 1
		}
		cmp := comparePrereleaseIdentifier(ap[i], bp[i])
		if cmp != 0 {
			return cmp
		}
	}
	return 0
}

func comparePrereleaseIdentifier(a, b string) int {
	an, aErr := strconv.Atoi(a)
	bn, bErr := strconv.Atoi(b)
	switch {
	case aErr == nil && bErr == nil:
		if an < bn {
			return -1
		}
		if an > bn {
			return 1
		}
		return 0
	case aErr == nil:
		return -1
	case bErr == nil:
		return 1
	default:
		return strings.Compare(a, b)
	}
}

func normalizeVersion(version string) string {
	version = strings.TrimSpace(version)
	version = strings.TrimPrefix(version, "v")
	return strings.TrimPrefix(version, "V")
}
