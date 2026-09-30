# Packaging

Holds the [nFPM](https://nfpm.goreleaser.com/) configuration, rendered once
per set. Each set builds into one package, `ai-tools-assets-<set>`, installed
under `/usr/share/ai-tools-assets/<set>/` and released from the tag
`<set>/v<semver>`. RPM is built first; deb, apk and Arch packages come from the
same configuration.

The same release also publishes `ai-tools-assets-<set>-<version>.zip`, built
from the same files as the package, with the set directory at the top of the
archive. It serves an agent without a package manager, and Claude Code
installs it as a plugin through an `archive` marketplace source, which checks
the archive's `sha256`.

Installing a package does not enable any asset. On an `ai-tools-base` host,
an asset is linked only when it is named in the root-owned `AI_TOOLS_ASSETS`
list.
