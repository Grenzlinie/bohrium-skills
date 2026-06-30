package updatecheck

import (
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestCheckCachedReturnsNoticeForNewerCachedVersion(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	resetForTest(t)

	if err := saveState(&updateState{LatestVersion: "0.2.0", CheckedAt: time.Now().Unix()}); err != nil {
		t.Fatal(err)
	}

	info := CheckCached("0.1.0")
	if info == nil {
		t.Fatal("CheckCached returned nil, want update notice")
	}
	if got, want := info.Message(), "bohrium-skills-cli 0.2.0 available, current 0.1.0, run: bohrium-skills-cli update"; got != want {
		t.Fatalf("Message() = %q, want %q", got, want)
	}
}

func TestCheckCachedSkipsDevAndOptOut(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	resetForTest(t)
	if err := saveState(&updateState{LatestVersion: "0.2.0", CheckedAt: time.Now().Unix()}); err != nil {
		t.Fatal(err)
	}
	if got := CheckCached("0.0.0-dev"); got != nil {
		t.Fatalf("CheckCached(dev) = %+v, want nil", got)
	}
	t.Setenv("BOHRIUM_SKILLS_CLI_NO_UPDATE_NOTIFIER", "1")
	if got := CheckCached("0.1.0"); got != nil {
		t.Fatalf("CheckCached(opt-out) = %+v, want nil", got)
	}
}

func TestRefreshCacheUsesTTLAndFetchesExpiredCache(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	resetForTest(t)

	requests := 0
	DefaultClient = &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
		requests++
		return response(http.StatusOK, `{"version":"0.3.0"}`), nil
	})}

	if err := saveState(&updateState{LatestVersion: "0.2.0", CheckedAt: time.Now().Unix()}); err != nil {
		t.Fatal(err)
	}
	RefreshCache("0.1.0")
	if requests != 0 {
		t.Fatalf("fresh cache made %d requests, want 0", requests)
	}

	if err := saveState(&updateState{LatestVersion: "0.2.0", CheckedAt: time.Now().Add(-25 * time.Hour).Unix()}); err != nil {
		t.Fatal(err)
	}
	RefreshCache("0.1.0")
	if requests != 1 {
		t.Fatalf("expired cache made %d requests, want 1", requests)
	}
	data, err := os.ReadFile(filepath.Join(home, ".config", "bohrium-skills-cli", StateFile))
	if err != nil {
		t.Fatal(err)
	}
	if got, want := string(data), `{"latest_version":"0.3.0"`; len(got) < len(want) || got[:len(want)] != want {
		t.Fatalf("state = %s, want prefix %s", got, want)
	}
}

func TestFetchLatestRejectsBadRegistryResponses(t *testing.T) {
	for _, tc := range []struct {
		name string
		code int
		body string
	}{
		{name: "http error", code: http.StatusInternalServerError, body: `{}`},
		{name: "empty version", code: http.StatusOK, body: `{}`},
		{name: "invalid json", code: http.StatusOK, body: `{`},
		{name: "too large", code: http.StatusOK, body: strings.Repeat("x", maxBody+1)},
	} {
		t.Run(tc.name, func(t *testing.T) {
			resetForTest(t)
			DefaultClient = &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
				return response(tc.code, tc.body), nil
			})}
			if got, err := FetchLatest(); err == nil {
				t.Fatalf("FetchLatest() = %q, nil error; want error", got)
			}
		})
	}
}

func resetForTest(t *testing.T) {
	t.Helper()
	for _, key := range []string{"CI", "BUILD_NUMBER", "RUN_ID", "BOHRIUM_SKILLS_CLI_NO_UPDATE_NOTIFIER"} {
		t.Setenv(key, "")
	}
	SetPending(nil)
	RegistryURL = defaultRegistryURL
	DefaultClient = nil
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) {
	return f(r)
}

func response(code int, body string) *http.Response {
	return &http.Response{
		StatusCode: code,
		Body:       io.NopCloser(strings.NewReader(body)),
		Header:     make(http.Header),
	}
}
