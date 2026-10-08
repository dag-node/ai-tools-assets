# Signing keys

A release carries signatures by two keys, and this directory does not hold
either public key:

| What | Signed by | Pinned by |
|---|---|---|
| the release tag `<set>/v<semver>` | a maintainer's personal key | its primary fingerprint, in the reusable set-release workflow |
| the zip, `SHA256SUMS` and the RPM | the dag-node package-signing key | its primary fingerprint, `67F42DC18BF764B42D82F14256D2F802CF9832E4` |

The tag signature ties a release to a maintainer, so a leaked CI secret
cannot publish one by itself. The package-signing key is the one
`rpm.dagnode.com` serves. On an `ai-tools-base` host, a root-owned binding
names that primary as the signer of each set this repository publishes, and
base refuses a set whose `SHA256SUMS.asc` does not verify against it.

A single skill's signature takes the name `skill.oms.sig`, reserved so adding
it does not rename or reinterpret a shipped file. Changes here need
repository-owner review.
