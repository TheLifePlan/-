#!/usr/bin/env python3
"""端末ごとに。窓表から実IDを照合し、client寸法以内のページを表示する。"""
import json, math, os, shlex, subprocess, sys, unicodedata, re
from pathlib import Path
from hq_head import terminal_config, tmux_path
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
    data = [(name, *byname[name]) for name in names if name in byname]
    def order(entry):
        symbol = entry[0].split(' ', 1)[0]
        family = {config['symbol'] + 'CD': 0, config['symbol'] + 'CL': 1,
                  config['symbol'] + 'GR': 2}.get(symbol[:4], 3)
        return family, 0 if symbol[4:] == '01' else 1
    return sorted(data, key=order)

def build(client, page, dimensions=None):
    cols, rows = dimensions or tuple(map(int, run('display-message','-p','-c',client,'#{client_width} #{client_height}').split()))
    # 2 borders + 2 navigation rows + extra clearance above 3-line status.
    size = max(1, min(9, rows - 8))
    data = entries(); pages = max(1, math.ceil(len(data) / size)); page %= pages
    args = ['display-menu','-O','-M','-c',client,'-T',f'机 {page+1}/{pages}','-x','C','-y','C']
    selected = data[page*size:(page+1)*size]
    for n, (name, index, wid) in enumerate(selected):
        number = str(n+1)
        label = number + ' ' + clip(name.replace('#','##'), max(4, cols-14))
        args += [label, number, f'select-window -t {wid}']
    for label, key, delta in [('◀','q',-1),('▶','p',1)]:
        command = 'run-shell -b ' + shlex.quote(shlex.join([sys.executable, SCRIPT, client, str((page+delta)%pages)]))
        args += [label,key,command]
    return args, dict(client=client,width=cols,height=rows,page=page+1,pages=pages,menu_rows=len(selected)+4,entries=selected)
if __name__ == '__main__':
    args, meta = build(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 and sys.argv[2]!='--inspect' else 0)
    if '--inspect' in sys.argv: print(json.dumps(meta,ensure_ascii=False))
    else: subprocess.run(TMUX+args,check=True)
