# SPDX-License-Identifier: MIT
"""Unit tests for scripts/ref-index.py, the cross-reference tool this skill ships.

A reference names a reftag and the reftag resolves to where its target now is, so a target that
moved, was renamed, or was deleted is reported, never left cited at its old place. Each finding
`check` makes is driven with a fixture it must report and with the corrected form it must stay
silent on; `relink`, `generate`, `new`, `kinds`, `retire` and `where` are held to their output.
"""
# This file holds reftags as fixture text, so a tree-wide check does not read it.
# ref-index: ignore-file

import datetime
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "ref-index.py"

# The fixtures carry a non-ASCII heading, so the tool reads and writes them as UTF-8 whatever the
# host locale.
CHILD_ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

EM_DASH = "\u2014"
MIDDLE_DOT = "\u00b7"


class RefIndexCase(unittest.TestCase):
    """Runs the tool from inside a fresh temporary directory, so a `file:line` report carries the
    fixture's relative path."""

    maxDiff = None

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def fixture(self, path, *lines):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(line + "\n" for line in lines), encoding="utf-8")

    def read(self, path):
        return (self.root / path).read_text(encoding="utf-8")

    def run_ri(self, *args):
        """(status, stdout and stderr together), as the shell harness read them."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args], cwd=str(self.root),
            capture_output=True, text=True, encoding="utf-8", env=CHILD_ENV)
        return result.returncode, result.stdout + result.stderr

    def assertReports(self, finding, *paths):
        rc, out = self.run_ri("check", *paths)
        self.assertRegex(out, re.compile(r"^[^:]*:[0-9]*: " + re.escape(finding) + " ", re.M),
                         "check did not report %s" % finding)
        return out

    def assertSilent(self, *paths):
        rc, out = self.run_ri("check", *paths)
        self.assertEqual((rc, out), (0, ""), "check reported a finding")

    def assertLine(self, line, text):
        self.assertIn(line, text.splitlines())

    # Shared fixtures: a section and a table target in docs/a.md, cited from docs/b.md, and a
    # function and message target in src/s.sh, cited from a comment, a document and a test.

    def write_section_targets(self):
        self.fixture(
            "docs/a.md", "# Doc A", "", '## Two project models <a id="ref-section-a1b2"></a>', "",
            "Text.", "", '<a id="ref-table-c3d4"></a>**Altitudes and who owns which fact**', "",
            "| a | b |", "|---|---|", "| 1 | 2 |", "",
            "## Security model %s what `SANDBOX_USER` can do" % EM_DASH, "", "More.")
        self.fixture(
            "docs/b.md", "# Doc B", "",
            "The owner rule [ref-section-a1b2](a.md#ref-section-a1b2) and the table "
            "[ref-table-c3d4](a.md#ref-table-c3d4).",
            "Navigation [What SANDBOX_USER can do](a.md#security-model--what-sandbox_user-can-do) "
            "and [Doc A](a.md).")

    def write_code_targets(self):
        self.fixture(
            "src/s.sh", "#!/usr/bin/env bash", "# FN-K1L2: chown_path", "# args: $1 path",
            "chown_path() {", '    die MSG-M3N4 "not in allowed projects: $1"', "}",
            "other() { :; }")
        self.fixture("src/t.sh", "# The refusal is MSG-M3N4, driven in the unit test; see FN-K1L2.")
        self.fixture(
            "docs/code.md", "The helper [FN-K1L2](../src/s.sh) prints [MSG-M3N4](../src/s.sh).", "",
            '[URI-O5P6]: https://example.invalid/spec "The spec"', "",
            "The spec [URI-O5P6](https://example.invalid/spec).")
        # A test cites the code beside the output it captured: the quoted string opens with an
        # expansion, does not name a message, and reads as a reference.
        self.fixture(
            "tests/s.sh", 'out="$(chown_path /x 2>&1)"',
            'assert_msg MSG-M3N4 "${out}" "refuses a path outside the allowlist"')

    def write_index(self):
        self.write_section_targets()
        self.write_code_targets()
        return self.run_ri("generate", "docs/a.md", "docs/b.md", "src/s.sh", "src/t.sh",
                           "docs/code.md", "tests/s.sh", "--out", "index.md")


class SectionTargetTest(RefIndexCase):

    def test_section_and_caption_cited_with_generated_destination_is_silent(self):
        self.write_section_targets()
        self.assertSilent("docs/a.md", "docs/b.md")


class DuplicateTest(RefIndexCase):

    def test_reftag_defined_twice_is_reported(self):
        self.write_section_targets()
        self.fixture("docs/dup.md", '## Another <a id="ref-section-a1b2"></a>')
        self.assertReports("duplicate", "docs/a.md", "docs/b.md", "docs/dup.md")

    def test_id_shared_across_kinds_is_reported(self):
        self.write_section_targets()
        self.fixture("docs/dupid.md", '<a id="ref-table-a1b2"></a>**Another table**', "",
                     "| a |", "|---|")
        self.assertReports("duplicate-id", "docs/a.md", "docs/dupid.md")


class UndefinedAndSameFileTest(RefIndexCase):

    def test_reference_without_target_is_reported(self):
        self.write_section_targets()
        self.fixture("docs/undef.md", "See [ref-section-z9z9](a.md#ref-section-z9z9).")
        self.assertReports("undefined", "docs/a.md", "docs/undef.md")

    def test_same_file_reference_is_reported_with_the_jump_link_to_use(self):
        self.fixture("docs/self.md", '## Own section <a id="ref-section-e5f6"></a>', "",
                     "See [ref-section-e5f6](#ref-section-e5f6).")
        out = self.assertReports("same-file", "docs/self.md")
        self.assertIn("[Own section](#own-section)", out)


class MisplacedCaptionTest(RefIndexCase):
    """A listing's caption sits before a fence and a table's before a table row; any other kind's
    caption sits before whatever block follows it."""

    def test_listing_caption_before_prose_is_reported(self):
        self.fixture("docs/orphan.md", '<a id="ref-listing-g7h8"></a>**A listing**', "",
                     "Prose, not a fence.")
        self.assertReports("misplaced", "docs/orphan.md")

    def test_listing_caption_before_fence_is_silent(self):
        self.fixture("docs/drawn.md", '<a id="ref-listing-g7h8"></a>**A listing**', "",
                     "```", "code", "```")
        self.assertSilent("docs/drawn.md")

    def test_other_kind_caption_before_any_block_is_silent(self):
        self.fixture("docs/callout.md", '<a id="ref-callout-g7h9"></a>**A note**', "",
                     "> Prose in a quote block.")
        self.assertSilent("docs/callout.md")

    def test_anchor_inside_a_paragraph_is_reported(self):
        self.fixture("docs/loose.md", 'Text <a id="ref-section-g8h0"></a> in a paragraph.')
        self.assertReports("misplaced", "docs/loose.md")


class MissingAndStaleTest(RefIndexCase):

    def test_bare_reftag_is_reported_and_relink_gives_it_its_destination(self):
        self.write_section_targets()
        self.fixture("docs/bare.md", "See [ref-section-a1b2] for the models.")
        self.assertReports("missing", "docs/a.md", "docs/bare.md")
        rc, out = self.run_ri("relink", "docs/a.md", "docs/bare.md")
        self.assertIn("relinked docs/bare.md", out)
        self.assertSilent("docs/a.md", "docs/bare.md")
        self.assertIn("[ref-section-a1b2](a.md#ref-section-a1b2)", self.read("docs/bare.md"))

    def test_moved_target_is_reported_stale_and_relink_corrects_it(self):
        self.write_section_targets()
        self.fixture("docs/stale.md", "See [ref-section-a1b2](old/a.md#ref-section-a1b2).")
        out = self.assertReports("stale", "docs/a.md", "docs/stale.md")
        self.assertIn("[ref-section-a1b2](a.md#ref-section-a1b2)", out)
        self.run_ri("relink", "docs/a.md", "docs/stale.md")
        self.assertSilent("docs/a.md", "docs/stale.md")

    def test_target_moved_into_the_citing_file_is_same_file_and_relink_leaves_it(self):
        self.fixture("docs/moved.md", '## Two project models <a id="ref-section-i9j0"></a>', "",
                     "See [ref-section-i9j0](a.md#ref-section-i9j0).")
        self.assertReports("same-file", "docs/moved.md")
        self.run_ri("relink", "docs/moved.md")
        self.assertIn("a.md#ref-section-i9j0", self.read("docs/moved.md"))


class OrdinaryLinkTest(RefIndexCase):
    """Navigation and file links are checked for resolving and take no reftag. The slug keeps the
    text of a backticked span in a heading."""

    def test_link_to_gone_heading_or_file_is_reported_and_a_resolving_one_is_not(self):
        self.write_section_targets()
        self.fixture("docs/nav.md", "# Title", "",
                     "**Contents**: [Requirements](#requirements) %s [Gone](#no-such-heading)"
                     % MIDDLE_DOT,
                     "", "## Requirements", "",
                     "See [missing](nope.md) and [the models](a.md#ref-section-a1b2).")
        out = self.assertReports("link", "docs/a.md", "docs/nav.md")
        self.assertRegex(out, "no-such-heading.*cite its reftag")
        self.assertIn("nope.md does not exist", out)
        self.assertNotRegex(out, "requirements|sandbox_user")


class CodeTargetTest(RefIndexCase):

    def test_code_targets_and_uri_cited_from_document_and_source_are_silent(self):
        self.write_code_targets()
        self.assertSilent("src/s.sh", "src/t.sh", "docs/code.md")

    def test_uri_cited_at_an_old_destination_is_stale(self):
        self.write_code_targets()
        self.fixture("docs/code-stale.md",
                     "The spec [URI-O5P6](https://example.invalid/old) and [FN-K1L2](s.sh).")
        self.assertReports("stale", "src/s.sh", "docs/code.md", "docs/code-stale.md")

    def test_code_cited_with_no_definition_is_undefined(self):
        self.fixture("src/u.sh", "# see FN-Q7R8, which is nowhere")
        self.assertReports("undefined", "src/u.sh")

    def test_message_cited_from_a_test_beside_its_output_is_silent(self):
        self.write_code_targets()
        self.assertSilent("src/s.sh", "tests/s.sh")

    def test_message_cited_in_a_later_argument_is_a_reference(self):
        # Only a command's first argument defines a message, so a parameterised assertion helper
        # naming the code it expects reads as a reference and is listed among the citing files.
        self.write_code_targets()
        self.fixture("tests/param.sh",
                     'refuses "a path outside the allowlist" MSG-M3N4 "not in allowed projects"')
        self.assertSilent("src/s.sh", "tests/param.sh")
        rc, out = self.run_ri("generate", "src/s.sh", "tests/param.sh")
        self.assertLine("| m3n4 | [MSG-M3N4](src/s.sh) | not in allowed projects: $1 | src/s.sh "
                        "| tests/param.sh | die |", out)

    def test_emit_call_continued_onto_the_next_line_defines_its_message(self):
        self.fixture("src/wrapped.sh", "ai_tools_msg_warn MSG-M3N9 \\",
                     '    "The group is an unaudited draft."')
        self.assertSilent("src/wrapped.sh")
        rc, out = self.run_ri("generate", "src/wrapped.sh")
        self.assertLine("| m3n9 | [MSG-M3N9](src/wrapped.sh) | The group is an unaudited draft. "
                        "| src/wrapped.sh |  | ai_tools_msg_warn |", out)

    def test_quote_inside_substitution_or_escaped_does_not_end_the_message(self):
        self.fixture(
            "src/nested.sh",
            "coded_refusal MSG-M3P7 \"declares $(printf '%q' \"${floor}\"), "
            "which is not <major>.<minor>\"",
            'refuse MSG-M3P8 "no agent provides \\"${launcher}\\" -- refusing to launch"')
        rc, out = self.run_ri("generate", "src/nested.sh")
        self.assertLine("| m3p7 | [MSG-M3P7](src/nested.sh) | declares $(printf '%q' \"${floor}\"), "
                        "which is not <major>.<minor> | src/nested.sh |  | coded_refusal |", out)
        self.assertLine("| m3p8 | [MSG-M3P8](src/nested.sh) | no agent provides \\\"${launcher}\\\" "
                        "-- refusing to launch | src/nested.sh |  | refuse |", out)

    def test_message_emitted_twice_is_a_duplicate(self):
        self.write_code_targets()
        self.fixture("src/twice.sh", 'warn MSG-M3N4 "a second situation under the same code"')
        self.assertReports("duplicate", "src/s.sh", "src/twice.sh")

    def test_comment_naming_a_code_with_a_colon_is_a_reference(self):
        self.fixture("src/colon.sh",
                     "# MSG-M3N5: a comment naming a code is a reference, not a message")
        self.assertReports("undefined", "src/colon.sh")


class QuotedTextTest(RefIndexCase):

    def test_fenced_block_and_backticked_span_are_not_read(self):
        self.fixture(
            "docs/quoted.md",
            'Write `[ref-section-z9z9](x.md#ref-section-z9z9)` and '
            '`## H <a id="ref-section-z9z8"></a>`.',
            "", "```", '## Fenced <a id="ref-section-z9z7"></a>',
            "[ref-section-z9z6](x.md#ref-section-z9z6)", "```")
        self.assertSilent("docs/quoted.md")

    def test_quoted_reftag_is_an_example_row_and_not_a_target(self):
        self.fixture("docs/ex.md",
                     'A caption reads `<a id="ref-figure-e9x9"></a>**A figure**` in the grammar.')
        self.fixture("docs/exref.md", "See [ref-figure-e9x9](ex.md#ref-figure-e9x9).")
        self.assertReports("undefined", "docs/ex.md", "docs/exref.md")
        rc, out = self.run_ri("generate", "docs/ex.md")
        self.assertLine("| e9x9 | ref-figure-e9x9 | example | docs/ex.md |  |  |", out)


class GenerateTest(RefIndexCase):

    def test_rows_carry_id_link_name_file_cited_by_and_emitter(self):
        self.write_index()
        index = self.read("index.md")
        self.assertLine("| a1b2 | [ref-section-a1b2](docs/a.md#ref-section-a1b2) | Two project models "
                        "| docs/a.md | docs/b.md |  |", index)
        self.assertLine("| m3n4 | [MSG-M3N4](src/s.sh) | not in allowed projects: $1 | src/s.sh "
                        "| docs/code.md, src/t.sh, tests/s.sh | die |", index)
        self.assertLine("| k1l2 | [FN-K1L2](src/s.sh) | chown_path | src/s.sh "
                        "| docs/code.md, src/t.sh |  |", index)

    def test_rows_follow_file_and_position(self):
        self.write_index()
        lines = self.read("index.md").splitlines()
        positions = [next(number for number, line in enumerate(lines) if token in line)
                     for token in ("ref-section-a1b2", "ref-table-c3d4", "FN-K1L2")]
        self.assertEqual(positions, sorted(positions))

    def test_name_keeps_the_text_of_a_backticked_span(self):
        # A span is blanked before a target is matched, so a reftag in backticks is not read as
        # one; the name is the heading as written.
        heading = "Security model %s what `SANDBOX_USER` can do" % EM_DASH
        self.fixture("docs/span.md", '## %s <a id="ref-section-g9f6"></a>' % heading)
        self.run_ri("generate", "docs/span.md", "--out", "span-index.md")
        self.assertIn("| %s |" % heading, self.read("span-index.md"))

    def test_at_computes_links_from_where_the_index_lives(self):
        self.write_section_targets()
        rc, out = self.run_ri("generate", "--at", "docs/index.md", "docs/a.md")
        self.assertIn("(a.md#ref-section-a1b2)", out)

    def test_pipe_in_a_name_round_trips_through_generate_where_and_retire(self):
        # Raw, a pipe opens a column and shifts every later cell left; `where` resolves the row's
        # FILE cell, so it reports a live line only while the columns hold.
        self.write_section_targets()
        self.fixture("src/pipe.sh",
                     'reject MSG-P1P2 "system bootstrap: unknown scope (--scope minimal|full)"')
        self.run_ri("generate", "src/pipe.sh", "--out", "pipe-index.md")
        self.assertLine("| p1p2 | [MSG-P1P2](src/pipe.sh) | system bootstrap: unknown scope "
                        "(--scope minimal\\|full) | src/pipe.sh |  | reject |",
                        self.read("pipe-index.md"))
        rc, out = self.run_ri("where", "MSG-P1P2", "--index", "pipe-index.md")
        self.assertLine("src/pipe.sh:1 (1 lines) system bootstrap: unknown scope "
                        "(--scope minimal|full)", out)
        self.run_ri("retire", "docs/a.md", "--index", "pipe-index.md",
                    "--retired", "pipe-retired.md", "--release", "0.16.0")
        self.assertIn("| system bootstrap: unknown scope (--scope minimal\\|full) |",
                      self.read("pipe-retired.md"))

    def test_tree_without_reftags_is_a_valid_index(self):
        self.fixture("empty.md")
        rc, out = self.run_ri("generate", "empty.md")
        self.assertEqual(rc, 0, out)
        self.assertNotRegex(out, re.compile(r"^\| \[", re.M))


class NewTest(RefIndexCase):

    def setUp(self):
        super().setUp()
        self.write_index()

    def test_each_family_prints_a_reftag_of_its_form(self):
        # The id is a letter, a digit, a letter, a digit, in the family's case.
        forms = {"section": "ref-section-[a-z][0-9][a-z][0-9]",
                 "table": "ref-table-[a-z][0-9][a-z][0-9]",
                 "fn": "FN-[A-Z][0-9][A-Z][0-9]",
                 "msg": "MSG-[A-Z][0-9][A-Z][0-9]",
                 "uri": "URI-[A-Z][0-9][A-Z][0-9]"}
        for family, form in forms.items():
            with self.subTest(family=family):
                rc, out = self.run_ri("new", family, "--index", "index.md")
                self.assertRegex(out, re.compile("^" + form + "$", re.M))

    def test_kinds_lists_each_kind_and_code_family(self):
        rc, out = self.run_ri("kinds")
        self.assertRegex(out, re.compile(r"^section .*ref-section-<id>", re.M))
        self.assertRegex(out, re.compile(r"^uri .*URI-<ID>", re.M))

    def test_unknown_family_is_refused(self):
        rc, out = self.run_ri("new", "spreadsheet", "--index", "index.md")
        self.assertEqual(rc, 2, out)

    def test_count_prints_that_many_distinct_reftags(self):
        # A mint is recorded nowhere, so each id joins the taken set as it is drawn.
        rc, out = self.run_ri("new", "section", "--count", "12", "--index", "index.md")
        minted = out.splitlines()
        self.assertEqual(len(minted), 12, out)
        self.assertEqual(len(set(minted)), 12, out)

    def test_count_under_one_is_refused(self):
        rc, out = self.run_ri("new", "section", "--count", "0", "--index", "index.md")
        self.assertEqual(rc, 2, out)


class RetireTest(RefIndexCase):
    """A reftag that leaves the tree keeps its id in the retired file, and a target under a
    retired reftag is reported rather than read as a fresh definition."""

    RETIRE_ARGS = ("retire", "docs/a.md", "docs/b.md", "src/t.sh", "docs/code.md",
                   "--index", "index.md", "--retired", "retired.md")

    def setUp(self):
        super().setUp()
        self.write_index()
        # Drawn before the run so a run crossing midnight is not misread.
        self.today = datetime.date.today().isoformat()
        self.rc, self.out = self.run_ri(*self.RETIRE_ARGS, "--release", "0.16.0")

    def test_reftag_the_files_no_longer_define_is_retired_with_date_and_release(self):
        self.assertRegex(self.out, re.compile(r"^retired MSG-M3N4 ", re.M))
        self.assertLine("| m3n4 | MSG-M3N4 | not in allowed projects: $1 | src/s.sh "
                        "| docs/code.md, src/t.sh, tests/s.sh | die | %s | 0.16.0 |" % self.today,
                        self.read("retired.md"))

    def test_second_run_leaves_the_retired_row_as_it_is(self):
        rc, out = self.run_ri(*self.RETIRE_ARGS)
        self.assertEqual((rc, out), (0, ""))
        rows = [line for line in self.read("retired.md").splitlines()
                if line.startswith("| m3n4 ")]
        self.assertEqual(len(rows), 1, rows)

    def test_target_under_a_retired_reftag_is_resurrected(self):
        rc, out = self.run_ri("check", "src/s.sh", "src/t.sh", "docs/code.md", "tests/s.sh",
                              "--retired", "retired.md")
        self.assertRegex(out, re.compile(r"^src/s\.sh:[0-9]*: resurrected \[MSG-M3N4\]", re.M))

    def test_new_reads_the_retired_file_and_still_mints(self):
        rc, out = self.run_ri("new", "msg", "--index", "index.md", "--retired", "retired.md")
        self.assertRegex(out, re.compile(r"^MSG-[A-Z][0-9][A-Z][0-9]$", re.M))


class WhereTest(RefIndexCase):

    def setUp(self):
        super().setUp()
        self.write_index()

    def test_section_spans_to_the_next_heading(self):
        rc, out = self.run_ri("where", "ref-section-a1b2", "--index", "index.md")
        self.assertLine("docs/a.md:3 (10 lines) Two project models", out)

    def test_function_spans_its_doc_comment_and_body(self):
        rc, out = self.run_ri("where", "FN-K1L2", "--index", "index.md")
        self.assertLine("src/s.sh:2 (5 lines) chown_path", out)

    def test_reftag_the_index_lacks_exits_1(self):
        rc, out = self.run_ri("where", "ref-section-z9z9", "--index", "index.md")
        self.assertEqual(rc, 1, out)


class MalformedTest(RefIndexCase):
    """A prefix followed by anything but a four-character id is a reftag no search finds. A code
    line carries the bare prefix as a pattern or a string, and a backticked span or a fence shows
    the shape without being read."""

    def test_short_id_in_prose_is_reported(self):
        self.fixture("docs/short.md", "The owner rule [ref-section-k7q](a.md#x) holds.")
        self.assertReports("malformed", "docs/short.md")

    def test_short_code_family_id_in_a_document_is_reported(self):
        self.fixture("docs/code-short.md", "The refusal prints MSG-12 and stops.")
        self.assertReports("malformed", "docs/code-short.md")

    def test_short_id_in_a_source_comment_is_reported(self):
        self.fixture("src/comment.sh", "#!/usr/bin/env bash",
                     "# The refusal prints MSG-12 and stops.", "true")
        self.assertReports("malformed", "src/comment.sh")

    def test_bare_prefix_on_a_code_line_is_silent(self):
        self.fixture("src/pattern.sh", "#!/usr/bin/env bash",
                     'code_re="MSG-[A-Z][0-9][A-Z][0-9]"', 'prefix="MSG-"', "true")
        self.assertSilent("src/pattern.sh")

    def test_prefix_in_a_span_or_a_fence_is_silent(self):
        self.write_section_targets()
        self.fixture("docs/shown.md",
                     "A code is `MSG-CODE` in a usage line, and `ref-index.py` is the tool.", "",
                     "```text", 'die MSG-CODE "the message"', "```", "",
                     "The owner rule [ref-section-a1b2](a.md#ref-section-a1b2) holds.")
        self.assertSilent("docs/a.md", "docs/shown.md")


if __name__ == "__main__":
    unittest.main()
