"""Offline behavior tests: no GitHub mutation or model calls."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills/lead-agent-workflow/scripts"
spec = importlib.util.spec_from_file_location("task", SCRIPTS / "task.py")
task = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task)
SHA = "a" * 40


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.policy = self.run / "policy.json"
        self.set_policy(["build"], [])

    def set_policy(self, expected, skipped):
        self.policy.write_text(json.dumps(dict(expected=expected, allow_skipped=skipped)))

    def command(self, script, *args, env=None, input=None):
        return subprocess.run(["bash", str(SCRIPTS / script), *map(str, args)], input=input,
                              text=True, capture_output=True, env={**os.environ, **(env or {})})

    def brief(self, task_id="T1", role="coder"):
        result = self.command("task.sh", "brief", "create", self.run, task_id, role)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(result.stdout.strip())
        return path

    def filled_brief(self, task_id="T1", role="coder"):
        path = self.brief(task_id, role)
        content = re.sub(r"\{\{[^}]+\}\}", "Concrete criteria", path.read_text())
        content = re.sub(r"## Read\n\n.*?\n\n", f"## Read\n\n- {path} — criteria\n\n", content, flags=re.S)
        path.write_text(content)
        return path

    def row(self, name, outcome="accepted"):
        brief = self.filled_brief(name)
        report = self.run / "reports" / f"{name}-coder.md"
        report.write_text("DONE revision 1; evidence\n")
        row = {c: "-" for c in task.COLUMNS}
        row.update(Task=name, Parent=task.parent(name), Phase="reported", Outcome=outcome,
                   Owner="coder:correct-id", Head=SHA, Brief=str(brief.relative_to(self.run)),
                   Report=str(report.relative_to(self.run)), Next="verify integration; wake")
        return row

    def ledger(self, rows):
        path = self.run / "ledger.md"
        path.write_text("# Ledger\n\n## Active tasks\n" + task.table(task.COLUMNS, rows) +
                        "\n\n## Decisions\n- T1-D1 active; applies to T2; reports/T1-advisor.md\n")
        return path

    def test_brief_scaffolds_all_roles_and_refuses_overwrite(self):
        for role in task.SECTIONS:
            with self.subTest(role=role):
                path = self.filled_brief("T4.2", role)
                before = path.read_bytes()
                checked = self.command("task.sh", "brief", "check", path)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                duplicate = self.command("task.sh", "brief", "create", self.run, "T4.2", role)
                self.assertNotEqual(duplicate.returncode, 0)
                self.assertEqual(path.read_bytes(), before)

    def test_placeholder_missing_source_output_revision_and_section(self):
        path = self.brief()
        self.assertNotEqual(self.command("task.sh", "brief", "check", path).returncode, 0)
        base = re.sub(r"\{\{[^}]+\}\}", "Concrete criteria", path.read_text())
        base = re.sub(r"## Read\n\n.*?\n\n", f"## Read\n\n- {path} — criteria\n\n", base, flags=re.S)
        for content in [base.replace("Revision: 1", "Revision: 0"),
                        base.replace("Report: /", "Report: relative/"),
                        base.replace(str(path) + " —", "/missing/file —"),
                        base.replace("## User request", "## Wrong section"),
                        base.replace("Task: T1", "Task: ../T1"),
                        base.replace("Parent: -", "Parent: T2")]:
            path.write_text(content)
            self.assertNotEqual(self.command("task.sh", "brief", "check", path).returncode, 0)

    def test_bad_arguments_and_ids_do_not_escape(self):
        for args in [("brief", "create", self.run, "../T1", "coder"),
                     ("brief", "create", self.run, "T0", "coder"),
                     ("brief", "create", self.run, "T1", "unknown"), ("archive", self.run), ()]:
            self.assertNotEqual(self.command("task.sh", *args).returncode, 0)

    def test_archive_child_preserves_references_decisions_and_parent(self):
        parent = self.row("T1", "-")
        child = self.row("T1.1")
        path = self.ledger([parent, child])
        result = self.command("task.sh", "archive", self.run, "T1.1")
        self.assertEqual(result.returncode, 0, result.stderr)
        first = path.read_bytes()
        _, rows, suffix = task.ledger(path.read_text())
        self.assertEqual([r["Task"] for r in rows], ["T1"])
        self.assertIn("archived T1.1", rows[0]["Next"])
        self.assertIn("T1-D1 active; applies to T2", suffix)
        self.assertTrue((self.run / child["Brief"]).exists())
        self.assertTrue((self.run / child["Report"]).exists())
        task.archive(self.run, "T1.1")
        self.assertEqual(path.read_bytes(), first)
        self.assertEqual((self.run / "archive/T1.md").read_text().count("## T1.1\n"), 1)
        self.assertIn(SHA, (self.run / "archive/index.md").read_text())
        # Archive parent later; child history/index remains available for dependencies.
        rows[0]["Outcome"] = "accepted"
        self.ledger(rows)
        task.archive(self.run, "T1")
        self.assertEqual(len(task.ledger(path.read_text())[1]), 0)
        self.assertIn("T1.1", (self.run / "archive/index.md").read_text())

    def test_archive_rejects_live_descendant_blocked_or_missing_record(self):
        rows = [self.row("T1"), self.row("T1.1"), self.row("T1.1.1", "-")]
        path = self.ledger(rows)
        original = path.read_bytes()
        with self.assertRaises(ValueError):
            task.archive(self.run, "T1")
        self.assertEqual(path.read_bytes(), original)
        rows[-1]["Outcome"] = "accepted"
        rows[-1]["Block"] = "missing access"
        self.ledger(rows)
        with self.assertRaises(ValueError):
            task.archive(self.run, "T1")
        rows[-1]["Block"] = "-"
        rows[-1]["Report"] = "missing.md"
        self.ledger(rows)
        with self.assertRaises(ValueError):
            task.archive(self.run, "T1")

    def test_archive_all_terminal_outcomes_without_claiming_merge(self):
        rows = [self.row("T1")] + [self.row(f"T1.{n}", outcome) for n, outcome in enumerate(sorted(task.OUTCOMES), 1)]
        path = self.ledger(rows)
        task.archive(self.run, "T1")
        self.assertEqual(task.ledger(path.read_text())[1], [])
        index = (self.run / "archive/index.md").read_text()
        for outcome in task.OUTCOMES:
            self.assertIn(outcome, index)

    def test_archive_interruption_after_each_write_is_repeatable(self):
        for boundary in (1, 2, 3):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                # Use a distinct run per simulated crash, preserving the actual completed writes.
                original_run = self.run
                self.run = Path(temporary)
                try:
                    self.ledger([self.row("T1"), self.row("T1.1")])
                    real_atomic = task.atomic
                    calls = 0

                    def interrupted(path, content):
                        nonlocal calls
                        real_atomic(path, content)
                        calls += 1
                        if calls == boundary:
                            raise OSError("simulated interruption")

                    with patch.object(task, "atomic", interrupted), self.assertRaises(OSError):
                        task.archive(self.run, "T1")
                    task.archive(self.run, "T1")
                    self.assertEqual(task.ledger((self.run / "ledger.md").read_text())[1], [])
                    history = (self.run / "archive/T1.md").read_text()
                    self.assertEqual(history.count("## T1\n"), 1)
                    self.assertEqual(history.count("## T1.1\n"), 1)
                finally:
                    self.run = original_run

    def test_archive_conflicting_retry_and_malformed_ledger_fail_without_loss(self):
        row = self.row("T1")
        path = self.ledger([row])
        real_atomic = task.atomic

        def interrupted(destination, content):
            real_atomic(destination, content)
            raise OSError("stop after history")

        with patch.object(task, "atomic", interrupted), self.assertRaises(OSError):
            task.archive(self.run, "T1")
        row["Outcome"] = "cancelled"
        self.ledger([row])
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            task.archive(self.run, "T1")
        self.assertEqual(before, path.read_bytes())
        path.write_text(path.read_text().replace("| Parent |", "| Wrong |"))
        before = path.read_bytes()
        result = self.command("task.sh", "archive", self.run, "T1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, path.read_bytes())

    def test_malformed_archive_index_preserves_active_tasks(self):
        path = self.ledger([self.row("T1")])
        (self.run / "archive").mkdir()
        (self.run / "archive/index.md").write_text("# Unrecognized index\n")
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            task.archive(self.run, "T1")
        self.assertEqual(before, path.read_bytes())
        self.assertFalse((self.run / "archive/T1.md").exists())

    def test_helper_lock_prevents_concurrent_writes(self):
        with (self.run / ".task.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = self.command("task.sh", "brief", "create", self.run, "T1", "coder")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.run / "briefs/T1-coder.md").exists())

    def classify(self, checks):
        return self.command("pr-ci.sh", "1", "--policy", self.policy,
                            env={"PR_CI_CLASSIFY_ONLY": "1"}, input=json.dumps(checks))

    def test_ci_classification(self):
        cases = [([], "NO_RUN"), ([dict(name="build", bucket="pass")], "GREEN"),
                 ([dict(name="build", bucket="pending")], "PENDING"),
                 ([dict(name="build", bucket="pass"), dict(name="external", bucket="fail")], "RED"),
                 ([dict(name="build", bucket="pass"), dict(name="other", bucket="cancel")], "RED"),
                 ([dict(name="build", bucket="cancel")], "RED"),
                 ([dict(name="external", bucket="pass")], "NO_RUN"),
                 ([dict(name="build", bucket="skipping")], "NO_RUN")]
        for checks, want in cases:
            with self.subTest(checks=checks):
                result = self.classify(checks)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.startswith(want), result.stdout)
        self.set_policy(["build", "lint"], ["lint"])
        result = self.classify([dict(name="build", bucket="pass"), dict(name="lint", bucket="skipping")])
        self.assertTrue(result.stdout.startswith("GREEN"), result.stdout)
        self.assertTrue(self.classify([dict(name="build", bucket="pass")]).stdout.startswith("NO_RUN"))

    def test_ci_malformed_and_ambiguous_evidence_is_error(self):
        for checks in [{}, [dict(name="build", bucket="unknown")], [dict(bucket="pass")],
                       [dict(name="build", bucket="pass"), dict(name="build", bucket="pass")]]:
            self.assertEqual(self.classify(checks).returncode, 4)
        self.policy.write_text('{"expected":[]}')
        self.assertEqual(self.classify([]).returncode, 4)

    def mock_github(self, **changes):
        state = dict(head=SHA, after_head=SHA, isDraft=False, state="OPEN", mergeable="MERGEABLE",
                     runs=[dict(name="build", status="completed", conclusion="success", html_url="check")],
                     statuses=[], error="", raw=False)
        state.update(changes)
        fixture = self.run / "github.json"
        fixture.write_text(json.dumps(state))
        executable = self.run / "gh"
        executable.write_text('''#!/usr/bin/env python3
import json, pathlib, sys
p = pathlib.Path(__file__).parent
s = json.loads((p / 'github.json').read_text())
if sys.argv[1:3] == ['pr', 'view']:
    count = p / 'reads'
    n = int(count.read_text()) if count.exists() else 0
    count.write_text(str(n + 1))
    if s['error'] == 'info' or (n and s['error'] == 'after'): sys.exit(1)
    print(json.dumps(dict(state=s['state'], isDraft=s['isDraft'], mergeable=s['mergeable'], headRefOid=s['head'] if not n else s['after_head'])))
elif sys.argv[1] == 'api':
    which = 'runs' if 'check-runs?' in sys.argv[-1] else 'statuses'
    if s['error'] == which: sys.exit(1)
    if s['raw']: print('{}')
    else: print(json.dumps([{'check_runs' if which == 'runs' else 'statuses': s[which]}]))
else: sys.exit(99)
''')
        executable.chmod(0o755)
        (self.run / "reads").unlink(missing_ok=True)
        return {"PATH": str(self.run) + os.pathsep + os.environ["PATH"]}

    def test_ci_live_adapter_queries_current_sha_and_all_sources(self):
        cases = [({}, 0, "GREEN"),
                 ({"statuses": [dict(context="scanner", state="failure", target_url="scanner")]}, 1, "RED"),
                 ({"runs": [dict(name="build", status="completed", conclusion="cancelled")]}, 1, "RED"),
                 ({"runs": []}, 2, "NO_RUN"),
                 ({"after_head": "b" * 40}, 3, "PENDING head-changed"),
                 ({"mergeable": "UNKNOWN"}, 3, "PENDING"),
                 ({"isDraft": True}, 2, "DRAFT"),
                 ({"state": "MERGED"}, 0, "MERGED"),
                 ({"raw": True}, 4, "ERROR")]
        for fixture, code, verdict in cases:
            with self.subTest(fixture=fixture):
                result = self.command("pr-ci.sh", "1", "--policy", self.policy, env=self.mock_github(**fixture))
                self.assertEqual(result.returncode, code, result.stderr + result.stdout)
                self.assertIn(verdict, result.stdout)
                self.assertIn(SHA, result.stdout)
        for endpoint in ("info", "runs", "statuses", "after"):
            with self.subTest(endpoint=endpoint):
                result = self.command("pr-ci.sh", "1", "--policy", self.policy,
                                      env=self.mock_github(error=endpoint))
                self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
                self.assertIn("ERROR", result.stdout)


if __name__ == "__main__":
    unittest.main()
