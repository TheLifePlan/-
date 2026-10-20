"""WS must start with the shared band and the 3-commander order; files and an isolated tmux only."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[1] / 'wsl'
LEAD = ['WSCD01', 'WSCL01', 'WSGR01']
# The state found after the 2026-10-21 reboot: studio.sh started the server from this file.
OLD_STUDIO = 'CONFIG=${WS_TMUX_CONFIG:-$HOME/ai/builder/tmux.conf}\n'
OLD_CONFIG = "set -g base-index 0\nset -g status-left '[WS] '\nbind -n Home select-window -t '=win:=WSMENU メニュー'\n"


def regressions(studio, config, table):
    """Reasons WS would boot into the old plain band / menu-window layout."""
    found = []
    default = re.search(r'^CONFIG=\$\{WS_TMUX_CONFIG:-([^}]+)\}', studio, re.M)
    if not default or default.group(1) != '$HOME/.tmux.conf':
        found.append('studio-default-config')
    if 'tmux-terminal-config.py' not in config or not re.search(r'^set -g base-index 1$', config, re.M):
        found.append('config-not-shared')
    if 'MENU' in config or re.search(r'\bHome\b', config):
        found.append('config-menu-window')
    rows = [line.split('|', 2)[:2] for line in table.splitlines() if line and not line.startswith('#')]
    if any(name.split(' ')[0].endswith('MENU') for _, name in rows):
        found.append('table-menu-window')
    if [name.split(' ')[0] for number, name in rows[:3]] != LEAD or [n for n, _ in rows[:3]] != ['1', '2', '3']:
        found.append('table-commanders-not-left')
    return found


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace('-', '_'), path)
    value = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(value)
    finally:
        sys.path.remove(str(path.parent))
    return value


class WsCommonBandTests(unittest.TestCase):
    def kit(self):
        return ((KIT / 'bin/studio.sh').read_text(), (KIT / 'builder/tmux.conf').read_text(),
                (KIT / 'builder/windows.conf.ws').read_text())

    def test_kit_boots_shared_band_with_commanders_left(self):
        self.assertEqual(regressions(*self.kit()), [])

    def test_old_reboot_state_is_detected(self):
        studio, config, table = self.kit()
        old_table = '0|WSMENU メニュー|$HOME/ai|menu\n' + table.replace('1|WSCD01', '7|WSCD01')
        self.assertIn('studio-default-config', regressions(OLD_STUDIO, config, table))
        found = regressions(studio, OLD_CONFIG, old_table)
        for reason in ('config-not-shared', 'config-menu-window', 'table-menu-window', 'table-commanders-not-left'):
            self.assertIn(reason, found)

    def test_preset_fkeys_home_and_no_menu_window(self):
        config = module(KIT / 'bin/tmux-terminal-config.py')
        preset = config.preset('WS', 'win', 'win')
        self.assertEqual([preset['fkeys'][k]['window'] for k in ('F1', 'F5', 'F9')],
                         ['WSCD01 Codexコマンダー', 'WSCL01 Claudeコマンダー', 'WSGR01 Grokコマンダー'])
        self.assertEqual(preset['home'], 'WSCD01 Codexコマンダー')
        self.assertNotIn('MENU', json.dumps(preset['fkeys'], ensure_ascii=False))
        rows = config.commands(preset, Path('/fixture'), '/usr/bin/python3', version='3.6')
        self.assertIn(['bind-key', '-n', 'Home', 'select-window', '-t', '=win:=WSCD01 Codexコマンダー'], rows)

    def test_work_menu_routes_input_and_check_to_separate_desks(self):
        rows = [line.split('\t') for line in (KIT / 'builder/work-menu.tsv').read_text().splitlines()
                if line and not line.startswith('#')]
        self.assertTrue(all(len(row) == 3 and row[1] in ('hands', 'all', 'note') for row in rows))
        hands = {row[2] for row in rows if row[1] == 'hands'}
        self.assertTrue({'42', '03'} <= hands)
        self.assertEqual(sum(row[1] == 'all' for row in rows), 1)
        self.assertNotIn('MENU', ''.join(''.join(row) for row in rows))

    def test_setup_places_shared_root_config_only_when_missing(self):
        # A fresh WS must not boot without ~/.tmux.conf; an existing one is kept as is.
        line = next(l for l in (KIT / 'setup-ws.sh').read_text().splitlines() if '"$HOME/.tmux.conf"' in l and 'install' in l)
        self.assertNotIn('ai/builder/tmux.conf"', line.split('install', 1)[0])
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            for case in ('missing', 'existing', 'link'):
                home = base / case; home.mkdir()
                if case == 'existing': (home / '.tmux.conf').write_text('# own\n')
                if case == 'link': (home / 'own.conf').write_text('# own\n'); (home / '.tmux.conf').symlink_to(home / 'own.conf')
                subprocess.run(['bash', '-c', line], env={'HOME': str(home), 'KIT': str(KIT), 'PATH': '/usr/bin:/bin'}, check=True)
                text = (home / '.tmux.conf').read_text()
                if case == 'missing':
                    self.assertEqual(text, (KIT / 'builder/tmux.conf').read_text())
                    self.assertEqual(regressions((KIT / 'bin/studio.sh').read_text(), text, (KIT / 'builder/windows.conf.ws').read_text()), [])
                else:
                    self.assertEqual(text, '# own\n')
                self.assertEqual((home / '.tmux.conf').is_symlink(), case == 'link')

    def test_isolated_server_from_kit_config_gets_shared_band(self):
        tmux = shutil.which('tmux')
        if not tmux:
            self.skipTest('tmux missing')
        sock = 'ws-band-' + uuid.uuid4().hex[:8]
        with tempfile.TemporaryDirectory() as td:
            home = Path(td).resolve(); (home / 'ai/bin').mkdir(parents=True)
            for name in ('hq_head.py', 'tmux-terminal-config.py', 'tmux-head-status-v3.py', 'tmux-desk-menu.py'):
                shutil.copyfile(KIT / 'bin' / name, home / 'ai/bin' / name)
            preset = module(KIT / 'bin/tmux-terminal-config.py').preset('WS', sock, 'win')
            (home / 'ai/terminal.conf').write_text(json.dumps(preset, ensure_ascii=False))
            env = {'HOME': str(home), 'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin', 'TERM': 'xterm'}
            run = lambda *a: subprocess.run([tmux, '-L', sock, *a], env=env, capture_output=True, text=True, timeout=20)
            try:
                self.assertEqual(run('-f', str(KIT / 'builder/tmux.conf'), 'new-session', '-d', '-s', 'win', 'sleep 30').returncode, 0)
                for _ in range(50):
                    if 'tmux-head-status-v3' in run('show', '-gv', 'status-format[0]').stdout: break
                    subprocess.run(['sleep', '0.1'])
                self.assertIn('tmux-head-status-v3', run('show', '-gv', 'status-format[0]').stdout)
                self.assertEqual(run('show', '-gv', 'base-index').stdout.strip(), '1')
                keys = run('list-keys', '-T', 'root').stdout
                self.assertIn('=win:=WSCD01 Codex', keys); self.assertIn('root Home', ' '.join(keys.split())); self.assertNotIn('WSMENU', keys)
            finally:
                run('kill-server')


if __name__ == '__main__':
    unittest.main()
