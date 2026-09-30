# core

The community baseline set, maintained by the repository owners and released
as the package `ai-tools-assets-core` and the Claude Code and Codex plugin
`ai-tools-core`.

```text
set.conf                    name, version, licence: the source the manifests are written from
CHANGELOG.md
plugin.json                 Agent Plugins manifest, read by Codex
.claude-plugin/plugin.json  Claude Code plugin manifest
skills/<name>/SKILL.md      one directory per skill
agents/<name>.md            one file per subagent
```

A skill or subagent follows the [asset format](../../CONTRIBUTING.md#asset-format),
and its name starts with `ai-tools-`, the prefix of this set. `agents/` holds
subagent files alone: Claude Code loads every `.md` file in a plugin's
`agents/` as a subagent.
