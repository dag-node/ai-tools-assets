# Contributing

How a set and its assets are laid out, the format every asset must follow,
and the conventions for commits and pull requests.

## Sets

A set lives in `sets/<set>/` and is also a Claude Code and a Codex plugin,
installed from the repository as it is committed, without a build step:

```text
sets/<set>/
├── set.conf                    name, version, licence
├── CHANGELOG.md
├── README.md
├── plugin.json                 Agent Plugins manifest, read by Codex
├── .claude-plugin/plugin.json  Claude Code plugin manifest
├── skills/<name>/SKILL.md
└── agents/<name>.md            subagents
```

A set directory holds these entries and no others; CI refuses anything else,
including every other kind of plugin component (hooks, MCP and LSP servers,
`bin/`, monitors, commands, workflows, output styles, themes,
`settings.json`). `jobs/` is reserved. `agents/` holds subagent files alone,
because Claude Code loads every `.md` file in it as a subagent.

Neither plugin manifest declares any component keys, so each agent reads
`skills/`, and Claude Code `agents/`, from their default places. Codex reads
skills alone; the subagents are Claude Code's. Each manifest's `name`,
`version` and `license` equal the set's: the plugin is named like the package,
`ai-tools-assets-<set>`, and takes its version from `set.conf`. The
repository's `.claude-plugin/marketplace.json` lists every set, and Codex reads
the same file. The manifests and the marketplace are written from `set.conf`,
and CI refuses one that differs from it.

