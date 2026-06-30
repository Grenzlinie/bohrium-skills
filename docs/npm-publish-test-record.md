# bohrium-skills-cli npm 发布流程测试记录

测试分支：`codex/npm-publish-test-flow`

测试日期：2026-06-30

## 目标

在 fork 仓库上先验证 `bohrium-skills-cli` 的本地构建、临时安装、npm 打包与发布 dry-run 流程，确认后再向官方仓库提交 PR。

## 环境状态

- 当前 remote：`origin https://github.com/Grenzlinie/bohrium-skills.git`
- GitHub CLI 状态：`gh auth status` 显示 `Grenzlinie` token 已失效，需要重新登录后才能 push / create PR / 查看 Actions。
- npm 登录状态：`npm whoami` 返回 `ENEEDAUTH`，说明当前机器尚未登录 npm；真实发布前需要 `npm login` 或配置 CI `NPM_TOKEN`。

## 本地 CLI 临时安装验证

使用临时 HOME，不影响真实 `~/.agents/skills`、`~/.claude/skills`、`~/.codex/skills`。

关键命令：

```bash
cd /Users/siyuliu/Desktop/bohrium-skills
GOCACHE=/Users/siyuliu/Desktop/bohrium-skills/.gocache go build -o /tmp/bohrium-skills-cli ./cmd/bohrium-skills-cli
TEST_HOME=$(mktemp -d /tmp/bohrium-skills-cli-home.XXXXXX)
/tmp/bohrium-skills-cli list
/tmp/bohrium-skills-cli install --home "$TEST_HOME" --json
/tmp/bohrium-skills-cli status --home "$TEST_HOME" --json
find "$TEST_HOME/.agents/skills" -maxdepth 1 -type d -name 'bohrium-*' | wc -l
find "$TEST_HOME/.claude/skills" -maxdepth 1 -type d -name 'bohrium-*' | wc -l
find "$TEST_HOME/.codex/skills" -maxdepth 1 -type d -name 'bohrium-*' | wc -l
sed -n '1,12p' "$TEST_HOME/.agents/skills/bohrium-job/SKILL.md"
/tmp/bohrium-skills-cli install --home "$TEST_HOME" --lang en --json
/tmp/bohrium-skills-cli status --home "$TEST_HOME" --json
```

结果摘要：

- `list` 输出 17 个 `bohrium-*` skills。
- 默认 `install` 安装 `zh` 版本成功。
- `status` 显示三处目标目录均存在，且 `skill_count=17`。
- 三处目录计数均为 `17`。
- `bohrium-job/SKILL.md` 在默认安装后显示中文标题 `# SKILL: Bohrium 任务 (Job) 管理`。
- `install --lang en` 后 `status` 显示 `lang=en`，三处目录仍均为 `skill_count=17`。
- `zh -> en` 覆盖产生 `backup_count=51`，符合 `17 skills × 3 target dirs`。

## Go 测试与构建

```bash
GOCACHE=/Users/siyuliu/Desktop/bohrium-skills/.gocache go test ./...
```

结果：

```text
ok  	github.com/dptech-corp/bohrium-skills	(cached)
ok  	github.com/dptech-corp/bohrium-skills/cmd/bohrium-skills-cli	(cached)
?   	github.com/dptech-corp/bohrium-skills/internal/build	[no test files]
ok  	github.com/dptech-corp/bohrium-skills/internal/syncer	(cached)
ok  	github.com/dptech-corp/bohrium-skills/internal/updater	(cached)
```

```bash
GOCACHE=/Users/siyuliu/Desktop/bohrium-skills/.gocache go build -o /tmp/bohrium-skills-cli-pr-test ./cmd/bohrium-skills-cli
```

结果：构建成功。

## npm 打包与发布 dry-run

```bash
npm_config_cache=/tmp/bohrium-skills-npm-cache npm pack --dry-run
```

结果：

```text
npm notice 📦  bohrium-skills-cli@0.1.0
npm notice filename: bohrium-skills-cli-0.1.0.tgz
npm notice package size: 7.4 kB
npm notice unpacked size: 17.9 kB
npm notice total files: 5
bohrium-skills-cli-0.1.0.tgz
```

```bash
npm_config_cache=/tmp/bohrium-skills-npm-cache npm publish --dry-run
```

结果：

```text
npm notice 📦  bohrium-skills-cli@0.1.0
npm notice Publishing to https://registry.npmjs.org/ with tag latest and default access (dry-run)
+ bohrium-skills-cli@0.1.0
```

注意：dry-run 同时提示 `This command requires you to be logged in ... (dry-run)`，说明真实发布前仍需要 npm 登录或 CI token。

## update --check 现状

```bash
/tmp/bohrium-skills-cli update --check --json
```

当前环境下失败原因是 npm registry 访问被本地代理/沙箱拦截：

```text
connect EPERM 127.0.0.1:7897
```

这是外部网络/代理问题，不影响本地安装、打包和 publish dry-run 验证。真实发布后需要在正常 npm registry 网络环境中复测。

## 后续发布前检查项

- 重新登录 GitHub CLI：`gh auth login -h github.com`
- 登录 npm：`npm login`
- 在 fork 仓库配置 `NPM_TOKEN` secret，用于 release workflow 的 `npm publish --provenance`
- 推送测试分支并触发/观察 GitHub Actions
- 若要真实发布 npm 包，确认包名 `bohrium-skills-cli` 在 npm registry 可用或有发布权限
