# Branching and release

How a change to a set reaches `develop`, becomes a signed `<set>/v<semver>` tag
on `main` and an RPM on `rpm.dagnode.com`, and how the tools pin moves.

## The flow

```text
<type>/<id>-<name>, off develop
      |
      | pull request into develop, rebase-merged once the checks are green
      v
   develop        every pull request and push: ai-tools-assets / validate,
      |           ai-tools-assets / tests (python 3.9) and (python 3.12)
      |
      | chore/<id>-release-<set>-X.Y.Z: set.conf, the manifests written
      | from it and the set's changelog, rebase-merged like any other
      v
   "Merge develop" pull request, develop -> main, merged with a merge commit
      |
      | check-images from the tools at the commit the uses: lines pin
      | git tag -s <set>/vX.Y.Z on main's merge commit
      v
   release.yml calls set-release.yml at the pinned tools commit:
   verify-tag, validate, build-set, sign-files, build-rpm, sign-rpm,
   create-release, dispatch
      |
      v
   GitHub release + rpm.dagnode.com
```

The rulesets of the repository decide the merge methods and who may tag. Each
row is read from `gh api repos/dag-node/ai-tools-assets/rulesets`:

| Ref | Ruleset | What it does |
|---|---|---|
| `develop` | `develop-linear` | requires a linear history, so a pull request into `develop` is rebase-merged and a merge commit is refused |
| `develop`, `main` | `branches-no-delete` | refuses a deletion of either branch |
| `main` | `main-checks` | requires the checks `ai-tools-assets / validate`, `ai-tools-assets / tests (python 3.9)` and `ai-tools-assets / tests (python 3.12)`, and refuses a deletion and a force push |
| `main` | `protect-main` | requires a pull request with one approving review from a code owner, merged with a merge commit alone |
| `*/v*` | `release-tags-create`, `release-tags-immutable` | restricts creation to the ruleset's bypass actors, and refuses an update, a deletion and a force push |

A release tag is immutable, so a release whose run failed is not re-tagged:
the fix lands on `develop` and the next patch version of the set carries it.

## Cutting a set release

