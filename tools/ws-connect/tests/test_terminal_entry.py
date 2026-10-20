"""Synthetic argv tests. No network, SSH, mosh or private WS hosts file is used."""
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'wsl/bin/terminal-entry'
LOADER = importlib.machinery.SourceFileLoader('terminal_entry', str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e)
SYNTHETIC = ('honsha\t本社\toperator@100.64.0.1\tmain\tstudio-main\tSMCL01\n'
             'koujou\t工場\tfactoryuser@100.64.0.1\tstudio\t-\tSFCL01\n'
             'mini\tミニ\tminiuser@mini-fixture.ts.net\tmini\tmini\tMDCL01\n'
             'book\tBook\tbookuser@100.64.0.3\t-\tbook-session\tBVCL01\n')


class TerminalEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.table = Path(self.tmp.name).resolve() / 'fixture.tsv'
        self.table.write_text(SYNTHETIC)

    def test_four_remote_commands_are_exact_separate_argv(self):
        rows = e.read_hosts(self.table)
        expected = {
            'honsha': ['/opt/homebrew/bin/tmux', '-L', 'main', 'attach', '-t', 'studio-main'],
            'koujou': ['/Users/factoryuser/bin/factory-remote.sh'],
            'mini': ['tmux', '-L', 'mini', 'attach', '-t', 'mini'],
            'book': ['/opt/homebrew/bin/tmux', 'attach', '-t', 'book-session']}
        for place, remote in expected.items():
            command = e.argv_for(place, rows)
            self.assertEqual(command[:6], ['ssh', '-o', 'ConnectTimeout=8', '-o', 'ServerAliveInterval=30', '-t'])
            self.assertEqual(command[6], rows[place]['target'])
            self.assertEqual(command[7:], ['env', 'LANG=ja_JP.UTF-8', 'LC_ALL=ja_JP.UTF-8', *remote])

    def test_mosh_is_explicit_and_missing_mosh_falls_back_to_ssh(self):
        rows = e.read_hosts(self.table)
        self.assertEqual(e.argv_for('mini', rows, mosh=True, which=lambda _: '/bin/mosh')[:3],
                         ['mosh', rows['mini']['target'], '--'])
        self.assertEqual(e.argv_for('mini', rows, mosh=True, which=lambda _: None)[0], 'ssh')

    def test_main_executes_argv_without_shell_and_without_real_network(self):
        calls = []
        with patch.dict(e.os.environ, {'DESK_MOSH': '0'}):
            self.assertEqual(e.main(['koujou', '--hosts', str(self.table)],
                execute=lambda executable, argv: calls.append((executable, argv))), 0)
        self.assertEqual(calls[0][0], 'ssh')
        self.assertEqual(calls[0][1][-1], '/Users/factoryuser/bin/factory-remote.sh')

    def test_duplicate_role_target_injection_and_non_tailscale_ip_are_rejected(self):
        for raw in (SYNTHETIC + SYNTHETIC.splitlines()[0] + '\n',
                    SYNTHETIC.replace('factoryuser@100.64.0.1', 'operator@100.64.0.1'),
                    SYNTHETIC.replace('operator@100.64.0.1', 'operator@host;touch-bad'),
                    SYNTHETIC.replace('operator@100.64.0.1', '-oProxyCommand=bad@host'),
                    SYNTHETIC.replace('operator@100.64.0.1', 'operator@192.0.2.1'),
                    SYNTHETIC.replace('book-session', 'session;bad'),
                    'honsha\t本社\tuser@100.64.0.1\n'):
            with self.subTest(raw=raw):
                self.table.write_text(raw)
                with self.assertRaises(e.Failure):
                    e.read_hosts(self.table)

    def test_symbolic_link_hosts_is_rejected(self):
        link = self.table.with_name('link')
        link.symlink_to(self.table)
        with self.assertRaises(OSError):
            e.read_hosts(link)


if __name__ == '__main__':
    unittest.main()