`core` is the community baseline, maintained by the repository owners; a
publisher adds its own set beside it, named as [Names](#asset-format) states,
with its own `CODEOWNERS` line.

A set's `set.conf` is `KEY=value` data, read by `ai-tools-base` and never
sourced. It requires `format=1`, `name`, `version` (semver), `summary`,
`license` (SPDX), `maintainers` and `source`, the repository the set is
published from; `requires_base` and `integrations` are optional. Base reports
and ignores an unknown key, and refuses a set whose `format` is higher than it
supports.

## Asset format

An asset is found by its shape: a skill is a directory under `skills/` holding
`SKILL.md`, and a subagent is a `*.md` file under `agents/`. Its id is
`<set>/<kind>/<name>`. `tools/validate` in CI and base's validator apply the
same rules, so an asset CI accepts also loads on a host.

**Names.** An asset or set name is 1 to 64 characters of `a-z`, `0-9` and
`-`, does not start or end with `-`, does not contain `--`, and does not
contain `anthropic` or `claude`, which Claude reserves. It equals the skill's
directory name, the subagent's file stem, or the set's directory, and the
frontmatter `name`.

**A set's name is its namespace.** The package `ai-tools-assets-<set>`, the
plugin of the same name, the install directory, every asset id
`<set>/<kind>/<name>`, and the prefix of the set's asset names all derive from
it. An agent lists skills and subagents in one list sorted by name, where the
set does not show, so the prefix is what groups a set's assets in that list.
A published set's name starts with its publisher:

| Set | Name | Its assets |
|---|---|---|
| this repository's baseline | `core` | `ai-tools-<name>` |
| a publisher's set | `<publisher>` or `<publisher>-<topic>`: `acme`, `acme-dotnet` | `<set>-<name>`: `acme-dotnet-ef-migrations` |
| vendored into a set, with an `UPSTREAM.conf` | — | keeps its upstream name |

`core`, the `ai-tools-` prefix and the marketplace name `ai-tools-assets`
belong to this repository; CI and base's validator refuse `ai-tools-` in every
other set. A set's name does not start with a word from
[tools/reserved-words.txt](tools/reserved-words.txt), the names of AI vendors,
their agents and models, and large technology companies (`openai`, `codex`,
`google`, `gemini`, `microsoft`, `qwen`, …), so a set and the assets it authors
do not read as published by one of them. CI refuses such a set name; the word
may still name a subject later in an asset's name (`ai-tools-codex-config`),
and a vendored asset keeps its upstream name. A fork that publishes its own
content renames its sets and its marketplace, so its packages, plugins and
skills do not share a name with this repository's. An operator's local copy of
`core` under `/usr/local/share/ai-tools-assets/` keeps the name on purpose:
that is how ai-tools-base overrides a packaged set on one host.

A name prevents a collision and does not prove who published a set. Base
shows each set's `source` and reports when it changes, and a set's signature,
once signing lands, is what binds a name to its publisher. Two enabled assets
of one name are both left unlinked and reported.

Skill names follow one pattern across a set, a noun phrase
(`ai-tools-technical-writing`). A description says what the skill does, then
when to use it, in the third person; Claude Code cuts a description at 1,536
characters in its listing, so the key use case comes first. `SKILL.md` stays
under 500 lines, with longer material in files it links to directly.

**Skill frontmatter** uses only the Agent Skills specification's fields:

```markdown
---
name: pdf-processing
description: Extract text and tables from PDF files and fill PDF forms. Use when a task reads or edits a PDF.
license: Apache-2.0
---
```

| Field | In a set skill |
|---|---|
| `name`, `description` | required; `description` at most 1024 characters |
| `license` | allowed; overrides the set's `license` |
| `compatibility` | allowed; at most 500 characters |
| `metadata` | allowed; string values; this project's keys start with `ai-tools-` |
| `allowed-tools`, any other key | refused |

**Subagent frontmatter** is an allowlisted subset of Claude Code's format:
`name` and `description` (required, `description` at most 1024 characters),
`tools`, `disallowedTools`, `model`, `effort`, `maxTurns`, `color`, `skills`
and `metadata`. Any other key is refused.

**Body and files.** CI refuses:

- dynamic context injection: a `` !`command` `` line or a ` ```! ` block;
- a `.claude-plugin/` directory inside a skill, which would make the skill
  a plugin of its own;
- a symbolic link inside an asset, which a zip or a copy does not carry
  the same way on every host;
- an absolute path into `/opt/ai-tools`, `/usr/share` or `/usr/local/share`;
  a skill names its own files relative to its root, and another skill by name;
- in a `.cs` script, a `#:package` directive, an `#:sdk` other than
  `Microsoft.NET.Sdk` or `Microsoft.NET.Sdk.Web`, and a `#:project` outside
  the skill;
- a committed binary, and content under `jobs/` or `libs/`, which are
  reserved.

A skill carries every file it runs, committed in the skill, and calls
a script through its interpreter (`python3 scripts/x.py`, `bash scripts/x.sh`,
`dotnet run scripts/x.cs`), so a call does not depend on the exec bit. A git
install reads the repository as committed, so a library shared through
`libs/`, once it lands, is copied into each skill that uses it and the copy is
committed. Python scripts use the standard library only. CI warns on
a `SKILL.md` over 500 lines.

**Reserved file names.** `SHA256SUMS`, `SHA256SUMS.asc`, `SHA512SUMS*`,
`*.oms.sig`, `UPSTREAM.conf`, `README.md`, `plugin.json`, and the directories
`.claude-plugin/` and `.agents/` are never discovered as assets. CI refuses
one used for anything else.

The allowlists start narrow: allowing a field later does not break a shipped
set, where refusing one would. Propose a field in an issue, with the asset that
needs it.

## Checks

CI runs `tools/validate` (which includes `skills-ref validate`), `reuse lint`,
`shellcheck`, `ruff`, a secret scan, and a check that no file name matches
a credential pattern.

## Commit style

Commit messages follow `type(scope): summary` (`feat`, `fix`, `docs`, `test`,
`chore`, `refactor`), with the set as the scope for asset changes:
`feat(core): add the pdf-processing skill`. Keep the "why" in the body. Record
a user-visible change in the set's `CHANGELOG.md` in the same pull request.

### AI-assisted commits

Commits in this repository frequently carry a `Co-Authored-By` trailer naming
an AI model. This records how the change was produced. Every commit is
authored and reviewed by a human contributor.

## Pull requests

Use a branch named `<type>/<id>-<name>` and give the pull request an explicit
title in the same `type(scope): summary` form as a commit subject. A set is
released by tagging `<set>/v<semver>` after its `version` and `CHANGELOG.md`
are updated.

## License

Contributions are made under the MIT license (see `LICENSE`) unless the file
or the skill states another. Each file that differs states its licence in an
`SPDX-License-Identifier` header or, for a skill, its `license` field.
A vendored skill keeps its upstream licence.
