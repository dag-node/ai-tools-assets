# Tools

Maintainer and user commands for sets. Every command runs from a checkout of
[ai-tools-assets-tools](https://github.com/dag-node/ai-tools-assets-tools),
whose `tools/README.md` states each one in full; the table names what each
does for this repository.

| Command | What it does |
|---|---|
| `check-publisher` | checks that the marketplace, the set names, each `set.conf`'s `maintainers` and `source`, and the plugin manifests' names, authors and URLs are copied from `publisher.conf`; with `--repository <owner>/<repo>`, that `publisher.conf` describes that repository. CI runs it on every pull request, and with `--repository` on every release tag |
| `new-set` | creates `sets/<set>/` with a `set.conf` and a `CHANGELOG.md` |
| `new-asset` | creates a skill or subagent in a set from a template |
| `validate` | applies the [asset format](../CONTRIBUTING.md#asset-format) and runs `skills-ref validate` |
| `build-set` | builds a set into a directory with its `SHA256SUMS`, and the release zip |
| `sync-manifests` | writes each set's `plugin.json` and `.claude-plugin/plugin.json` and the repository's `.claude-plugin/marketplace.json` from `set.conf`; CI refuses a manifest that differs from its output |
| `link-set` | links a built set's skills into an agent's skills directory |

`validate` reads [reserved-words.txt](reserved-words.txt), the words a set's
name does not start with.

`link-set` requires `--target`, the directory the agent reads, and takes
`--copy` for an agent that imports by copying rather than following a link.

```bash
tools/link-set core --target ~/.claude/skills
```
