# Changelog: core

Changes to the `core` set, released as the package `ai-tools-assets-core` and
tagged `core/v<version>`. The format follows [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-08

### Added

- The skills `ai-tools-engineering-principles`, `ai-tools-agent-governance`,
  `ai-tools-reftags` (with `scripts/ref-index.py`) and
  `ai-tools-technical-writing` (with `scripts/prose-check.py`), and the
  subagent `ai-tools-reference-docs-maintainer`, each script with its tests
  under the skill's `tests/`. They are ported from ai-tools-base at
  `v0.23.2-31-gbc695ce`, ahead of its 0.24.0 release, where they ship as
  `ai-tools-engineering-principles`, `ai-tools-capable-systems-governance`,
  `ai-tools-reftags`, `ai-tools-technical-docs` and
  `ai-tools-reference-architect` under `AGPL-3.0-only`; here they are MIT,
  as the set is, and the copies in ai-tools-base releases keep their
  `AGPL-3.0-only` terms. Every commit to those files in ai-tools-base is
  authored by the maintainer, and the files carry no copyright line, licence
  statement or attribution of another party.
- The set installs in Claude Code as the plugin `ai-tools-assets-core`, from the
  repository's marketplace: `/plugin marketplace add dag-node/ai-tools-assets`.
- The set's skills install in Codex from the same marketplace:
  `codex plugin marketplace add dag-node/ai-tools-assets`.
- The set installs in Qwen Code from the same marketplace, skills and
  subagents both: `qwen extensions install dag-node/ai-tools-assets:ai-tools-assets-core`.
- The set's skills install in Gemini CLI:
  `gemini skills install https://github.com/dag-node/ai-tools-assets.git --path sets/core/skills --consent`.
