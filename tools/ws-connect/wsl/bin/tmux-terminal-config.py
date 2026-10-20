#!/usr/bin/env python3
"""Apply the shared tmux status/F-key layout using terminal-local metadata only."""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

LABELS = {'SM': '本社', 'SF': '工場', 'MD': 'ミニ', 'BV': 'Book', 'WS': 'WS'}


def preset(symbol, socket, session):
    keys = {}
    def window(key, name): keys['F' + str(key)] = {'window': name}
    if symbol in ('SM', 'WS'):
        for start, family, names in [(1, 'CD', [('01', 'Codexコマンダー'), ('05', 'さなこ'), ('04', 'えまこ'), ('06', 'みおこ')]),
                                     (5, 'CL', [('01', 'Claudeコマンダー'), ('05', 'さなくろ'), ('04', 'えまくろ'), ('06', 'みおくろ')]),
                                     (9, 'GR', [('01', 'Grokコマンダー'), ('05', 'さな'), ('04', 'えま'), ('06', 'みお')])]:
            for offset, (number, title) in enumerate(names): window(start + offset, symbol + family + number + ' ' + title)
    elif symbol == 'SF':
        # 2026-10-21 ZARA: the menu window is retired; F4 opens the desk popup instead.
        names = ['SFCD01 Codexコマンダー', 'SFCD02 次元', 'SFCD03 五右衛門', None,
                 'SFCL01 Claudeコマンダー', 'SFCL02 助さん', 'SFCL03 格さん', 'SFMO01 進み具合',
                 'SFGR01 Grokコマンダー', 'SFGR02 金さん', 'SFGR03 銀さん', 'SFSH01 作業端末']
        for key, name in enumerate(names, 1):
            if name: window(key, name)
            else: keys['F' + str(key)] = {'popup': 'desks'}
    elif symbol == 'MD':
        names = ['MDCD01 Codexコマンダー', 'MDCD02 次元', 'MDCD03 五右衛門', None,
                 'MDCL01 Claudeコマンダー', 'MDCL02 助さん', 'MDCL03 格さん', '',
                 'MDGR01 Grokコマンダー', 'MDGR02 金さん', 'MDGR03 銀さん', 'MDOP 操作']
        for key, name in enumerate(names, 1):
            if name: window(key, name)
            elif name is None: keys['F' + str(key)] = {'popup': 'desks'}
    elif symbol == 'BV':
        for start, family, title, roles in [(1, 'CD', 'Codex', ['さなこ', 'えまこ', 'みおこ']),
                                          (5, 'CL', 'Claude', ['さなくろ', 'えまくろ', 'みおくろ']),
                                          (9, 'GR', 'Grok', ['さな', 'えま', 'みお'])]:
            window(start, 'BV' + family + '01 ' + title + 'コマンダー')
            for offset, role in enumerate(roles, 1): keys['F' + str(start + offset)] = {'message': title + ' / ' + role + ': 未設置（予約枠）'}
    else:
        raise ValueError('terminal-symbol-invalid')
    value = {'symbol': symbol, 'socket': socket, 'session': session, 'label': LABELS[symbol], 'menu': symbol + 'MENU', 'fkeys': keys}
    if symbol == 'WS': value['home'] = 'WSCD01 Codexコマンダー'  # replaces the old Home → WSMENU
    return value



def native_fallback(symbol):
    def group(prefix, width):
        match = '#{m/r:^' + prefix + '[0-9][0-9] ,#{window_name}}'
        return window(match, width)
    def window(condition, width):
        return ('#{W:#{?' + condition + ',#[range=window|#{window_index}]'
                '#{?window_active,#[bg=colour32 fg=colour231 bold list=focus],#[bg=colour236 fg=colour250]}'
                '#{p-' + str(width) + ':#{=' + str(width) + ':#{s/Claude|Codex|Grok//:window_name}}}'
                '#[norange default list=on] ,}}')
    def row(width):
        # Codex01/Claude01/Grok01 exact first, then the other AI desks in window order.
        non_ai = '#{&&:#{!:#{m/r:^' + symbol + '(CL|CD|GR)[0-9][0-9] ,#{window_name}}},#{window_active}}'
        others = '#{m/r:^' + symbol + '(CL|CD|GR)(0[2-9]|[1-9][0-9]) ,#{window_name}}'
        return ('#[list=on align=left]#[list=left-marker]‹#[list=right-marker]›#[list=on]'
                + ''.join(window('#{m/r:^' + symbol + family + '01 ,#{window_name}}', width) for family in ('CD', 'CL', 'GR'))
                + window(others, width) + window(non_ai, width) + '#[nolist norange default]')
    return '#{?#{e|<:#{client_width},80},' + row(16) + ',#{?#{e|<:#{client_width},120},' + row(20) + ',' + row(33) + '}}'


