#!/usr/bin/env python3
"""端末ごとに。窓表から実IDを照合し、client寸法以内のページを表示する。"""
import json, math, os, shlex, subprocess, sys, unicodedata, re
from pathlib import Path
from hq_head import terminal_config, tmux_path, resolve_work_target
def tmux_command():
    return [tmux_path(), '-L', terminal_config()['socket']]
TMUX = tmux_command()
SCRIPT = str(Path(__file__).resolve())
def run(*args):
    return subprocess.check_output(TMUX + list(args), text=True).strip()
def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)
def clip(s, limit):
    out = ''
    for c in s:
        if width(out + c) > limit: return out[:-1] + '…'
        out += c
    return out

def lead(symbol):
    # 2026-10-21 ZARA: Codex01/Claude01/Grok01 exact, always first.
    return tuple(symbol + family + '01' for family in ('CD', 'CL', 'GR'))

def entries():
    config = terminal_config()
    live = [row.split('\t', 2) for row in run('list-windows', '-t', '=' + config['session'],
            '-F', '#{window_index}\t#{window_id}\t#{window_name}').splitlines()]
    if any(len(row) != 3 for row in live):
        raise ValueError('windows-unconfirmed')
    byname = {}
    for index, wid, name in live:
        if name in byname or not index.isdigit() or not re.fullmatch(r'@[0-9]+', wid):
            raise ValueError('windows-not-unique')
        byname[name] = (index, wid)
    if config['symbol'] == 'SM':
        # HQ keeps the established table order and its exact set of entries.
        names = [row.split('|', 3)[1] for row in Path.home().joinpath('ai/builder/windows.conf').read_text().splitlines()
                 if row and not row.startswith('#')]
    else:
        names = [row[2] for row in live]
    # The dedicated menu window was retired (ZARA 2026-10-21); never offer it.
    data = [(name, *byname[name]) for name in names if name in byname
            and name.split(' ', 1)[0] != config['symbol'] + 'MENU']
    first = lead(config['symbol'])
    def order(entry):
        symbol = entry[0].split(' ', 1)[0]
        return first.index(symbol) if symbol in first else 3
    return sorted(data, key=order)

def work_rows(home=None):
    """Terminal-local work menu (label<TAB>kind<TAB>value); absent = normal popup."""
    path = Path(home or Path.home()) / 'ai/work-menu.tsv'
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'): continue
        fields = line.split('\t')
        if len(fields) != 3 or not fields[0] or any(ord(c) < 32 for f in fields for c in f):
            raise ValueError('work-menu-invalid')
        label, kind, value = fields
        if kind == 'hands' and not re.fullmatch(r'[0-9]{2}', value): raise ValueError('work-menu-invalid')
        if kind not in ('hands', 'all', 'note'): raise ValueError('work-menu-invalid')
        rows.append((label, kind, value))
    return rows

def work_items(client, rows, data):
    """Commanders first, then work entries routed by the hands family; never runs work."""
    symbol = terminal_config()['symbol']
    items = [(name, f'select-window -t {wid}') for name, index, wid in data
             if name.split(' ', 1)[0] in lead(symbol)]
    bycode = {}
    for name, index, wid in data:
        bycode.setdefault(name.split(' ', 1)[0], []).append((name, wid))
    for label, kind, value in rows:
        if kind == 'all':
            items.append((label, 'run-shell -b ' + shlex.quote(shlex.join([sys.executable, SCRIPT, client, '0', '--all']))))
        elif kind == 'note':
            items.append(('-' + label, ''))
        else:
            code = resolve_work_target(symbol + 'CL' + value)
            match = bycode.get(code, [])
            if len(match) == 1:
                items.append((label + ' → ' + match[0][0], f'select-window -t {match[0][1]}'))
            else:
                items.append(('-' + label + ' (' + code + ' 窓なし)', ''))
    return items

def build(client, page, dimensions=None, show_all=False):
    cols, rows = dimensions or tuple(map(int, run('display-message','-p','-c',client,'#{client_width} #{client_height}').split()))
    # 2 borders + 2 navigation rows + extra clearance above 3-line status.
    size = max(1, min(9, rows - 8))
    data = entries()
    work = None if show_all else work_rows()
    if work is None:
        items = [(name, f'select-window -t {wid}') for name, index, wid in data]
        title = '机'
    else:
        items = work_items(client, work, data)
        title = '仕事'
    pages = max(1, math.ceil(len(items) / size)); page %= pages
    args = ['display-menu','-O','-M','-c',client,'-T',f'{title} {page+1}/{pages}','-x','C','-y','C']
    selected = items[page*size:(page+1)*size]
    for n, (name, command) in enumerate(selected):
        number = str(n+1)
        disabled = name.startswith('-')
        label = ('-' if disabled else '') + number + ' ' + clip(name.lstrip('-').replace('#','##'), max(4, cols-14))
        args += [label, '' if disabled else number, command]
    for label, key, delta in [('◀','q',-1),('▶','p',1)]:
        argv = [sys.executable, SCRIPT, client, str((page+delta)%pages)] + (['--all'] if show_all else [])
        args += [label,key,'run-shell -b ' + shlex.quote(shlex.join(argv))]
    shown = [entry for entry in data if any(command == f'select-window -t {entry[2]}' for _, command in selected)]
    return args, dict(client=client,width=cols,height=rows,page=page+1,pages=pages,menu_rows=len(selected)+4,
                      mode='all' if work is None else 'work',items=[name for name, _ in selected],entries=shown)
if __name__ == '__main__':
    flags = [value for value in sys.argv[2:] if value.startswith('--')]
    numbers = [value for value in sys.argv[2:] if not value.startswith('--')]
    args, meta = build(sys.argv[1], int(numbers[0]) if numbers else 0, show_all='--all' in flags)
    if '--inspect' in flags: print(json.dumps(meta,ensure_ascii=False))
    else: subprocess.run(TMUX+args,check=True)
