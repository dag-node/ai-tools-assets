# Changelog: core

Changes to the `core` set, released as the package `ai-tools-assets-sets-core`
(`ai-tools-assets-core` up to 0.2.2) and tagged `core/v<version>`. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.4] - 2026-10-17

### Fixed

- **The MIT text is the one SPDX publishes.** `LICENSES/MIT.txt`,
  which the package carries, is the text `reuse download MIT` writes, its
  holder line the published placeholder; `LICENSE` and `REUSE.toml` name
  the holder. Before, the text carried the holder line, so the tools' licence
  check warned under `license.text-modified`.

## [0.2.3] - 2026-10-15

### Changed

- **The package is `ai-tools-assets-sets-core`.** `dnf upgrade` replaces
  an installed `ai-tools-assets-core` with it in one transaction, and
  `dnf install ai-tools-assets-core` installs it. The files stay under
  `/usr/share/ai-tools-assets/core/`. The release zip is
  `ai-tools-assets-sets-core-<version>.zip`, and the plugin keeps the name
  `ai-tools-assets-core`. Before, the package and the zip were named
  `ai-tools-assets-core`.

### Fixed

- **A comment heading framed by dash runs stands alone.** `prose-check.py`
  ends a block at a comment line such as `# --- Title ---`, as it does at
  a Markdown heading. It joined the heading to the sentence under it, so
  a word of the heading reached a check on that sentence: `definitional`
  matched a noun of the heading, and a guard word in the heading kept
  `unbacked-absolute` from reporting the sentence.

## [0.2.2] - 2026-10-14

### Added

- **`legal-register` check.** `prose-check.py` reports the legal words for
  a process step by default: `ratify`, `ratification`, `amendment`, `hereby`,
  `pursuant`, `thereunder`, `entitlement`, `void` as a verb or a state, and
  `standing` as a noun of status. The hint names the word to write instead:
  approval, revision, change request or decision. The writing skill's "Plain
  register" rule lists the same words.

### Fixed

- **Licence texts are not read.** `prose-check.py` does not read a file named
  `LICENSE`, `LICENCE` or `COPYING`, with any suffix, or a file under
  `LICENSES/`, and `--print-width` reports it as the kind `license`, which
  a formatter skips. It read a `LICENSE.md` as a document and reported the
  publisher's wording, and reported a plain-text licence as `source`, the kind
  a formatter fills.

- **`definitional` reads the noun the pivot opens on.** The `--all` check
  `definitional` reports `is not a` only where the word after the article
  repeats a word of the subject's own clause, as in `a control the system can
  decline is not a control`. A noun from an earlier clause, as in a list of
  test outcomes, and a qualified noun, as in `a name that is not a plain
  name`, are not reported. It matched a repeated word anywhere in five words
  either side of the pivot.

## [0.2.1] - 2026-10-12

### Fixed

- **Release.** core 0.2.1 is the first release of the 0.2.0 changes. The
  `core/v0.2.0` tag has no GitHub release and no package: its release run
  stopped at the Fedora 44 signature check, since the release workflow pinned
  an image digest quay.io no longer serves. The release workflow now calls the
  ai-tools-assets-tools 1.2.0 commit, which pins the current digest.

## [0.2.0] - 2026-10-12

### Changed

- **`--new` pairing.** `prose-check.py --new <revision>` pairs findings by
  check within a file once it has paired them by content. A sentence that a
  rename or a reworded clause touched is not reported for a finding it already
  had. A file reports as many findings of a check as it holds beyond the
  revision's count.
- **Formatter pointer.** The writing skill's `references/checks.md` states that
  a repository names its formatter in its own `CLAUDE.md`, and that the package
  `ai-tools-assets-tools` installs one.

### Fixed

- **Identifiers and code spans.** `prose-check.py` reads a token carrying `_`,
  and a span marked as code, as one word without a stem. The `--all` checks
  `mirrored-clause` and `definitional` stop matching a fragment of an
  identifier such as `ai_tools_load_operators`, or a pair of backticked spans,
  across the pivot.
- **Shell heredocs.** `prose-check.py` does not read the body of a shell
  heredoc, which is data the file writes, such as a test fixture or a seeded
  config header. Its `#` lines reported findings, and `--wrap` reported them
  over the column.

## [0.1.0] - 2026-10-09

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
- The set installs in Claude Code as the plugin `ai-tools-assets-core`,
  from the repository's marketplace:
  `/plugin marketplace add dag-node/ai-tools-assets`.
- The set's skills install in Codex from the same marketplace:
  `codex plugin marketplace add dag-node/ai-tools-assets`.
- The set installs in Qwen Code from the same marketplace, skills and subagents
  both:
  `qwen extensions install dag-node/ai-tools-assets:ai-tools-assets-core`.
- The set's skills install in Gemini CLI:
  `gemini skills install https://github.com/dag-node/ai-tools-assets.git --path sets/core/skills --consent`.
