# Tools

Maintainer and user commands for sets. None is implemented yet.

| Command | What it does |
|---|---|
| `new-set` | creates `sets/<set>/` with a `set.conf` and a `CHANGELOG.md` |
| `new-asset` | creates a skill or subagent in a set from a template |
| `validate` | applies the [asset format](../CONTRIBUTING.md#asset-format) and runs `skills-ref validate` |
| `build-set` | builds a set into a directory with its `SHA256SUMS` |
| `link-set` | links a built set's skills into an agent's skills directory |

`link-set` requires `--target`, the directory the agent reads, and takes
`--copy` for an agent that imports by copying rather than following a link.

```bash
tools/link-set core --target ~/.claude/skills
```
