# Packaging

A set is released by pushing a signed tag `<set>/v<semver>` whose version
equals the set's `version` in `set.conf`:

```bash
git tag -s core/v0.1.0 -m "core 0.1.0" && git push origin core/v0.1.0
```

[release.yml](../.github/workflows/release.yml) calls the reusable
`set-release.yml` of
[ai-tools-assets-tools](https://github.com/dag-node/ai-tools-assets-tools),
which holds the [nFPM](https://nfpm.goreleaser.com/) template and the signing
steps; that repository's `packaging/README.md` states the inputs, the
`release` environment and each step. The tag is signed by a maintainer key the
workflow pins. A prerelease tag (`core/v0.2.0-rc.1`) creates a prerelease and
does not publish the RPM.

A release attaches:

| Asset | What it is |
|---|---|
| `ai-tools-assets-<set>-<version>.zip` | the built set, set directory at the top of the archive |
| `….zip.sha256`, `….zip.asc` | its SHA-256 and its detached signature |
| `SHA256SUMS`, `SHA256SUMS.asc` | the set's file inventory and its detached signature |
| `ai-tools-assets-<set>-<version>-1.<dist>.noarch.rpm` | the set under `/usr/share/ai-tools-assets/<set>/`, `SHA256SUMS.asc` included, with an RPM header signature; one per `<dist>` of `el9`, `el10` and `fc44`, served from that distribution's tree |

The dag-node package-signing key, the key `rpm.dagnode.com` serves, makes every
signature. A host verifies the RPM with `rpmkeys -K` and installs it
from that repository with `dnf install ai-tools-assets-<set>`. Claude Code
installs the zip as a plugin through an `archive` marketplace source,
which checks the archive's `sha256`.

Installing a package does not enable any asset. On an `ai-tools-base` host,
an asset is linked only when it is named in the root-owned `AI_TOOLS_ASSETS`
list.