def commands(config, home, python, version='3.7'):
    symbol, session, label = config['symbol'], config['session'], config['label']
    if symbol not in LABELS or not re.fullmatch(r'[A-Za-z0-9_-]+', session): raise ValueError('terminal-invalid')
    if any(ord(c) < 32 or ord(c) == 127 for c in label): raise ValueError('terminal-label-invalid')
    keys = config.get('fkeys', preset(symbol, config['socket'], session)['fkeys'])
    binary = shlex.quote(str(python)); scripts = home / 'ai/bin'
    menu = binary + ' ' + shlex.quote(str(scripts / 'tmux-desk-menu.py')) + " #{?client_name,#{q:client_name},''}"
    rows = []
    for key in range(1, 13): rows.append(['unbind-key', '-q', '-n', 'F' + str(key)])
    rows.append(['unbind-key', '-q', '-n', 'Home'])
    home_window = config.get('home')
    if home_window is not None:
        if not isinstance(home_window, str) or not home_window or any(ord(c) < 32 or ord(c) == 127 for c in home_window): raise ValueError('home-invalid')
        rows.append(['bind-key', '-n', 'Home', 'select-window', '-t', '=' + session + ':=' + home_window])
    for key, action in keys.items():
        if not re.fullmatch(r'F(?:[1-9]|1[0-2])', key) or not isinstance(action, dict) or len(action) != 1: raise ValueError('fkey-invalid')
        kind, value = next(iter(action.items()))
        if not isinstance(value, str) or not value or any(ord(c) < 32 or ord(c) == 127 for c in value): raise ValueError('fkey-invalid')
        if kind == 'window': rows.append(['bind-key', '-n', key, 'select-window', '-t', '=' + session + ':=' + value])
        elif kind == 'message': rows.append(['bind-key', '-n', key, 'display-message', '-d', '3000', value])
        elif kind == 'popup' and value == 'desks': rows.append(['bind-key', '-n', key, 'run-shell', '-b', menu])
        else: raise ValueError('fkey-invalid')
    status = binary + ' ' + shlex.quote(str(scripts / 'tmux-head-status-v3.py'))
    args = " --session '#{session_id}' --client #{?client_name,#{q:client_name},''}"
    render = status + args + " --current '#{window_id}' --width #{client_width} 2>/dev/null"
    # The v3 script chooses two/three slots; arrows and popup match HQ's layout.
    visible = '#{?#{!=:#(' + render + '),},#(' + render + '),' + native_fallback(symbol) + '}'
    legacy_mouse = version.startswith('3.6')
    ranges = ('user|menu', 'user|prev', 'user|next') if legacy_mouse else ('control|0', 'control|1', 'control|2')
    fmt = '#[range=' + ranges[0] + '][' + label.replace('#', '##') + ']#[norange default] #[range=' + ranges[1] + ' bold] ◀◀ #[norange default] ' + visible + ' #[align=right range=' + ranges[2] + ' bold] ▶▶ #[norange default]'
    rows += [['set-option', '-g', 'base-index', '1'], ['set-option', '-g', 'status-interval', '1'],
             ['set-option', '-g', 'status-left', '[Studio ' + label + '] ']]
    actions = [menu, status + args + ' --move -1', status + args + ' --move 1']
    if legacy_mouse:
        # tmux 3.6 has user ranges, but no MouseDown1Control* keys.
        # A normal window-range click keeps the native mouse target (=).
        dispatch = 'select-window -t ='
        for name, command in reversed(list(zip(('menu', 'prev', 'next'), actions))):
            dispatch = shlex.join(['if-shell', '-F', '#{==:#{mouse_status_range},' + name + '}',
                                   shlex.join(['run-shell', '-b', command]), dispatch])
        rows.append(['bind-key', '-n', 'MouseDown1Status', *shlex.split(dispatch)])
    else:
        for number, command in enumerate(actions):
            rows.append(['bind-key', '-n', 'MouseDown1Control' + str(number), 'run-shell', '-b', command])
    rows.append(['set-option', '-g', 'status-format[0]', fmt])
    if symbol == 'SM': rows.append(['bind-key', '-n', 'S-F1', 'run-shell', '-b', binary + ' ' + shlex.quote(str(scripts / 'menu-navigation.py')) + ' builder'])
    return rows


def main():
    p = argparse.ArgumentParser(); p.add_argument('--socket-path'); p.add_argument('--preset', choices=LABELS); p.add_argument('--socket'); p.add_argument('--session'); a = p.parse_args()
    if a.preset:
        print(json.dumps(preset(a.preset, a.socket, a.session), ensure_ascii=False, indent=2)); return 0
    from hq_head import terminal_config
    home = Path.home(); config = terminal_config(home)
    tmux = shutil.which('tmux') or '/opt/homebrew/bin/tmux'
    base = [tmux, '-S', a.socket_path] if a.socket_path else [tmux, '-L', config['socket']]
    version = subprocess.check_output(base + ['display-message', '-p', '#{version}'], text=True, timeout=10).strip()
    rows = commands(config, home, sys.executable, version)  # Validate all actions before applying any.
    for row in rows: subprocess.run(base + row, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    return 0


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError): raise SystemExit(1)
