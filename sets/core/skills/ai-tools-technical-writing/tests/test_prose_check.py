# SPDX-License-Identifier: MIT
"""Unit tests for scripts/prose-check.py, the mechanical half of the writing standard.

Each check is driven with a fixture it must report and with the corrected form it must stay silent on, so neither
a broken pattern nor one widened into reporting good prose passes. The exit status, the suppression markers, the read
mode an extension selects, and the git-backed modes are held to the same two-sided contract.
"""
# The fixtures hold cross-reference reftags as text, so the tree-wide reference check does not read this file.
# ref-index: ignore-file
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "prose-check.py"

# A hook or an outer repository exports these, and each would point the fixture repository's git at another index.
GIT_LOCATION_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY")


def case_id(name: str) -> str:
    return name.split(".", 1)[0]


class ProseCheckTestCase(unittest.TestCase):
    """Runs the checker from a temporary directory holding the fixtures, so a finding names a relative path."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def fixture(self, name: str, *lines: str) -> str:
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(line + "\n" for line in lines))
        return name

    def run_check(self, *args: str, cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(cwd or self.dir), env=env,
                              capture_output=True, text=True)
        return proc.returncode, (proc.stdout + proc.stderr).rstrip("\n")

    def assertReports(self, check: str, name: str, *lines: str, options: tuple = ()) -> None:
        _, out = self.run_check(*options, self.fixture(name, *lines))
        self.assertIn(check, out, f"{case_id(name)}: did NOT report {check}")

    def assertSilent(self, name: str, *lines: str, options: tuple = ()) -> None:
        rc, out = self.run_check(*options, self.fixture(name, *lines))
        self.assertEqual((rc, out), (0, ""), f"{case_id(name)}: expected no finding; rc {rc}, output: {out}")

    def assertOmits(self, check: str, out: str, description: str) -> None:
        self.assertNotIn(check, out, f"{description} -- reported {check}: {out}")

    def assertCases(self, reported: list, silent: list, options: tuple = ()) -> None:
        for check, name, *lines in reported:
            with self.subTest(case_id(name)):
                self.assertReports(check, name, *lines, options=options)
        for name, *lines in silent:
            with self.subTest(case_id(name)):
                self.assertSilent(name, *lines, options=options)


class DefaultChecksTest(ProseCheckTestCase):
    def test_each_default_check_fires_on_the_shape_it_names(self) -> None:
        self.assertCases([
            ("fronted-quantifier", "TEST-PC-01-fronted-quantifier.md", "The helper takes no path argument."),
            ("nothing", "TEST-PC-02-nothing.md", "There is nothing left to check."),
            # An emit verb elsewhere in the sentence does not exempt a `nothing` it does not govern.
            ("nothing", "TEST-PC-79-nothing-ungoverned.md", "The sweep prints a summary, and nothing is exempt."),
            ("unbacked-cost", "TEST-PC-03-unbacked-cost.md", "The label probe is cheap."),
            ("predicted-action", "TEST-PC-04-wants-clause.md",
             "A host that wants it enforced keeps operator.conf root-owned."),
            ("predicted-action", "TEST-PC-05-second-person.md", "If you want the notice, you should set the key."),
            ("positional-reference", "TEST-PC-67-positional.md",
             "The rule above governs a first draft, and the steps are covered below."),
            ("positional-reference", "TEST-PC-68-positional-paren.md",
             "An explicit answer at the end of the install (below) puts the line back."),
            ("positional-reference", "TEST-PC-69-positional-placement.md",
             "The details are printed plain below the box."),
            ("register-verb", "TEST-PC-183-register-verb.md", "The gate admits the name only in a launcher's charset."),
            ("register-verb", "TEST-PC-185-register-verb-past.md",
             "A checksum is admitted only in exact 64-hex shape."),
        ], [])

    def test_corrected_forms_are_silent(self) -> None:
        self.assertCases([], [
            ("TEST-PC-06-fronted-quantifier-ok.md", "The helper does not take a path argument."),
            ("TEST-PC-07-nothing-ok.md", "The helper does not read the path argument, so the validator is skipped."),
            ("TEST-PC-184-register-verb-ok.md", "The gate accepts the name only in a launcher's charset."),
            ("TEST-PC-70-positional-threshold.md", "A comment line stays below 120 columns, and a box within 80."),
            # A cost claim backed by a frequency, and one backed by a bounded operation named as the subject.
            ("TEST-PC-08-cost-frequency.md", "It runs once per restart, not per connection, so the relabel is cheap."),
            ("TEST-PC-09-cost-bounded.md", "A single write of the whole text keeps the window negligible."),
            ("TEST-PC-10-predicted-action-ok.md",
             "The installer creates `operator.conf` root-owned, and the probe reads it there."),
            # An advisory reader, a man page's operator, and `reader` naming a function stay outside the vocabulary.
            ("TEST-PC-11-person-registers.md",
             "A reader should stop at the first mismatch, and you can set the key by hand.",
             "A clamped reader will refuse the value, which the caller reports."),
            ("TEST-PC-12-cost-compounds.md",
             "The prompt is fast-tracked when its default is yes, and the build is fail-fast."),
        ])

    def test_nothing_as_an_output_verbs_object_is_a_result(self) -> None:
        # Exempt: the object of an output verb. Not exempt: an authority, a returned value, and an empty effect.
        self.assertCases([
            ("nothing", "TEST-PC-81-nothing-granted.md", "A claim over a sealed directory grants nothing."),
            ("nothing", "TEST-PC-82-nothing-returned.md", "The helper returns nothing when the two agree."),
            ("nothing", "TEST-PC-83-nothing-run.md", "A comment between the two runs nothing."),
        ], [
            ("TEST-PC-80-nothing-result.md", "Prints nothing when the set in force matches the baseline.",
             "The drift report writes nothing on a host that has kept the shipped patterns."),
        ])


class MarkupChecksTest(ProseCheckTestCase):
    def test_each_bare_literal_kind_is_reported_and_its_backticked_form_is_silent(self) -> None:
        self.assertCases([
            ("bare-option", "TEST-PC-84-bare-option.md", "Pass --dry-run to preview the claim."),
            ("bare-option", "TEST-PC-85-bare-option-short.md", "The -n spelling was dropped at 0.15.0."),
            ("bare-option", "TEST-PC-86-bare-option-comment.sh", "x=1", "# The claim takes --for and refuses root."),
            ("bare-placeholder", "TEST-PC-87-bare-placeholder.md", "The helper writes <operator> into the registry."),
            ("bare-variable", "TEST-PC-88-bare-variable.md", "The unit hands AI_TOOLS_AGENT_EXEC to the shim."),
            ("bare-path", "TEST-PC-89-bare-path-root.md", "The gate is staged under src/usr/local/bin."),
            ("bare-path", "TEST-PC-90-bare-path-extension.md",
             "The seeder reads managed-assets.lib.sh from the datadir."),
        ], [
            ("TEST-PC-91-markup-backticked.md",
             "Pass `--dry-run` to preview the claim, writing `<operator>` into the registry.",
             "The unit hands `AI_TOOLS_AGENT_EXEC` to `src/usr/local/bin/ai-tools-run`."),
        ])

    def test_shapes_that_are_not_markup(self) -> None:
        self.assertCases([], [
            # A hyphenated word, spaced dashes, and a list marker.
            ("TEST-PC-92-option-not-an-option.md",
             "A well-maintained page keeps its wording, and the gate -- a read-only one -- refuses.",
             "- an item in a list takes a marker"),
            ("TEST-PC-93-placeholder-html.md", "A tag such as <code>x</code> is markup, so the check reads it as one."),
            ("TEST-PC-96-path-link.md",
             "The conventions are in [docs/naming-conventions.md](docs/naming-conventions.md)."),
            ("TEST-PC-97-path-prose.md", "The ratio of docs:code stays low, and/or the header is filled, etc."),
            ("TEST-PC-98-path-version.md", "Rocky 9.5 and release 0.16.0 carry one policy."),
        ])

    def test_document_only_checks_do_not_read_a_source_comment(self) -> None:
        self.assertCases([], [
            ("TEST-PC-94-variable-comment.sh", "x=1", "# The unit hands AI_TOOLS_AGENT_EXEC to the shim."),
            ("TEST-PC-95-path-comment.sh", "x=1", "# The seeder reads managed-assets.lib.sh from the datadir."),
        ])

    def test_exemptions_each_read_by_one_check(self) -> None:
        self.assertCases([
            # An extension outside the whole-file set would read a section-7 page as source and report zero.
            ("nothing", "TEST-PC-141-man-page-seven.7", ".TH X 7", "There is nothing left to check."),
            # The SPDX tag is not joined to the header sentence beneath it. `reuse lint` and check-licenses read the
            # tag in this fixture as a second expression of this file, so the lines sit in an ignored block.
            # REUSE-IgnoreStart
            ("bare-option", "TEST-PC-101-spdx.sh", "# SPDX-License-Identifier: AGPL-3.0-only",
             "# The claim takes --for and refuses root."),
            # REUSE-IgnoreEnd
        ], [
            ("TEST-PC-99-contract-fragment.sh", "x=1", "# usage: ai-tools-admin operators add --for <name>"),
            ("TEST-PC-99-contract-signature.md",
             "seed_asset <kind> <name> -- place the shipped asset, and report what it replaced."),
            ("TEST-PC-100-man-page.1", ".TH AI-TOOLS 1", ".B \\-\\-full", ".I /etc/ai-tools/operator.conf",
             "The AI_TOOLS_REQUIRE_SELINUX key is read at launch."),
            ("TEST-PC-142-man-page-seven-markup.7", ".TH X 7", ".B \\-\\-full",
             "The AI_TOOLS_REQUIRE_SELINUX key is read at launch."),
        ])

    def test_a_backticked_span_survives_each_way_it_can_be_lost(self) -> None:
        self.assertCases([], [
            ("TEST-PC-104-span-holds-a-period.md",
             "A refusal reads `ai-tools projects claim <path>. Claim it with the CLI` and stops."),
            ("TEST-PC-105-span-glued.md", "The `an`-macro form is read as one word."),
            ("TEST-PC-106-span-suffix.md", "A session that `cat`s the root-owned log keeps reading."),
            ("TEST-PC-107-span-double-backtick.md", "A value carrying `` ` `` is passed to `logger` as one argument."),
            ("TEST-PC-118-span-wrapped-alternation.md",
             "The logger records one line (`confirm: <question> -> yes|no (answered",
             "| default | assume-yes)`) for every decision."),
        ])

    def test_option_boundaries(self) -> None:
        self.assertCases([
            ("bare-option", "TEST-PC-117-option-short-pair.md", "Pass -v and -x to the shim."),
            ("bare-option", "TEST-PC-126-option-value.md", "The scriptlet passes --scope=full to the seeder."),
            ("bare-option", "TEST-PC-132-option-after-slash.md", "The listing is `--help`/-h and nothing else."),
            ("bare-option", "TEST-PC-133-option-after-bracket.md", "Run it as `--check` [--all] on the block."),
            ("bare-option", "TEST-PC-135-and-short-option.md", "It returns EACCES and -e would report it missing."),
            ("bare-option", "TEST-PC-136-and-after-comma.md", "A symlink is listed, and -type f excludes it."),
            ("bare-option", "TEST-PC-137-word-colon.sh", "x=1", "# Flags: --suggest appends the proposal."),
            ("bare-option", "TEST-PC-140-comment-fence-closed.sh", "x=1", "# Usage:", "#   ```bash",
             "#   podman build -t image -f file .", "#   ```", "# Then pass --rm to it."),
        ], [
            ("TEST-PC-116-option-suspended-hyphen.md",
             "The ACL makes the whole tree agent-readable and -writable once it is claimed."),
            ("TEST-PC-127-option-value-marked.md", "The scriptlet passes `--scope=full` to the seeder."),
            ("TEST-PC-134-suspended-hyphen.md", "The tree is agent-readable and -writable by design."),
            ("TEST-PC-138-contract-colon.sh", "x=1", "# run_gate: pass --allow-uncommitted through to the gate."),
            ("TEST-PC-139-comment-fence.sh", "x=1", "# Usage:", "#   ```bash", "#   podman build -t image -f file .",
             "#   ```"),
            ("TEST-PC-128-ellipsis.sh", "x=1",
             "# seed_asset <kind> <name>... -- place the shipped asset, and report what it replaced."),
        ])

    def test_an_option_value_stops_before_the_closing_punctuation(self) -> None:
        _, out = self.run_check(self.fixture("TEST-PC-129-option-value-punctuation.md",
                                             "The scriptlet passes --scope=full, then the rest."))
        self.assertIn("[--scope=full]", out, "TEST-PC-129: the value stops before the comma")

    def test_an_assignment_is_a_variable_and_an_html_attribute_is_not(self) -> None:
        self.assertReports("bare-variable", "TEST-PC-130-assignment.md", "The unit sets Type=oneshot and nothing else.")
        _, out = self.run_check(self.fixture("TEST-PC-131-html-attribute.md",
                                             '## Security model <a id="ref-section-e7n8"></a>', "",
                                             "The section states the model."))
        self.assertOmits("bare-variable", out, "TEST-PC-131: an HTML attribute is not an assignment")

    def test_path_boundaries(self) -> None:
        self.assertCases([
            ("bare-path", "TEST-PC-120-path-absolute-root.md", "The account is created at /opt, never at /home."),
            ("bare-path", "TEST-PC-115-path-uppercase.md", "The router CLAUDE.md holds the invariants."),
        ], [
            ("TEST-PC-121-path-absolute-word.md", "An /optional group is enabled by the operator alone."),
            ("TEST-PC-114-path-product.md", "The updater keeps Node.js current under the account."),
        ])

    def test_a_literal_split_by_its_own_backticks(self) -> None:
        self.assertCases([
            ("split-literal", "TEST-PC-122-split-literal.md",
             "The unit is `/usr/lib/systemd/system/ai-tools-handback`@.service on the host."),
        ], [
            ("TEST-PC-123-split-literal-coordination.md",
             "The type keeps it off other domains' `tmp_t`/`user_tmp_t` files.",
             "The seeder reads `managed-assets.lib.sh`. It runs as root."),
        ])

    def test_a_doc_comment_format_marks_its_own_literals(self) -> None:
        self.assertCases([
            ("bare-option", "TEST-PC-125-doc-markup-bare.cs",
             "/// Runs the build with --verbosity=quiet and reports what it wrote."),
        ], [
            ("TEST-PC-124-doc-markup.cs",
             '/// Runs the build with <c>--verbosity=quiet</c>, reported by <see cref="Builder"/>.'),
        ])

    def test_path_roots_are_a_checker_option(self) -> None:
        sentence = "The module sits in selinux/policy and loads at boot."
        _, out = self.run_check(self.fixture("TEST-PC-102-path-roots.md", sentence))
        self.assertOmits("bare-path", out, "TEST-PC-102-path-roots: a root outside the default set is not a path")
        _, out = self.run_check("--path-roots", "selinux/", self.fixture("TEST-PC-103-path-roots-arg.md", sentence))
        self.assertIn("bare-path", out, "TEST-PC-103-path-roots-arg: --path-roots names the root it reports")


class NonProseRegionsTest(ProseCheckTestCase):
    def test_each_region_is_skipped_and_the_prose_beside_it_is_read(self) -> None:
        self.assertCases([
            # The indent that opens a code block is a continuation line inside a list item.
            ("bare-option", "TEST-PC-109-list-continuation.md", "- An item whose continuation runs on:", "",
             "    The launcher takes --full and refuses root."),
            # A folded scalar's body is prose.
            ("bare-option", "TEST-PC-111-frontmatter-body.md", "---", "description: >",
             "  Use where the launcher takes --full and refuses root.", "---", "The rule is stated once."),
            ("bare-option", "TEST-PC-113-url-prose.md",
             "The page at https://example.org/a_b.md says the launcher takes --full."),
        ], [
            ("TEST-PC-108-indented-code.md", "Start here -- one command answers it:", "",
             "    sudo ai-tools audit --since '2 days ago'", "", "It reads the two trails and reports what refused."),
            ("TEST-PC-110-frontmatter.md", "---", "paths:", "  - src/usr/local/lib/ai-tools/msg.lib.sh", "---",
             "The library wraps a refusal to the terminal width."),
            ("TEST-PC-112-url.md",
             "The AV rules are at https://example.org/notebook/src/avc_rules.md and stay current."),
        ])


class SuppressionTest(ProseCheckTestCase):
    def test_the_line_marker_and_a_quoted_span(self) -> None:
        self.assertCases([], [
            ("TEST-PC-13-allow-marker.md", "The label probe is cheap. <!-- prose-check: ignore -->"),
            ("TEST-PC-14-quoted-span.md",
             "Write `does not take a path argument` rather than the fronted `takes no path`."),
        ])

    def test_the_file_marker_only_on_a_line_of_its_own(self) -> None:
        self.assertCases([
            ("nothing", "TEST-PC-78-ignore-file-named.md",
             "A file carrying <!-- prose-check: ignore-file --> as a line of its own is not read.",
             "There is nothing left to check."),
        ], [
            ("TEST-PC-77-ignore-file.md", "<!-- prose-check: ignore-file -->", "There is nothing left to check.",
             "The helper takes no path argument."),
            ("TEST-PC-143-ignore-file-roff.7", '.\\" prose-check: ignore-file', ".TH X 7",
             "There is nothing left to check."),
        ])

    def test_a_binary_file_is_not_read(self) -> None:
        (self.dir / "TEST-PC-144-binary.webp").write_bytes(b"RIFF\0\0WEBP\n# There is nothing left to check.\n")
        rc, out = self.run_check("TEST-PC-144-binary.webp")
        self.assertEqual((rc, out), (0, ""), f"TEST-PC-144-binary: expected no finding; rc {rc}, output: {out}")


class ExitStatusTest(ProseCheckTestCase):
    def test_exit_status(self) -> None:
        rc, out = self.run_check(self.fixture("TEST-PC-15-exit-finding.md", "There is nothing left to check."))
        self.assertEqual(rc, 1, f"TEST-PC-15-exit-finding: exits 1 when a finding is reported; output: {out}")
        rc, out = self.run_check(self.fixture("TEST-PC-16-exit-clean.md", "The helper does not take a path argument."))
        self.assertEqual(rc, 0, f"TEST-PC-16-exit-clean: exits 0 when clean; output: {out}")


class ReadModeTest(ProseCheckTestCase):
    def test_the_extension_decides_the_read_mode_and_the_options_override_it(self) -> None:
        rc, out = self.run_check(self.fixture("TEST-PC-17-source-comment.conf", "KEY=value",
                                              "# There is nothing left to check."))
        self.assertEqual(rc, 1, f"TEST-PC-17-source-comment: source mode reads a # comment; output: {out}")
        body = self.fixture("TEST-PC-18-source-body.conf", "There is nothing left to check.")
        rc, out = self.run_check(body)
        self.assertEqual(rc, 0, f"TEST-PC-18-source-body: source mode leaves a non-comment body unread; output: {out}")
        rc, out = self.run_check("--prose", body)
        self.assertEqual(rc, 1, f"TEST-PC-18-source-body: --prose reads the same body as prose; output: {out}")
        md = self.fixture("TEST-PC-19-prose-as-source.md", "# There is nothing left to check.",
                          "The helper does not take a path argument.")
        rc, out = self.run_check("--source", md)
        self.assertEqual(rc, 1, f"TEST-PC-19-prose-as-source: --source reads a .md as comments only; output: {out}")


class InvariantAltitudeTest(ProseCheckTestCase):
    def test_a_mechanism_is_reported_in_the_router_and_nowhere_else(self) -> None:
        altitude = "The stop helper is `750 root:root`, so the agent cannot replace it."
        _, out = self.run_check(self.fixture("CLAUDE.md", altitude))
        self.assertIn("invariant-altitude", out, "TEST-PC-20-altitude-mode: reports a file mode in the router")
        _, out = self.run_check(self.fixture("TEST-PC-21-domain.rule.md", altitude))
        self.assertOmits("invariant-altitude", out,
                         "TEST-PC-21-domain: the same sentence is not reported in a domain rule")

    def test_the_other_two_marks(self) -> None:
        _, out = self.run_check(self.fixture("CLAUDE.md",
                                             "The gate is in `providers.lib.sh:123`, which the launch path calls."))
        self.assertIn("invariant-altitude", out, "TEST-PC-22-altitude-file-line: reports a file:line reference")
        _, out = self.run_check(self.fixture("CLAUDE.md",
                                             "The refusal is asserted in tests/unit/providers.sh, from both ends."))
        self.assertIn("invariant-altitude", out, "TEST-PC-23-altitude-test-path: reports a test path")

    def test_an_invariant_without_mechanism_is_silent(self) -> None:
        rc, out = self.run_check(self.fixture("CLAUDE.md",
                                              "The control plane is root-owned and not writable by `SANDBOX_USER`."))
        self.assertEqual(rc, 0, f"TEST-PC-24-router-invariant: an invariant carrying no mechanism is not reported; "
                                f"output: {out}")


class ClosedSetCountTest(ProseCheckTestCase):
    def test_a_count_word_standing_alone_and_the_forms_that_name_the_set(self) -> None:
        _, out = self.run_check("--all", self.fixture("TEST-PC-25-closed-set.md", "The command seeds both."))
        self.assertIn("closed-set-count", out, "TEST-PC-25-closed-set: reports a count word standing alone")
        for name, lines, description in [
            ("TEST-PC-26-closed-set-named.md", ["The command seeds the operator's config files."],
             "the named set is not reported"),
            ("TEST-PC-27-closed-set-noun.md", ["Both files are seeded at enrolment."],
             "a following noun names what is counted"),
            ("TEST-PC-28-closed-set-correlative.md", ["It seeds both the allowlist and the secret patterns.",
                                                      "The manifest and the key both ship in the package."],
             "enumerated members are not reported"),
        ]:
            with self.subTest(case_id(name)):
                _, out = self.run_check("--all", self.fixture(name, *lines))
                self.assertOmits("closed-set-count", out, f"{case_id(name)}: {description}")


class MessageTest(ProseCheckTestCase):
    def test_a_commit_message_is_checked(self) -> None:
        msg = self.fixture("TEST-PC-40-message.txt", "fix(x): state what changed", "",
                           "There is nothing left to check.")
        rc, out = self.run_check("--message", msg)
        self.assertEqual(rc, 1, f"TEST-PC-40-message: --message checks a commit message; output: {out}")


@unittest.skipUnless(shutil.which("git"), "git not available")
class GitRepositoryTestCase(ProseCheckTestCase):
    """A fixture repository whose git reads the test's own configuration alone."""

    def setUp(self) -> None:
        super().setUp()
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items() if key not in GIT_LOCATION_VARIABLES}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", HOME=str(self.dir),
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        self.git("-c", "init.defaultBranch=main", "init", "-q")

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=str(self.repo), env=self.env, check=True, capture_output=True, text=True)

    def write(self, name: str, text: str) -> None:
        (self.repo / name).write_text(text, encoding="utf-8")

    def stage(self, name: str, text: str) -> None:
        self.write(name, text)
        self.git("add", name)

    def commit(self, name: str, text: str) -> None:
        self.stage(name, text)
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", name)

    def checker_output(self, *args: str) -> str:
        return self.run_check(*args, cwd=self.repo, env=self.env)[1]

    def rewrite(self, before: str, after: str) -> str:
        """The `--kept` report for doc.md committed as `before` and staged as `after`."""
        self.commit("doc.md", before)
        self.stage("doc.md", after)
        return self.checker_output("--kept")