The version follows [Semantic Versioning](https://semver.org/), which the set's
`CHANGELOG.md` names: an `[Unreleased]` section holding `### Fixed` alone is
a patch, and a new skill, subagent or script option is a minor.

1. **The release branch** carries the version. Off a synced `develop`,
   with the tools checked out beside this repository:

   ```bash
   git fetch origin && git switch -c chore/ATR-261103c-release-core-0.3.0 origin/develop
   sed -i 's/^version=.*/version=0.3.0/' sets/core/set.conf
   python3 ../ai-tools-assets-tools/tools/sync-manifests
   ```

   `sync-manifests` writes the set's `plugin.json`
   and `.claude-plugin/plugin.json` from `set.conf`, which CI holds
   the committed copies to. In `sets/core/CHANGELOG.md`,
   `## [0.3.0] - 2026-11-03` goes under an empty `## [Unreleased]`. Commit
   with `git commit -s` as `chore: release core 0.3.0`, push, and open the pull
   request with that title. It is rebase-merged into `develop` once the checks
   are green.

2. **`Merge develop`** is opened only once the release commit is on `develop`:
   opened earlier, it runs CI on a tree without that commit and again when it
   lands. Its body lists the commits `main` lacks, oldest first,
   which `origin/main..origin/develop` is exactly, since `main` is a merge
   of `develop`:

   ```bash
   git fetch origin
   gh pr create --repo dag-node/ai-tools-assets --base main --head develop --title "Merge develop" --body "$(git log --reverse --format='- **%s**' origin/main..origin/develop)"
   gh pr merge <number> --repo dag-node/ai-tools-assets --merge --admin
   ```

   `protect-main` asks for one approving review from a code owner,
   and `CODEOWNERS` names the maintainers team, so a maintainer's own pull
   request shows a grey merge button beside green checks: the author cannot
   approve it. The merge goes through the ruleset's bypass, which both routes
   record as the pull request's merge: `gh pr merge --merge --admin`
   from the terminal, or the merge button in the GitHub web interface. A local
   `git merge` and push is refused by the ruleset.

3. **`check-images`** runs immediately before the tag, from a checkout
   of the tools at the commit the `uses:` lines under `.github/workflows/` pin,
   so the images checked are the ones the release will run:

   ```bash
   git -C ../ai-tools-assets-tools switch --detach "$(sed -n 's/.*set-release.yml@\([0-9a-f]*\).*/\1/p' .github/workflows/release.yml)"
   bash ../ai-tools-assets-tools/packaging/release-steps.sh check-images
   ```

   It asks each image's registry for the manifest at the pinned digest
   and exits non-zero when a digest no longer resolves, naming the digest
   the tag resolves to now; a retired digest is taken through [Taking a digest
   refresh](#taking-a-digest-refresh) before the tag. The release run pulls
   every image before its first signature, so a stale digest stops the run
   there otherwise.

4. **The tag**, on `main`'s merge commit, named for the set and signed
   by a maintainer key the workflow pins:

   ```bash
   git fetch origin
   git tag -s core/v0.3.0 -m "core 0.3.0" origin/main && git push origin core/v0.3.0
   ```

   The push prints `Bypassed rule violations` for a bypass actor
   of `release-tags-create`, which is expected. The version must equal
   the set's `version` in `set.conf`, or the build step stops. A prerelease tag
   (`core/v0.3.0-rc.1`) creates a prerelease and does not dispatch. The release
   run verifies the tag, validates and builds the set, signs the zip
   and `SHA256SUMS`, builds and signs the `el9`, `el10` and `fc44` RPMs,
   creates the release
   with what [packaging/README.md](../../packaging/README.md) lists, and asks
   `dag-node/rpm` to publish the RPMs. The release is published when each RPM
   answers at its tree,
   as `https://rpm.dagnode.com/el/9/x86_64/ai-tools-assets-sets-core-0.3.0-1.el9.noarch.rpm`
   does for EL9 (`el/10` and `fedora/44` for the others); the publish run lags
   the dispatch by minutes.

5. **Downstream.** `ai-tools-base` names the release in its
   `tools/lib/assets-core.pin` before its next tag.

## Pinning the tools

Both `uses:` lines under `.github/workflows/` name a workflow
of `dag-node/ai-tools-assets-tools` at one full commit SHA, with a comment
naming what the SHA is, as in `release.yml`:

```yaml
uses: dag-node/ai-tools-assets-tools/.github/workflows/set-release.yml@b11c27282193da07f1067ce905de6974e420c433 # v1.5.0
```

A full SHA in a reviewed commit, not the moving `v1` tag, because the called
workflow runs with this repository's signing secrets: the code that runs
with them changes only in a commit reviewed here. The `validate` run refuses
the two lines when they pin different refs, so the images `check-images` reads
are the ones a release would run.

A **release pin** carries the comment `# v1.5.0` and is the normal state:
the tag the comment names is signed by a maintainer of the tools, and its
release run passed. A **develop pin** carries
`# develop <date>, <dists> digest, ai-tools-assets-tools#<PR>` and exists only
between a digest refresh and the next tools release, since `repin-tools`
refuses a `develop` commit that changes more than the image pins and the tools'
changelog.

### Taking a digest refresh

When the tools' `check-images` reports a retired digest, every pull request
here fails at that step until the tools' `develop` carries the refreshed pin
and this repository pins that commit. The tools' release page holds
the procedure, [The digest
refresh](https://github.com/dag-node/ai-tools-assets-tools/blob/develop/docs/development/release.md#the-digest-refresh);
this repository's half, in a clean checkout on `develop` equal
to `origin/develop`, with the tools checked out beside it:

```bash
bash ../ai-tools-assets-tools/packaging/release-steps.sh repin-tools --id ATR-261103a <full sha>
```

It rewrites both `uses:` lines to the merged refresh commit, commits with `-s`
on `ci/<id>-tools-<dists>-digest`, pushes, and opens the pull request
`ci: call the ai-tools-assets-tools commit that pins the <Distro> image`
with a generated body. The pull request's `ai-tools-assets / validate` run is
the proof: `check-images` passes through the new pin. Rebase-merge it.

### Re-pinning to a tools release

The same command, given a tag, re-pins this repository to a release
of the tools. After the tools' final release run is green, from this
repository's root, with the tools checked out at `develop` beside it:

```bash
bash ../ai-tools-assets-tools/packaging/release-steps.sh repin-tools --id ATR-261120a v1.6.0
```

It verifies the tag, runs `check-images` at the tag's commit, rewrites both
`uses:` lines to `@<full sha> # v1.6.0`, commits with `-s`
on `ci/<id>-tools-1.6.0`, pushes, and opens the pull request
`ci: call the ai-tools-assets-tools 1.6.0 workflows`, whose body lists
the release's changelog headlines. Run from the tools' own checkout, it
refuses, since that checkout is not a caller. Where this repository's git signs
commits, `gpg-agent` asks for the passphrase.
