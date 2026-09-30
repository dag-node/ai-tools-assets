# Security policy

A skill is text an agent follows. An asset in this repository can direct
an agent to read, write, run or send whatever the agent's session permits, so
review covers what an asset tells the agent to do, and its scripts.

## What a set asset cannot carry

The [asset format](CONTRIBUTING.md#asset-format) refuses the features that
act before a person or the model reads the asset, or that change what
a session may do:

- `allowed-tools`, which pre-approves tools without a prompt while the skill
  runs;
- a subagent's `permissionMode`, `hooks` and `mcpServers`, which change
  permissions, run commands, or add tool servers;
- dynamic context injection, which runs a shell command when the skill loads;
- a `.claude-plugin/` directory inside a skill, which turns the skill into
  a plugin that can bundle hooks and servers;
- in a set, any Claude Code plugin component other than skills and
  subagents: hooks, MCP and LSP servers, `bin/`, monitors, commands,
  workflows, output styles, themes and `settings.json`. A set directory
  holds an allowlisted set of entries, so a component kind Claude Code adds
  later is refused as well;
- a NuGet package in a C# script, which fetches code the checksums do not
  cover.

The repository is public and its content is not vetted per host. Installing
a set's package does not enable any asset: `ai-tools-base` links an asset only
when it is named in the operator's root-owned enable list. Installing a set as
a Claude Code plugin is the user's own action and enables every asset in it;
an administrator restricts which marketplaces and plugins a user may install
with Claude Code's `strictKnownMarketplaces` and `enabledPlugins` settings.

## Signing

Signing is planned and not implemented. The file names `SHA256SUMS.asc`, for
a set, and `skill.oms.sig`, for a single skill, are reserved for it. Maintainer
public keys will be kept under `keys/`.

## Supported versions

Only the latest release of each set is supported for security updates.

## Reporting a vulnerability

Please report suspected vulnerabilities privately:

* [GitHub private vulnerability
  reporting](https://github.com/dag-node/ai-tools-assets/security/advisories/new).
* Alternatively, email **[tools@dagnode.com](mailto:tools@dagnode.com)**
  with the subject prefix `[SECURITY]`.

Do not include vulnerability details in public issues or pull requests.

A vulnerability here includes an asset that instructs an agent to exfiltrate
data, weaken a confinement, or run code the asset does not show, and a gap in
the asset format that lets a set asset do one of these. Include the set,
its version, the asset, and the agent that loaded it.

## Handling and disclosure

Security reports are reviewed and prioritized according to their potential
impact. Response and remediation times depend on maintainer availability; no
fixed timeframes are guaranteed.

Please coordinate public disclosure with the maintainer so that users can
receive a fix or mitigation where possible.