class KeptTest(GitRepositoryTestCase):
    def test_a_swapped_set_and_a_weakened_modality(self) -> None:
        kept = self.rewrite("The file carries no secrets, and the rule is never a glob.\n",
                            "The file contains only settings, and the rule is not a glob.\n")
        self.assertIn("dropped", kept, "TEST-PC-30-kept-set: --kept reports a dropped security term")
        self.assertIn("weakened", kept, "TEST-PC-31-kept-modality: --kept reports a weakened modality")

    def test_a_preserved_claim_is_silent(self) -> None:
        kept = self.rewrite("The file carries no secrets, and the rule is never a glob.\n",
                            "The file does not carry any secrets, and the rule is never a glob.\n")
        self.assertEqual(kept, "", f"TEST-PC-32-kept-preserved: --kept reported a preserved claim: {kept}")

    def test_a_dropped_access_verb(self) -> None:
        kept = self.rewrite("The agent may not read other users files.\n", "No rule grants access to them.\n")
        self.assertIn("dropped [read]", kept, "TEST-PC-33-kept-access-verb: reports a dropped verb")

    def test_an_inflection_is_one_term(self) -> None:
        kept = self.rewrite("The helper searches the tree once.\n", "The helper does not search the tree.\n")
        self.assertEqual(kept, "", f"TEST-PC-34-kept-inflection: reported an inflection as a dropped claim: {kept}")

    def test_a_dropped_rfc_2119_verb(self) -> None:
        kept = self.rewrite("A preview must not ask to apply.\n", "A preview stops before the confirmation.\n")
        self.assertIn("weakened [must not]", kept, "TEST-PC-35-kept-rfc-verb: reports a dropped RFC 2119 verb")

    def test_the_negation_is_matched_before_its_stem(self) -> None:
        kept = self.rewrite("A preview must not ask to apply.\n", "A preview must ask before it applies.\n")
        self.assertIn("weakened [must not]", kept,
                      'TEST-PC-36-kept-negation-first: "must not" weakened to "must" is reported')

    def test_a_contraction_and_its_long_form_are_one_modality(self) -> None:
        kept = self.rewrite("The agent cannot read the file.\n", "The agent can't read the file.\n")
        self.assertEqual(kept, "", f"TEST-PC-37-kept-contraction: reported a contraction as a weakening: {kept}")

    def test_a_dropped_contraction_reports_as_its_long_form(self) -> None:
        kept = self.rewrite("The agent can't read the file.\n", "The agent reads the file.\n")
        self.assertIn("weakened [cannot]", kept,
                      "TEST-PC-38-kept-contraction-dropped: a dropped contraction reports as its long form")

    def test_a_dropped_mode(self) -> None:
        kept = self.rewrite("The home root is drwxr-s--x at 2751, and the claim runs chmod g+s on it.\n",
                            "The home root gives the group read and traverse.\n")
        self.assertIn("dropped [drwxr-s--x]", kept, "TEST-PC-39-kept-mode-rendering: a dropped mode rendering")
        self.assertIn("dropped [g+s]", kept, "TEST-PC-39-kept-symbolic-mode: a dropped symbolic mode")
        self.assertIn("dropped [2751]", kept, "TEST-PC-39-kept-special-octal: a dropped four-digit octal")

    def test_a_mode_changed_in_place(self) -> None:
        kept = self.rewrite("The dir is 2751 and the file is 640, stripped with g-x.\n",
                            "The dir is 2750 and the file is 660, stripped with g-w.\n")
        self.assertIn("dropped [2751]", kept, "TEST-PC-39-kept-mode-changed: an octal changed in place")
        self.assertIn("dropped [g-x]", kept, "TEST-PC-39-kept-symbolic-changed: a symbolic mode changed in place")


