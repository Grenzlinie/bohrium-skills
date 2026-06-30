package bohriumskills

import (
	"embed"
	"fmt"
	"io/fs"
	"path"
	"sort"
	"strings"
)

// EmbeddedFS contains the bundled Bohrium skills.
//
//go:embed zh/** en/**
var EmbeddedFS embed.FS

type Skill struct {
	Lang  string
	Name  string
	Path  string
	Files []string
}

func (s Skill) HasFile(name string) bool {
	for _, file := range s.Files {
		if file == name {
			return true
		}
	}
	return false
}

func OfficialSkills(lang string) ([]Skill, error) {
	if lang != "zh" && lang != "en" {
		return nil, fmt.Errorf("unsupported language %q", lang)
	}
	entries, err := fs.ReadDir(EmbeddedFS, lang)
	if err != nil {
		return nil, err
	}

	var skills []Skill
	for _, entry := range entries {
		if !entry.IsDir() || !strings.HasPrefix(entry.Name(), "bohrium-") {
			continue
		}
		skillPath := path.Join(lang, entry.Name())
		data, err := fs.ReadFile(EmbeddedFS, path.Join(skillPath, "SKILL.md"))
		if err != nil {
			return nil, fmt.Errorf("%s: %w", skillPath, err)
		}
		name, err := frontmatterName(string(data))
		if err != nil {
			return nil, fmt.Errorf("%s/SKILL.md: %w", skillPath, err)
		}
		var files []string
		if err := fs.WalkDir(EmbeddedFS, skillPath, func(filePath string, d fs.DirEntry, walkErr error) error {
			if walkErr != nil {
				return walkErr
			}
			if d.IsDir() {
				return nil
			}
			rel := strings.TrimPrefix(filePath, skillPath+"/")
			files = append(files, rel)
			return nil
		}); err != nil {
			return nil, err
		}
		sort.Strings(files)
		skills = append(skills, Skill{Lang: lang, Name: name, Path: skillPath, Files: files})
	}
	sort.Slice(skills, func(i, j int) bool { return skills[i].Name < skills[j].Name })
	return skills, nil
}

func OfficialSkillNames(lang string) ([]string, error) {
	skills, err := OfficialSkills(lang)
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(skills))
	for _, skill := range skills {
		names = append(names, skill.Name)
	}
	return names, nil
}

func ValidateEmbeddedSkills() error {
	for _, lang := range []string{"zh", "en"} {
		skills, err := OfficialSkills(lang)
		if err != nil {
			return err
		}
		for _, skill := range skills {
			if path.Base(skill.Path) != skill.Name {
				return fmt.Errorf("%s: frontmatter name %q does not match directory", skill.Path, skill.Name)
			}
			if !skill.HasFile("SKILL.md") {
				return fmt.Errorf("%s: missing SKILL.md", skill.Path)
			}
		}
	}
	return nil
}

func frontmatterName(text string) (string, error) {
	lines := strings.Split(text, "\n")
	if len(lines) == 0 || strings.TrimSpace(lines[0]) != "---" {
		return "", fmt.Errorf("missing frontmatter")
	}
	for _, line := range lines[1:] {
		line = strings.TrimSpace(line)
		if line == "---" {
			break
		}
		key, value, ok := strings.Cut(line, ":")
		if !ok || strings.TrimSpace(key) != "name" {
			continue
		}
		value = strings.TrimSpace(value)
		value = strings.Trim(value, `"'`)
		if value == "" {
			return "", fmt.Errorf("empty name")
		}
		return value, nil
	}
	return "", fmt.Errorf("frontmatter name not found")
}
