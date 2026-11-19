import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import probe  # noqa: E402

probe.log.disabled = True

TAILNET = {"home.feocco.com": ["100.81.237.11"], "reader.home.feocco.com": ["100.120.139.67"]}
LAN = {**TAILNET, "home.feocco.com": ["192.168.1.43"]}


def resolver(table):
    def resolve(hostname):
        if hostname not in table:
            raise OSError("NXDOMAIN")
        return table[hostname]
    return resolve


def fetch_status(status):
    return lambda hostname, address, timeout: status


class Notifications:
    def __init__(self, ok=True):
        self.sent, self.ok = [], ok

    def __call__(self, title, message):
        self.sent.append((title, message))
        return self.ok


class ProbeTest(unittest.TestCase):
    targets = sorted(TAILNET)

    def run_probe(self, table, state, notes, status=200):
        return probe.run_once(self.targets, state, resolver(table), fetch_status(status), notes)

    def test_tailnet_answers_pass_without_alert(self):
        state, notes = probe.State(), Notifications()
        results = self.run_probe(TAILNET, state, notes)
        self.assertTrue(all(r.ok for r in results))
        self.assertEqual(notes.sent, [])

    def test_lan_answer_is_the_failure_mode(self):
        result = probe.check("home.feocco.com", resolver(LAN), fetch_status(200), 1)
        self.assertFalse(result.ok)
        self.assertIn("192.168.1.43", result.detail)

    def test_alerts_after_two_failing_runs_then_all_clear_once(self):
        state, notes = probe.State(), Notifications()
        self.run_probe(LAN, state, notes)
        self.assertEqual(notes.sent, [])
        self.run_probe(LAN, state, notes)
        self.assertEqual(len(notes.sent), 1)
        self.assertIn("home.feocco.com", notes.sent[0][1])
        self.run_probe(LAN, state, notes)
        self.assertEqual(len(notes.sent), 1, "no repeat alert while still failing")
        self.run_probe(TAILNET, state, notes)
        self.assertEqual(len(notes.sent), 2)
        self.assertIn("OK", notes.sent[1][0])
        self.run_probe(TAILNET, state, notes)
        self.assertEqual(len(notes.sent), 2)

    def test_one_failing_run_does_not_alert(self):
        state, notes = probe.State(), Notifications()
        self.run_probe(LAN, state, notes)
        self.run_probe(TAILNET, state, notes)
        self.run_probe(LAN, state, notes)
        self.assertEqual(notes.sent, [])

    def test_server_errors_and_dns_failures_count(self):
        self.assertFalse(probe.check("home.feocco.com", resolver(TAILNET), fetch_status(502), 1).ok)
        self.assertTrue(probe.check("home.feocco.com", resolver(TAILNET), fetch_status(401), 1).ok)
        self.assertFalse(probe.check("missing.home.feocco.com", resolver(TAILNET), fetch_status(200), 1).ok)

        def refused(hostname, address, timeout):
            raise ConnectionRefusedError("refused")

        self.assertFalse(probe.check("home.feocco.com", resolver(TAILNET), refused, 1).ok)

    def test_failed_notify_retries_next_run(self):
        state, notes = probe.State(), Notifications(ok=False)
        for _ in range(3):
            self.run_probe(LAN, state, notes)
        self.assertEqual(len(notes.sent), 2)
        self.assertFalse(state.alerted)

    def test_state_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "state.json"
            probe.State(consecutive_failures=1, alerted=False).save(path)
            state, notes = probe.State.load(path), Notifications()
            self.run_probe(LAN, state, notes)
            self.assertEqual(len(notes.sent), 1)


if __name__ == "__main__":
    unittest.main()