class StagedTest(GitRepositoryTestCase):
    def test_frontmatter_takes_its_own_lines_and_no_more(self) -> None:
        self.commit("doc.md", "The dir is 2750 and the file is 660, stripped with g-w.\n")
        self.stage("front.md", "---\npaths:\n  - src/**\n---\n\nThe launcher takes --full and refuses root.\n")
        staged = self.checker_output("--all", "--staged")
        self.assertIn("bare-option", staged,
                      "TEST-PC-119-staged-frontmatter: an unclosed region does not silence the lines after it")


class NewTest(GitRepositoryTestCase):
    INSERTED = "An inserted line that is plain.\nAnother inserted line, also plain.\n"

    def setUp(self) -> None:
        super().setUp()
        self.commit("new.md", "The account is never an administrator.\nA claim adds nothing here.\n")

    def test_a_finding_that_only_moved_is_not_new(self) -> None:
        self.write("new.md", self.INSERTED + "The account is never an administrator.\n"
                   "A claim adds nothing here.\nThe helper grants no access.\n")
        added = self.checker_output("--all", "--new", "HEAD", "new.md")
        self.assertIn("grants no access", added, "TEST-PC-39a-new-added: --new reports the figure the edit introduced")
        self.assertOmits("never", added, "TEST-PC-39b-new-shifted: a finding that only moved down the file")
        self.assertOmits("nothing", added, "TEST-PC-39c-new-shifted-second: the second one the insert displaced")

    def test_a_reworded_sentence_that_still_reports_is_new(self) -> None:
        self.write("new.md", self.INSERTED + "The service account is never an administrator.\n"
                   "A claim adds nothing here.\nThe helper grants no access.\n")
        added = self.checker_output("--all", "--new", "HEAD", "new.md")
        self.assertIn("The service account", added,
                      "TEST-PC-39d-new-edited: a sentence reworded and still reporting counts as new")

    def test_a_path_the_revision_lacks_reports_every_finding(self) -> None:
        self.write("fresh.md", "The helper grants no access.\n")
        added = self.checker_output("--all", "--new", "HEAD", "fresh.md")
        self.assertIn("grants no access", added,
                      "TEST-PC-39e-new-absent: a file the revision lacks reports every finding in it")

    def test_new_needs_paths(self) -> None:
        rc, _ = self.run_check("--new", "HEAD", cwd=self.repo, env=self.env)
        self.assertNotEqual(rc, 0, "TEST-PC-39f-new-needs-paths: --new with no path was accepted")


