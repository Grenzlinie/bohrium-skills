package updater

import (
	"reflect"
	"testing"
)

func TestUpdateNPMInstallThenSyncsSkills(t *testing.T) {
	var calls []string
	runner := FakeRunner{
		LatestVersion: "1.2.0",
		InstallFunc: func(version string) error {
			calls = append(calls, "install:"+version)
			return nil
		},
		SyncFunc: func(version string, force bool) error {
			calls = append(calls, "sync:"+version)
			if force {
				calls = append(calls, "force")
			}
			return nil
		},
		InstallMethod: InstallNPM,
	}

	result, err := Update(UpdateOptions{
		CurrentVersion: "1.1.0",
		Force:          true,
		Runner:         runner,
	})
	if err != nil {
		t.Fatalf("Update() error = %v", err)
	}
	if result.Action != "updated" {
		t.Fatalf("Action = %q, want updated", result.Action)
	}
	want := []string{"install:1.2.0", "sync:1.2.0", "force"}
	if !reflect.DeepEqual(calls, want) {
		t.Fatalf("calls = %#v, want %#v", calls, want)
	}
}

func TestUpdateCheckDoesNotInstallOrSync(t *testing.T) {
	called := false
	runner := FakeRunner{
		LatestVersion: "1.2.0",
		InstallFunc: func(version string) error {
			called = true
			return nil
		},
		SyncFunc: func(version string, force bool) error {
			called = true
			return nil
		},
		InstallMethod: InstallNPM,
	}

	result, err := Update(UpdateOptions{
		CurrentVersion: "1.1.0",
		Check:          true,
		Runner:         runner,
	})
	if err != nil {
		t.Fatalf("Update() error = %v", err)
	}
	if result.Action != "update_available" {
		t.Fatalf("Action = %q, want update_available", result.Action)
	}
	if called {
		t.Fatal("check mode installed or synced")
	}
}
