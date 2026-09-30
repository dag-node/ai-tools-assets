# Maintainer keys

Reserved for the public keys of set maintainers. Signing is not implemented, so
this directory does not hold any keys yet.

When signing lands, a set is signed in `SHA256SUMS.asc` beside its
`SHA256SUMS`, and a single skill in `skill.oms.sig`. Both names are reserved
now, so adding a signature does not rename or reinterpret a shipped file.
Changes here need repository-owner review.