class ConfigHeaderTest(ProseCheckTestCase):
    def test_the_width_rule_and_its_exemptions(self) -> None:
        long = "# " + "x" * 75
        _, out = self.run_check("--config-header", self.fixture("TEST-PC-41-header-width.conf", long))
        self.assertIn("header-width [77>72]", out,
                      "TEST-PC-41-header-width: a 77-column comment line is reported at the default width")
        rc, out = self.run_check("--config-header", "--width", "80",
                                 self.fixture("TEST-PC-42-header-width-arg.conf", long))
        self.assertEqual(rc, 0, f"TEST-PC-42-header-width-arg: within an explicit width of 80; output: {out}")
        _, out = self.run_check("--config-header", self.fixture("TEST-PC-180-header-default-mid.conf",
                                                                "# The value Default: names " + "x" * 75))
        self.assertIn("header-width", out,
                      "TEST-PC-180-header-default-mid: a prose line mentioning Default: mid-line is measured")
        for name, lines, description in [
            ("TEST-PC-43-header-default.conf", ["#KEY=" + "v" * 75], "a commented default is not measured"),
            ("TEST-PC-179-header-default-line.conf", ["# Default: [" + "v" * 75 + "]"],
             "a # Default: line states a value, so it is not measured"),
            ("TEST-PC-181-header-values-line.conf", ["# Values: " + "v" * 75],
             "a # Values: line states a value, so it is not measured"),
            ("TEST-PC-182-header-setting.conf", ["KEY=[" + "v" * 75 + "]"],
             "a setting the file ships set is not measured either"),
            ("TEST-PC-44-header-line-end.conf", ["# A session starts only inside a", "# listed directory."],
             "a line's last word is the formatter's business, not this check's"),
            ("TEST-PC-47-header-clean.conf", ["# A session starts only inside", "# a listed directory.", "KEY=value",
                                              "#OTHER=default"],
             "a wrapped header, a setting and a commented default are silent"),
        ]:
            with self.subTest(case_id(name)):
                rc, out = self.run_check("--config-header", self.fixture(name, *lines))
                self.assertEqual(rc, 0, f"{case_id(name)}: {description}; output: {out}")


