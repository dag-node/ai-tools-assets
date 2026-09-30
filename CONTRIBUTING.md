# Contributing

How a set and its assets are laid out, the format every asset must follow,
and the conventions for commits and pull requests.

## Sets

A set lives in `sets/<set>/` and holds a `set.conf`, a `CHANGELOG.md`, and
the kind directories `skills/` and `subagents/`. `core` is the community
baseline, maintained by the repository owners; an organization or a domain
adds its own set beside it, with its own `CODEOWNERS` line.

A set's `set.conf` is `KEY=value` data, read by `ai-tools-base` and never
sourced. It requires `format=1`, `name`, `version` (semver), `summary`,
`license` (SPDX) and `maintainers`; `source`, `requires_base` and
`integrations` are optional. Base reports and ignores an unknown key, and
refuses a set whose `format` is higher than it supports.

## Asset format

An asset is found by its shape: a skill is a directory under `skills/` holding
`SKILL.md`, and a subagent is a `*.md` file under `subagents/` other than
`README.md`. Its id is `<set>/<kind>/<name>`. `tools/validate` in CI and base's
validator apply the same rules, so an asset CI accepts also loads on a host.

**Names.** An asset or set name is 1 to 64 characters of `a-z`, `0-9` and
`-`, does not start or end with `-`, and does not contain `--`. It equals the
skill's directory name, the subagent's file stem, or the set's directory, and
the frontmatter `name`. The `ai-tools-` prefix belongs to base's own assets
and is refused.

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
- a `.claude-plugin/` directory;
- an absolute path into `/opt/ai-tools`, `/usr/share` or `/usr/local/share`;
  a skill names its own files relative to its root, and another skill by name;
- in a `.cs` script, a `#:package` directive, an `#:sdk` other than
  `Microsoft.NET.Sdk` or `Microsoft.NET.Sdk.Web`, and a `#:project` outside
  the skill;
- a committed binary, and content under `jobs/` or `libs/`, which are
  reserved.

A skill carries every file it runs and calls a script through its interpreter
(`python3 scripts/x.py`, `bash scripts/x.sh`, `dotnet run scripts/x.cs`), so a
call does not depend on the exec bit. Python scripts use the standard library
only. CI warns on a `SKILL.md` over 500 lines.

**Reserved file names.** `SHA256SUMS`, `SHA256SUMS.asc`, `SHA512SUMS*`,
`*.oms.sig`, `UPSTREAM.conf`, and `README.md` in a kind directory are never
discovered as assets. CI refuses one used for anything else.

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
