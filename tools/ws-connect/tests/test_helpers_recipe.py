"""Synthetic homes/CLI stubs only. No actual HQ source, auth, network or tmux."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

RECIPE = Path(__file__).resolve().parents[1] / 'wsl/bin/refresh-hq-helpers'
loader = importlib.machinery.SourceFileLoader('helpers_recipe', str(RECIPE))
spec = importlib.util.spec_from_loader(loader.name, loader)
r = importlib.util.module_from_spec(spec); loader.exec_module(r)


class HelperRecipeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve(); self.source = self.root / 'source'; self.home = self.root / 'ws'
        for relative in r.ALLOWLIST:
            path = self.source / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#!/bin/bash\nexit 0\n' if relative.endswith('.sh') else 'pass\n' if relative.endswith('.py') else '# metadata\n')
        (self.source / 'ai/guard/external-input-hooks.json').write_text('{"hooks":{}}')
        (self.source / 'ai/bin/hq_head.py').write_text("import json\nfrom pathlib import Path\ndef atomic_routing(home,head,hands):\n p=Path(home)/'ai/flags';p.mkdir(parents=True,exist_ok=True)\n (p/'head.conf').write_text(head);(p/'hands.conf').write_text(hands)\n (p/'routing-snapshot.json').write_text(json.dumps({'head':head,'hands':hands,'generation':'fixture-ws-only'}))\n")
        (self.home / 'ai/builder').mkdir(parents=True)
        self.windows = self.home / 'ai/builder/windows.conf'
        self.windows.write_text('0|WSMENU メニュー|/fixture|true\n1|WSCL01 Claudeコマンダー|/fixture|true\n56|WSCD57 YouTube|/fixture|true\n99|WSSH コマンド|/fixture|true\n')

    def test_allowlist_install_is_private_preserves_windows_and_existing_rules(self):
        self.assertEqual(len(r.ALLOWLIST), 31)
        self.assertFalse(any('/state/' in p or '/alerts/' in p or '/diagnostics/' in p or '.bak' in p for p in r.ALLOWLIST))
        existing = self.home / 'Code/youtube/AGENTS.md'; existing.parent.mkdir(parents=True); existing.write_text('existing WS rule')
        before = self.windows.read_bytes()
        result = r.install(self.source, self.home)
        self.assertEqual(result['targets'], 2)  # menu/shell intentionally excluded from tell.
        self.assertEqual(self.windows.read_bytes(), before)
        self.assertEqual(result['routing'], 'initialized-claude-claude')
        (self.home/'ai/flags/head.conf').write_text('grok')
        self.assertEqual(r.install(self.source,self.home)['routing'], 'preserved')
        self.assertEqual((self.home/'ai/flags/head.conf').read_text(),'grok')
        self.assertEqual(existing.read_text(), 'existing WS rule')
        self.assertFalse((self.home / 'ai/guard/state').exists())
        self.assertFalse((self.home / 'ai/flags/health-ai-approved.on').exists())
        self.assertEqual((self.home / 'ai/bin/tell-targets.tsv').stat().st_mode & 0o777, 0o600)

    def test_portable_local_identifiers_routes_and_fixed_hook_secret_refusal(self):
        code = "import re\npattern=r'^SM(?:CL|CD)\\d+'\nargv=['tmux',\"-L\",\"main\"]\nlabel='SMCD01 Codexコマンダー'\n"
        out = r.portable('ai/bin/desk-config.py', code, self.home)
        self.assertIn('WS(?:CL|CD)', out); self.assertIn("'-L', 'win'", out); self.assertIn('WSCD01', out)
        tell = "routes=('SM', 'MD', 'SF', 'BV')\npattern=r'^(?:SM|MD|SF|BV|BM)'\n"
        out = r.portable('ai/bin/tell.py', tell, self.home)
        self.assertIn("('SM', 'WS', 'MD', 'SF', 'BV')", out); self.assertIn('SM|WS|MD', out)
        with self.assertRaises(ValueError): r.safe_config('{"hooks":{},"api_key":"fixture"}')

    def test_youtube_launches_new_cli_only_and_guard_entry_uses_guard_directory(self):
        source = '''#!/bin/bash
set -eu
family="$1"
folder=/Users/prod/Code/youtube
cd "$folder"
paper="/Users/prod/ai/codex/jobs/_tmp/youtube-studio-start-goemon/$family-startup.md"
case "$family" in
 codex) exec /opt/homebrew/bin/codex resume 00000000-0000-4000-8000-000000000001 -C "$folder" "$paper" ;;
 claude) exec /Users/prod/.local/bin/claude --resume 00000000-0000-4000-8000-000000000002 --name 'SMCL57 YouTube' "$paper" ;;
esac
'''
        (self.source / 'ai/bin/youtube-ai.sh').write_text(source)
        (self.source / 'ai/guard/guard-engine.py').write_text("import pathlib,sys\nraise SystemExit(1 if 'REFUSE' in pathlib.Path(sys.argv[2]).read_text() else 0)\n")
        (self.source / 'ai/guard/guard-paper.sh').write_text('#!/bin/bash\nexec python3 "$(dirname "$0")/guard-engine.py" paper "$1"\n')
        r.install(self.source, self.home)
        bins = self.home / '.local/bin'; bins.mkdir(parents=True)
        for name in ('codex','claude'):
            path = bins/name
            path.write_text('#!/usr/bin/env python3\nimport json,os,sys\nopen(os.environ["FIXTURE_ARGS"],"w").write(json.dumps(sys.argv[1:]))\n'); path.chmod(0o755)
        argsfile = self.root / 'args.json'; env = dict(os.environ, HOME=str(self.home), FIXTURE_ARGS=str(argsfile))
        for family in ('codex','claude'):
            subprocess.run(['/bin/bash', str(self.home/'ai/bin/youtube-ai.sh'), family], env=env, check=True)
            args = json.loads(argsfile.read_text())
            self.assertFalse(any('resume' in arg or '00000000-' in arg for arg in args))
            self.assertTrue(any('ai/ws/startup/youtube-' in arg for arg in args))
        paper = self.root / 'paper.md'
        for content, expected in [('benign fixture',0),('REFUSE fixture',1)]:
            paper.write_text(content)
            result = subprocess.run(['/bin/bash',str(self.home/'ai/bin/guard-paper.sh'),str(paper)],env=env)
            self.assertEqual(result.returncode, expected)


if __name__ == '__main__': unittest.main()