class PrintWidthTest(ProseCheckTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.fixture("TEST-PC-145-width-document.md", "A page.")
        self.fixture("TEST-PC-148-width-source.sh", "x=1")
        self.fixture("TEST-PC-149-width-header.conf", "# A header.", "KEY=value")
        (self.dir / "TEST-PC-144-binary.webp").write_bytes(b"RIFF\0\0WEBP\n# There is nothing left to check.\n")

    def assertWidthLine(self, case: str, column: str, kind: str, *args: str) -> None:
        _, out = self.run_check("--print-width", *args)
        self.assertRegex(out, re.compile("\t" + re.escape(column) + "\t" + re.escape(kind) + "$", re.MULTILINE),
                         f"{case}: prints {column} {kind}")

    def test_each_kind_with_its_column(self) -> None:
        for case, column, kind, args in [
            ("TEST-PC-145-width-document", "79", "document", ["TEST-PC-145-width-document.md"]),
            ("TEST-PC-146-width-rule", "120", "document", [self.fixture("TEST-PC-146-width-rule.rule.md", "A rule.")]),
            ("TEST-PC-147-width-router", "120", "document", [self.fixture("width-router/CLAUDE.md", "A router.")]),
            ("TEST-PC-148-width-source", "120", "source", ["TEST-PC-148-width-source.sh"]),
            ("TEST-PC-149-width-header", "72", "header", ["--config-header", "TEST-PC-149-width-header.conf"]),
            ("TEST-PC-150-width-man", "-", "man", [self.fixture("TEST-PC-150-width-man.1", ".TH X 1")]),
            ("TEST-PC-151-width-generated", "-", "generated",
             [self.fixture("TEST-PC-151-width-generated.md", "<!-- prose-check: ignore-file -->", "Copied text.")]),
            ("TEST-PC-152-width-binary", "-", "binary", ["TEST-PC-144-binary.webp"]),
            ("TEST-PC-153-width-override-document", "60", "document",
             ["--width", "60", "TEST-PC-145-width-document.md"]),
            ("TEST-PC-154-width-override-source", "60", "source", ["--width", "60", "TEST-PC-148-width-source.sh"]),
            ("TEST-PC-155-width-prose", "79", "document", ["--prose", "TEST-PC-149-width-header.conf"]),
        ]:
            with self.subTest(case):
                self.assertWidthLine(case, column, kind, *args)

    def test_a_missing_path_fails_the_run_and_the_others_still_print(self) -> None:
        rc, out = self.run_check("--print-width", "TEST-PC-156-absent.md", "TEST-PC-145-width-document.md")
        self.assertIn("TEST-PC-156-absent.md\t-\tmissing", out,
                      "TEST-PC-156-width-missing: names a path it cannot read")
        self.assertEqual(rc, 1, f"TEST-PC-156-width-missing: a missing path fails the run; output: {out}")
        self.assertIn("79\tdocument", out, "TEST-PC-156-width-missing: the other paths are still printed")


LONG_MD = "word " * 25
MEDIUM_MD = "word " * 19
WIDE_TOKEN = "p" * 90
WIDE_SPAN = "`" + "word " * 18 + "end`"


class WrapTest(ProseCheckTestCase):
    WRAP = ("--wrap",)

    def test_line_rules_are_off_by_default(self) -> None:
        self.assertSilent("TEST-PC-48a-wrap-off-by-default.sh", "KEY=1",
                          "# The helper reads the list from the operator, the",
                          "# one whose allowlist covers the path.")

    def test_source_comment_width(self) -> None:
        self.assertCases([
            ("comment-width", "TEST-PC-55-comment-width.sh", "x=1", "# " + "w" * 125),
            # A plain `##` comment is prose; a SELinux interface's XML documentation is the policy tools'.
            ("comment-width", "TEST-PC-172-comment-double-hash.if", "## " + "w" * 125),
        ], [
            # Where a comment line breaks is the formatter's.
            ("TEST-PC-49-comment-line-end.sh", "KEY=1", "# The helper reads the list from the operator, the",
             "# one whose allowlist covers the path."),
            ("TEST-PC-50-comment-line-end-docstring.py", "def f():", '    """Return the rows of', '    the table."""'),
            ("TEST-PC-56-comment-width-under.sh", "x=1", "# " + "w" * 110),
            ("TEST-PC-58-comment-directive.sh", "x=1",
             "# shellcheck disable=SC2154  # set by the sourced library, whose contract names the", "y=2"),
            ("TEST-PC-171-comment-xml-doc.if", "## <summary>" + "w" * 125 + "</summary>"),
        ], options=self.WRAP)
        _, out = self.run_check("--wrap", "--width", "100",
                                self.fixture("TEST-PC-57-comment-width-arg.sh", "x=1", "# " + "w" * 110))
        self.assertIn("comment-width [112>100]", out,
                      "TEST-PC-57-comment-width-arg: --width lowers the column a source comment is measured against")

    def test_document_width_and_the_units_a_wrap_cannot_break(self) -> None:
        self.assertCases([
            ("document-width", "TEST-PC-59-document-width.md", "# Title", LONG_MD),
            ("document-width", "TEST-PC-161-document-width-three-tokens.md", "read at " + WIDE_TOKEN),
            ("document-width", "TEST-PC-174-document-width-span-third-unit.md", "read at " + WIDE_SPAN),
            ("document-width", "TEST-PC-164-document-width-quoted-prose.md", "> ```", "> code", "> ```",
             "> " + LONG_MD),
            ("document-width", "TEST-PC-166-document-width-list-continuation.md", "- An item:", "", "    " + LONG_MD),
            ("document-width", "TEST-PC-170-document-width-after-comment.md", "<!-- a note", "     ends -->", LONG_MD),
            ("document-width", "TEST-PC-178-document-width-after-link-definition.md", "[a]: docs/a.md", "", LONG_MD),
            ("document-width", "TEST-PC-158-document-width-after-frontmatter.md", "---", "name: x", "---", LONG_MD),
        ], [
            ("TEST-PC-60-document-width-under.md", "# Title", "word " * 14),
            ("TEST-PC-61-document-width-table.md", "| a | b |", "|---|---|", "| " + "cell " * 25 + " | x |"),
            ("TEST-PC-62-document-width-fence.md", "```", LONG_MD, "```", "After the fence."),
            ("TEST-PC-63-document-width-url.md", "See https://example.invalid/" + "p" * 100 + " for the reference."),
            ("TEST-PC-64-document-width-token.md", "p" * 110),
            ("TEST-PC-65-document-width-man.1", ".TH X 1", LONG_MD),
            ("TEST-PC-159-document-width-heading.md", "# " + LONG_MD, "Body."),
            ("TEST-PC-160-document-width-two-tokens.md", "at " + WIDE_TOKEN),
            ("TEST-PC-173-document-width-span-unit.md", "at " + WIDE_SPAN),
            ("TEST-PC-162-document-width-quoted-table.md", "> | " + "cell " * 25 + " | x |"),
            ("TEST-PC-163-document-width-quoted-fence.md", "> ```", "> " + LONG_MD, "> ```"),
            ("TEST-PC-165-document-width-indented-code.md", "A command:", "", "    " + LONG_MD),
            ("TEST-PC-167-document-width-nested-fence.md", "~~~markdown", "```bash", LONG_MD, "```", "~~~"),
            ("TEST-PC-169-document-width-comment.md", "<!-- " + LONG_MD, "     " + LONG_MD + " -->"),
            ("TEST-PC-175-document-width-link-definition.md", "[a]: docs/a.md", "[b]: docs/b.md",
             "[c]: " + LONG_MD.replace(" ", "-")),
            ("TEST-PC-157-document-width-frontmatter.md", "---", "description: " + LONG_MD, "---", "Body."),
            # The parenthesised part of a label link is generated.
            ("TEST-PC-75-document-width-label-link.md", "word " * 8 + "[ref-section-y4v2](../../src/usr/share/ai-tools/"
             "skills/ai-tools-technical-docs/SKILL.md#ref-section-y4v2) ends."),
        ], options=self.WRAP)
        _, out = self.run_check("--wrap", "--width", "60",
                                self.fixture("TEST-PC-66-document-width-arg.md", "# Title", MEDIUM_MD))
        self.assertIn("document-width [94>60]", out,
                      "TEST-PC-66-document-width-arg: --width lowers the column a document line is measured against")

    def test_a_nested_fence_holds_its_sentence_as_code(self) -> None:
        self.assertSilent("TEST-PC-168-nested-fence-sentence.md", "~~~markdown", "```bash",
                          "There is nothing left to check.", "```", "~~~")

    def test_a_link_definition_block_is_not_prose_and_the_prose_after_it_is(self) -> None:
        self.assertSilent("TEST-PC-176-link-definition-block.md", "Prose naming [the guide][a] and [the other][b].", "",
                          "[a]: docs/project-lifecycle.md", "[b]: docs/naming-conventions.md",
                          "[c]: /opt/ai-tools/bin/ai-tools-run")
        self.assertReports("bare-path", "TEST-PC-177-prose-after-link-definition.md", "[a]: docs/a.md",
                           "[b]: docs/b.md", "", "The helper reads docs/project-lifecycle.md as prose.")

    def test_the_reader_decides_the_column(self) -> None:
        self.assertReports("document-width", "TEST-PC-76-document-width-human.md", "# Title", MEDIUM_MD,
                           options=self.WRAP)
        self.assertSilent("TEST-PC-77-document-width-rule.rule.md", "# Title", MEDIUM_MD, options=self.WRAP)
        rc, out = self.run_check("--wrap", self.fixture("router/CLAUDE.md", "# Title", MEDIUM_MD))
        self.assertEqual(rc, 0, f"TEST-PC-78-document-width-router: the router takes the agent column; output: {out}")
        rc, out = self.run_check("--wrap", self.fixture("skills/SKILL.md", "# Title", MEDIUM_MD))
        self.assertEqual(rc, 0, f"TEST-PC-79-document-width-skill: a page under skills/ takes the agent column; "
                                f"output: {out}")
        _, out = self.run_check("--wrap", self.fixture("skills/SKILL.md", "# Title", LONG_MD))
        self.assertIn("document-width [124>120]", out,
                      "TEST-PC-80-document-width-agent-over: the agent column is 120, not unlimited")


if __name__ == "__main__":
    unittest.main()
