package bohriumskills

import (
	"path/filepath"
	"testing"
)

func TestOfficialSkillsListsBothLanguages(t *testing.T) {
	for _, lang := range []string{"zh", "en"} {
		t.Run(lang, func(t *testing.T) {
			skills, err := OfficialSkills(lang)
			if err != nil {
				t.Fatalf("OfficialSkills(%q) error = %v", lang, err)
			}
			if got, want := len(skills), 17; got != want {
				t.Fatalf("OfficialSkills(%q) length = %d, want %d", lang, got, want)
			}

			seen := map[string]bool{}
			for _, skill := range skills {
				if skill.Lang != lang {
					t.Fatalf("skill %s language = %q, want %q", skill.Name, skill.Lang, lang)
				}
				if filepath.Base(skill.Path) != skill.Name {
					t.Fatalf("skill path %q base does not match name %q", skill.Path, skill.Name)
				}
				if !skill.HasFile("SKILL.md") {
					t.Fatalf("skill %s missing SKILL.md", skill.Name)
				}
				if seen[skill.Name] {
					t.Fatalf("duplicate skill %q", skill.Name)
				}
				seen[skill.Name] = true
			}
		})
	}
}

func TestValidateEmbeddedSkillsRejectsNameMismatches(t *testing.T) {
	if err := ValidateEmbeddedSkills(); err != nil {
		t.Fatalf("ValidateEmbeddedSkills() error = %v", err)
	}
}
