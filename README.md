# ai-tools-assets

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Skills and subagents for coding agents, released as versioned sets.**

A set is one collection of assets, kept under `sets/<set>/` and released as
the package `ai-tools-assets-<set>`. Its skills follow the [Agent Skills
specification](https://agentskills.io/) without the fields that change
permissions or run code. A set skill therefore loads unchanged in Claude Code,
Codex, Qwen Code and other agents that read `SKILL.md`, and it does not widen
what a session may do.

**Status.** The repository has its layout and the empty `core` set. It does
not ship any skills or subagents yet, and the commands under `tools/` are not
implemented.

## Layout

```text
sets/<set>/          set.conf, CHANGELOG.md, skills/, subagents/
keys/                maintainer public keys (reserved)
packaging/           nFPM configuration, rendered per set
tools/               new-set, new-asset, validate, build-set, link-set
tests/               tests for tools/
```

Each set has a `set.conf` of `KEY=value` lines, which `ai-tools-base` reads
and does not execute. The keys are documented in `ai-tools-assets(5)`.

## Using a set

With [Agent Tools
Restricted](https://github.com/dag-node/tools-agent-tools-restricted)
(`ai-tools-base`), install the set's package and name the assets to enable in
the root-owned `AI_TOOLS_ASSETS` list. Installing a package does not enable
any asset.

Without base, `tools/link-set` links a built set's skills into the directory
an agent reads, as described in [tools/README.md](tools/README.md).

## Community

- [Contributing](CONTRIBUTING.md), including the asset format
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## License

MIT, see [LICENSE](LICENSE). A skill may state another licence in its
`license` field, and a vendored skill keeps its upstream licence;
[REUSE.toml](REUSE.toml) covers files that do not state one.
