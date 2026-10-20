"""メニューの窓名解決。オフラインでは一覧の読み込みだけを行う。"""
import importlib.util
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.dont_write_bytecode = True
SYMBOL = re.compile(r'(?:(?:SM|SF|MD|BV|WS)MENU|(?:SM|SF|MD|BV|WS)(?:CL|CD|GR)[0-9]{2})', re.ASCII)
FACTORY_DESKS = set(range(12, 34))
FACTORY_MESSAGE = '工場へ移した (SFCL01)'
BOOK_MESSAGE = 'Book へ移した (BVCL01)'
HISHO_NAMES = {f'SM{ai}{number}': f'SM{ai}{number} '+(name+'こ' if ai=='CD' else name+'くろ' if ai=='CL' else name) for ai in ('CL','CD','GR') for number,name in [('05','さな'),('04','えま'),('06','みお')]}
LEADER_NAME = 'SMCD07 はると'
FUND_MESSAGE = '07 fund は 58 に移す予定（未起動）'
HEAD_SYMBOLS = {'SMMENU', 'SMCL00', 'SMCL01', 'SMCL02', 'SMCL03',
                'SMCD01', 'SMCD02', 'SMCD03', 'SMGR01', 'SMGR02', 'SMGR03'}


def _head_helper():
    spec = importlib.util.spec_from_file_location('menu_terminal_head', Path(__file__).with_name('hq_head.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper

def _terminal():
    return _head_helper().terminal_config(os.environ.get('MENU_HOME'))

def _connection():
    config = _terminal()
    return (os.environ.get('DESKS_SOCKET', config['socket']),
            os.environ.get('DESKS_SESSION', config['session']))

def _tmux():
    return _head_helper().tmux_path()

def resolve_live(value, windows, config):
    value = value.strip().upper()
    if value in ('', 'R', 'Q'):
        return ('none',)
    prefix = config['symbol']
    if value.isascii() and value.isdigit():
        matches = [(index, name) for index, name in windows if index == int(value)]
    else:
        if value.startswith('SM'):
            value = prefix + value[2:]
        if not SYMBOL.fullmatch(value) or not value.startswith(prefix):
            raise ValueError('この端末の窓を指定してください。')
        matches = [(index, name) for index, name in windows if symbol_of(name) == value]
    if len(matches) != 1 or sum(index == matches[0][0] for index, _ in windows) != 1:
        raise ValueError('窓が無いか重複しています。')
    # Non-HQ menus never invent desks or invoke HQ-only helper dependencies.
    return ('select', matches[0][0])

def symbol_of(name):
    token = name.split(maxsplit=1)[0].upper() if name.split() else ''
    return token if SYMBOL.fullmatch(token) else ''


def factory_input(value):
    match = re.fullmatch(r'(?:SM(?:CL|CD)([0-9]{2})|C?([0-9]+))', value.strip().upper(), re.ASCII)
    return bool(match and int(match[1] or match[2]) in FACTORY_DESKS)


def book_input(value):
    # SMCD05 is now secretary Sana; retired YouTube has an explicit old name.
    return False


def secretary_target(role):
    prefix = _terminal()['symbol']
    defaults = {'sana':prefix+'CL05 さなくろ','ema':prefix+'CL04 えまくろ','mio':prefix+'CL06 みおくろ'}
    base = {'sana':('05','さな'),'ema':('04','えま'),'mio':('06','みお')}[role]
    default = prefix+'CD'+base[0]+' '+base[1]+'こ'
    try:
        spec = importlib.util.spec_from_file_location('menu_hq_head', Path(__file__).with_name('hq_head.py'))
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        result = helper.resolve_target(defaults[role])
        allowed = (prefix+'CL'+base[0]+' '+base[1]+'くろ',default,prefix+'GR'+base[0]+' '+base[1])
        if result in allowed:
            return result
    except (OSError, ValueError, ImportError, AttributeError, TypeError):
        pass
    return default


def builder_target(home=None):
    # 09 is now available to every hands family. No model/repo access here.
    spec=importlib.util.spec_from_file_location('menu_builder_head',Path(__file__).with_name('hq_head.py'))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    family=helper.read_hands(home)
    prefix=_terminal()['symbol']+{'claude':'CL','codex':'CD','grok':'GR'}[family]
    return prefix+'09 ビルダー'


def navigate_builder():
    return navigate(builder_target().split(' ',1)[0])


def navigate_secretary(role):
    try:
        target = secretary_target(role)
        windows = read_windows()
        matches = [(i,n) for i,n in windows if n == target]
        if len(matches) != 1:
            return '秘書の窓を確認してください。'
        if os.environ.get('MENU_OFFLINE') == '1':
            return '選択予定: ' + target
        socket, session = _connection()
        subprocess.run([_tmux(),'-L',socket,'select-window','-t',f'={session}:{matches[0][0]}'],
                       check=True,capture_output=True,text=True)
        return ''
    except (OSError, ValueError, subprocess.CalledProcessError):
        return '接続できません'


def read_windows():
    if os.environ.get('MENU_OFFLINE') == '1':
        filename = os.environ.get('MENU_WINDOWS_FILE', '')
        if not filename:
            return []
        source = Path(filename).read_text()
    else:
        socket, session = _connection()
        source = subprocess.run(
            [_tmux(), '-L', socket, 'list-windows', '-t', '=' + session,
             '-F', '#{window_index}|#{window_name}'],
            check=True, capture_output=True, text=True).stdout
    windows = []
    for line in source.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split('|', 2) if '|' in line else line.split(maxsplit=1)
        if len(fields) < 2 or not re.fullmatch(r'[0-9]+', fields[0]):
            raise ValueError('一覧を取得できません')
        windows.append((int(fields[0]), fields[1]))
    return windows


def desk_config():
    spec = importlib.util.spec_from_file_location('menu_desk_config', Path(__file__).with_name('desk-config.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve(value, windows):
    config = _terminal()
    if config['symbol'] != 'SM':
        return resolve_live(value, windows, config)
    if book_input(value):
        raise ValueError(BOOK_MESSAGE)
    if factory_input(value):
        raise ValueError(FACTORY_MESSAGE)
    value = value.strip().upper()
    if value in ('', 'R', 'Q'):
        return ('none',)
    legacy = re.fullmatch(r'(C?)([0-9]+)', value, re.ASCII)
    if SYMBOL.fullmatch(value):
        symbol = value
    elif legacy:
        number = int(legacy[2])
        if number > 99:
            raise ValueError('不明な入力')
        if not legacy[1] and number == 9:
            symbol=builder_target().split(' ',1)[0]
        elif not legacy[1] and number == 0:
            symbol = 'SMMENU'
        else:
            symbol = f'SM{"CD" if legacy[1] else "CL"}{number:02d}'
    else:
        raise ValueError('不明な入力')

    matches = [(index, name) for index, name in windows if symbol_of(name) == symbol]
    if symbol in HISHO_NAMES and any(name != HISHO_NAMES[symbol] for _, name in matches):
        raise ValueError(HISHO_NAMES[symbol] + 'の窓を確認してください。')
    if symbol in ('SMCD07','SMCL07') and any(name != (LEADER_NAME if symbol=='SMCD07' else 'SMCL07 はるくろ') for _,name in matches):
        raise ValueError('旧fundの窓をはるととして使えません。')
    if len(matches) > 1:
        raise ValueError(symbol + ' 窓が重複しています')
    if matches:
        index = matches[0][0]
        if sum(other == index for other, _ in windows) != 1:
            raise ValueError(symbol + ' 窓が重複しています')
        return ('select', index)
    if symbol in ('SMCL54','SMCD54','SMGR54'):
        raise ValueError(symbol+' 新聞デスクの窓を確認してください。')
    if symbol in ('SMCL53','SMCD53','SMGR53'):
        raise ValueError(symbol+' ayakoの窓を確認してください。')
    if symbol in ('SMCL09','SMCD09','SMGR09'):
        raise ValueError(symbol+' ビルダーの窓を確認してください。')
    if symbol in ('SMCD47','SMGR47'):
        return ('health','codex' if symbol=='SMCD47' else 'grok')
    if symbol in HISHO_NAMES:
        
        if symbol.startswith('SMGR'):
            raise ValueError('Grok秘書の窓が停止しています。親へ知らせてください。')
        return ('open',int(symbol[4:]),symbol.startswith('SMCD'))
    if symbol in HEAD_SYMBOLS:
        raise ValueError(symbol + ' 止まっている')
    if not symbol.startswith(('SMCL', 'SMCD')):
        raise ValueError(symbol + ' 本社の対象外')
    number = int(symbol[4:])
    desk = desk_config()
    fields = desk.read_row(number)
    codex = symbol.startswith('SMCD')
    if codex:
        desk.require_codex(fields)
    elif symbol_of(fields[1]) != symbol:
        raise ValueError(symbol + ' 表の記号が一致しません')
    return ('open', number, codex)


def navigate(value):
    local_hq = _terminal()['symbol'] == 'SM'
    if local_hq and book_input(value):
        return BOOK_MESSAGE
    if local_hq and factory_input(value):
        return FACTORY_MESSAGE
    if value.strip().upper() in ('', 'R', 'Q'):
        return ''
    try:
        windows = read_windows()  # 描画時の一覧を使い回さない。
    except (OSError, ValueError, subprocess.CalledProcessError):
        return '一覧を取得できません'
    try:
        action = resolve(value, windows)
        socket, session = _connection()
        if action[0] == 'select':
            if os.environ.get('MENU_OFFLINE') == '1':
                return f'選択予定: {session}:{action[1]}'
            subprocess.run([_tmux(), '-L', socket, 'select-window', '-t',
                            f'={session}:{action[1]}'], check=True, capture_output=True, text=True)
        elif action[0] == 'health':
            family=action[1]
            name=('SMCD47' if family=='codex' else 'SMGR47')+' health'
            if os.environ.get('MENU_OFFLINE') == '1':
                return '起動予定: '+name
            # New health families must pass the owner's approval guard.
            # Do not rewrite windows.conf or tell-targets (owned by the health task).
            command=shlex.join([str(Path.home()/'ai/bin/health-ai.sh'),family])+'; exec /bin/zsh -l'
            subprocess.run([_tmux(),'-L',socket,'new-window','-t','='+session,
                            '-n',name,'-c',str(Path.home()/'Code/health'),command],
                           check=True,capture_output=True,text=True)
            return ''
        elif action[0] == 'open':
            if os.environ.get('MENU_OFFLINE') == '1':
                symbol = f'SM{"CD" if action[2] else "CL"}{action[1]:02d}'
                return '起動予定: ' + symbol
            command = [str(Path(__file__).with_name('desk.sh')), str(action[1])]
            if action[2]:
                command.append('codex')
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                return (result.stderr or result.stdout).strip() or '起動できません'
            return result.stdout.strip()
        return ''
    except ValueError as error:
        return str(error)
    except (OSError, subprocess.CalledProcessError):
        return '接続できません'


def main():
    if sys.argv[1:] == ['windows']:
        try:
            for index, name in read_windows():
                print(f'{index}|{name}')
        except (OSError, ValueError, subprocess.CalledProcessError):
            print('一覧を取得できません', file=sys.stderr)
            return 1
    elif sys.argv[1:] == ['builder']:
        print(navigate_builder())
    elif len(sys.argv) == 3 and sys.argv[1] == 'secretary' and sys.argv[2] in ('sana','ema','mio'):
        print(navigate_secretary(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == 'input':
        print(navigate(sys.argv[2]))
    else:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
