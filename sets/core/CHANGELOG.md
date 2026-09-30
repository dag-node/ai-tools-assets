# Changelog: core

Changes to the `core` set, released as the package `ai-tools-assets-core` and
tagged `core/v<version>`. The format follows [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- The set installs in Claude Code as the plugin `ai-tools-assets-core`, from the
  repository's marketplace: `/plugin marketplace add dag-node/ai-tools-assets`.
- The set's skills install in Codex from the same marketplace:
  `codex plugin marketplace add dag-node/ai-tools-assets`.
- The set installs in Qwen Code from the same marketplace, skills and
  subagents both: `qwen extensions install dag-node/ai-tools-assets:ai-tools-assets-core`.
- The set's skills install in Gemini CLI:
  `gemini skills install https://github.com/dag-node/ai-tools-assets.git --path sets/core/skills --consent`.
