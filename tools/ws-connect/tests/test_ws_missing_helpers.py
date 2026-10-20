"""Fake tmux records arguments; no CLI, real session, helper or SSH is started."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

KIT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader('ws_conf_helper_test', str(KIT / 'wsl/bin/ws-windows-conf.py'))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)
HELPERS = ('hisho-codex', 'hisho-leader-claude', 'builder-ai', 'health-ai',
           'ayako-ai', 'yomimono-ai', 'youtube-ai')


class MissingHelpersTests(unittest.TestCase):
    def setUp(self):
        parent = Path.home() / 'ai/codex/jobs/_tmp'
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        bindir = self.home / 'bin'
        bindir.mkdir()
        fake = bindir / 'tmux'
        fake.write_text('#!' + sys.executable + '\n'
            'import json,os,sys\n'
            'from pathlib import Path\n'
            'args=sys.argv[1:]\n'
            'with Path(os.environ["WS_TEST_LOG"]).open("a") as f:f.write(json.dumps(args)+"\\n")\n'
            'if "has-session" in args:sys.exit(0 if os.environ.get("WS_TEST_EXISTING")=="1" else 1)\n'
            'if "list-windows" in args:\n'
            ' if os.environ.get("WS_TEST_EXISTING")=="1":\n'
            '  for line in Path(os.environ["WS_WINDOWS_CONF"]).read_text().splitlines():print("|".join(line.split("|",3)[:2]))\n'
            ' else:print("0")\n')
        fake.chmod(0o755)
        self.log = self.home / 'tmux.jsonl'
        self.flag = self.home / 'flag.txt'
        self.conf = self.home / 'windows.conf'
        self.env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ['PATH'],
                        WS_TEST_LOG=str(self.log), WS_WINDOWS_CONF=str(self.conf), WS_CLI_FLAG=str(self.flag),
                        WS_TMUX_CONFIG=str(self.home / 'tmux.conf'), PYTHONDONTWRITEBYTECODE='1')

    def run_rows(self, commands, existing=False):
        self.conf.write_text(''.join(str(i) + '|WSCD' + str(i + 1).zfill(2) + ' fixture|' +
            str(self.home) + '|' + command + '\n' for i, command in enumerate(commands)))
        self.env['WS_TEST_EXISTING'] = '1' if existing else '0'
        result = subprocess.run(['/bin/bash', str(KIT / 'wsl/bin/studio.sh'), '--create-only'],
                                env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        launches = [call[-1] for call in calls if 'new-session' in call or 'new-window' in call]
        self.assertEqual(len(launches), 0 if existing else len(commands))
        if existing:
            self.assertFalse(any(op in call for call in calls for op in
                ('new-session', 'new-window', 'move-window', 'select-window', 'send-keys', 'respawn-window')))
        for launch in launches:
            subprocess.run(['/bin/bash', '-n'], input=launch, text=True, check=True)
        return launches

    def test_all_seven_missing_helpers_are_flagged_despite_exec_bash(self):
        commands = [str(self.home / (name + '.sh')) + ' arg; exec bash -l' for name in HELPERS]
        launches = self.run_rows(commands)
        self.assertEqual(self.flag.read_text().splitlines(), [str(i) for i in range(7)])
        self.assertTrue(all('exec bash -l' in launch for launch in launches))
        self.assertTrue(all(name + '.sh' not in '\n'.join(launches) for name in HELPERS))

    def test_existing_matching_session_audits_missing_helpers_without_window_mutation(self):
        commands = [str(self.home / (name + '.sh')) + '; exec bash -l' for name in HELPERS]
        self.run_rows(commands, existing=True)
        self.assertEqual(self.flag.read_text().splitlines(), [str(i) for i in range(7)])
        self.run_rows(commands, existing=True)
        self.assertEqual(self.flag.read_text().splitlines(), [str(i) for i in range(7)])

    def test_nonexec_nested_and_quoted_helper_check_without_expansion(self):
        nonexec = self.home / 'not executable.sh'
        nonexec.write_text('exit 0\n')
        nonexec.chmod(0o644)
        executable = self.home / 'exists.sh'
        executable.write_text('exit 0\n')
        executable.chmod(0o755)
        nested = 'bash -c ' + shlex.quote(str(self.home / 'missing.sh') + '; exec bash -l')
        marker = self.home / 'must-not-exist'
        launches = self.run_rows([shlex.quote(str(nonexec)) + '; exec bash -l', nested,
                                 str(self.home / 'missing2.sh') + ' "$(touch ' + str(marker) + ')"; exec bash -l',
                                 str(executable) + '; exec bash -l'])
        self.assertEqual(self.flag.read_text().splitlines(), ['0', '1', '2'])
        self.assertFalse(marker.exists())
        self.assertIn(str(executable), launches[-1])

    def test_template_and_grok_runtime_remain_fifty_seven_bash_rows(self):
        # 2026-10-21: the WSMENU window was retired (58 -> 57); commanders CD01/CL01/GR01 at 1-3.
        template = (KIT / 'wsl/builder/windows.conf.ws').read_text()
        self.assertEqual(len(w.rows(template)), 57)
        self.assertNotIn('WSMENU', template)
        self.assertNotIn('exec zsh -l', template)
        self.assertNotIn('zsh -c', template)
        resolved, skipped = w.resolve_template(template, {'CL': '/fixture/claude', 'CD': '/fixture/codex',
                                                         'GR': '/fixture/grok'}, self.home)
        self.assertEqual(len(resolved), 57)
        self.assertEqual(skipped, [])
        sample = '0|SMMENU menu|~/ai|zsh -c "echo fixture"; exec zsh -l\n'
        command = w.make_template(sample)[0][3]
        self.assertEqual(command, 'bash -c "echo fixture"; exec bash -l')


if __name__ == '__main__':
    unittest.main()
