#!/usr/bin/env python3
"""Convert the HQ table to a WS template, then resolve it on WS without eval."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
from zoneinfo import ZoneInfo

HOME = Path.home()
DEFAULT_SOURCE = HOME / 'ai/builder/windows.conf'
DEFAULT_TEMPLATE = HOME / 'ai/builder/windows.conf.ws'
VARS = {'claude': 'CL', 'codex': 'CD', 'grok': 'GR'}
NAME = re.compile(r'^SM(?=(?:CL|CD|GR)[0-9]{2}(?: |$)|MENU(?: |$)|SH(?: |$))')
EXECUTABLE = re.compile(r'(?<![A-Za-z0-9_/.])/(?:[A-Za-z0-9_.+-]+/)+(claude|codex|grok)(?![A-Za-z0-9_./-])')
ARGUMENT = re.compile(r'((?:--name|--remote-control)\s+)([\"\']?)SM(?=(?:CL|CD|GR)[0-9]{2}(?: |[\"\']|$))')


class Failure(Exception):
    pass


def read_text(path):
    path = Path(path).absolute()
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        handle = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(handle, 'r', encoding='utf-8') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise Failure('input-not-regular')
            text = stream.read(2 * 1024 * 1024 + 1)
            if len(text) > 2 * 1024 * 1024:
                raise Failure('input-too-large')
            return text
    finally:
        os.close(fd)


def rows(text):
    result, seen = [], set()
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        fields = line.split('|', 3)
        if len(fields) != 4 or not fields[0].isdigit() or not all(fields[1:]):
            raise Failure('four-fields-required')
        number = int(fields[0])
        if number in seen:
            raise Failure('duplicate-window-number')
        if any(ord(c) < 32 or ord(c) == 127 for field in fields for c in field):
            raise Failure('control-character')
        seen.add(number)
        result.append(fields)
    if not result:
        raise Failure('no-window-rows')
    if [int(row[0]) for row in result] != sorted(int(row[0]) for row in result):
        raise Failure('window-order-invalid')
    names = [row[1] for row in result]
    if len(names) != len(set(names)):
        raise Failure('duplicate-window-name')
    return result


def bash_check(table):
    # Parse each command without executing any expansion, executable or helper.
    for row in table:
        result = subprocess.run(['/bin/bash', '-n'], input=row[3] + '\n', text=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        if result.returncode:
            raise Failure('command-syntax-invalid-window-' + row[0])


def make_template(source, source_home=HOME):
    original = rows(source)
    output = []
    for number, name, directory, command in original:
        name = NAME.sub('WS', name, count=1)
        if not name.startswith('WS'):
            raise Failure('source-window-name-invalid')
        command = EXECUTABLE.sub(lambda match: '"$' + VARS[match.group(1)] + '"', command)
        command = ARGUMENT.sub(lambda match: match.group(1) + match.group(2) + 'WS', command)
        directory = directory.replace(str(source_home), '$HOME')
        if directory == '~' or directory.startswith('~/'):
            directory = '$HOME' + directory[1:]
        command = command.replace(str(source_home), '$HOME')
        output.append([number, name, directory, command])
    if [row[0] for row in original] != [row[0] for row in output] or len(original) != len(output):
        raise Failure('template-window-count-changed')
    bash_check(output)
    return output


def command_path(name):
    # This executes only the fixed command-v builtin with a positional argument.
    # It does not evaluate a command read from windows.conf.
    result = subprocess.run(['/bin/bash', '-c', 'command -v "$1"', 'ws-windows-conf', name],
                            capture_output=True, text=True, timeout=10)
    value = result.stdout.strip()
    if result.returncode:
        return None
    if not value.startswith('/') or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise Failure('executable-path-invalid')
    if not Path(value).is_file() or not os.access(value, os.X_OK):
        raise Failure('executable-unavailable')
    return value


def resolve_template(template, paths, home):
    original = rows(template)
    if not paths.get('CL') or not paths.get('CD'):
        raise Failure('install-claude-and-codex-first')
    result, skipped = [], []
    for row in original:
        number, name, directory, command = row
        if not name.startswith('WS'):
            raise Failure('template-window-name-invalid')
        if name.startswith('WSGR') and not paths.get('GR'):
            skipped.append(number)
            continue
        directory = directory.replace('$HOME', str(home))
        command = command.replace('$HOME', shlex.quote(str(home)))
        # Quoted variable tokens become one quoted executable path. Never eval.
        for variable in ('CL', 'CD', 'GR'):
            if '$' + variable not in command:
                continue
            if not paths.get(variable):
                raise Failure('required-executable-missing')
            command = command.replace('"$' + variable + '"', shlex.quote(paths[variable]))
            command = re.sub(r'\$' + variable + r'(?![A-Za-z0-9_])', lambda _: shlex.quote(paths[variable]), command)
        result.append([number, name, directory, command])
    if [row[0] for row in result] != [row[0] for row in original if row[0] not in skipped]:
        raise Failure('runtime-window-order-changed')
    bash_check(result)
    return result, skipped


def grok_flag(home, available):
    directory = home / 'ai/flags'
    directory.mkdir(parents=True, exist_ok=True)
    if any(path.is_symlink() for path in [directory, *directory.parents]):
        raise Failure('flag-path-symlink')
    flag = directory / 'ws-grok-unconfirmed.txt'
    if available:
        if flag.is_symlink():
            raise Failure('flag-path-symlink')
        flag.unlink(missing_ok=True)
        return
    fd = os.open(flag, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds') +
                     ' WS: command -v grok 未確認。GR行だけ除外、番号を詰めない。\n')


def render(table):
    return '\n'.join('|'.join(row) for row in table) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', action='store_true', help='HQ source -> portable template; no runtime CLI lookup')
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--source-home', type=Path, default=HOME)
    parser.add_argument('--input', type=Path, default=DEFAULT_TEMPLATE, help='portable WS template')
    args = parser.parse_args(argv)
    try:
        if args.template:
            table = make_template(read_text(args.source), args.source_home)
        else:
            paths = {variable: command_path(name) for name, variable in VARS.items()}
            table, _ = resolve_template(read_text(args.input), paths, HOME)
            grok_flag(HOME, bool(paths['GR']))
        sys.stdout.write(render(table))
        return 0
    except (Failure, OSError, ValueError, subprocess.SubprocessError):
        print('WS窓の表を作れませんでした。入力の形式・実行ファイル・場所を確認してください。', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
