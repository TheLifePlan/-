#!/usr/bin/env python3
"""HQ head/hands routes. Reads never invoke AI or change live settings."""
import argparse
import fcntl
import json
import hashlib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from pathlib import Path
import re
import stat
import tempfile
import shutil

KINDS=('claude','codex','grok')
PREFIX={'claude':'SMCL','codex':'SMCD','grok':'SMGR'}
SECRETARIES={'sana':('05','さな'),'ema':('04','えま'),'mio':('06','みお')}
HEAD_ROLES={'01':{'claude':'Claudeコマンダー','codex':'Codexコマンダー','grok':'Grokコマンダー'},
            '04':dict(claude='えまくろ',codex='えまこ',grok='えま'),
            '05':dict(claude='さなくろ',codex='さなこ',grok='さな'),
            '06':dict(claude='みおくろ',codex='みおこ',grok='みお'),
            '07':dict(claude='はるくろ',codex='はると',grok='はると')}

WORK_ROLES={'02':dict(claude='助さん',codex='次元',grok='金さん'),'03':dict(claude='格さん',codex='五右衛門',grok='銀さん')}

TERMINALS = {
    'SM': ('main', 'studio-main', '本社'), 'SF': ('studio', 'studio', '工場'),
    'MD': ('mini', 'mini', 'ミニ'), 'BV': ('default', 'zara', 'Book'), 'WS': ('win', 'win', 'WS'),
}

def terminal_config(home=None):
    home = Path(home or Path.home())
    path = home / 'ai/terminal.conf'
    defaults = dict(symbol='SM', socket='main', session='studio-main', label='本社', menu='SMMENU')
    try:
        if any(part.is_symlink() for part in [path, *path.parents]):
            raise ValueError('terminal-config-link')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 16384:
                raise ValueError('terminal-config-invalid')
            value = json.load(stream)
    except FileNotFoundError:
        return defaults
    if not isinstance(value, dict) or value.get('symbol') not in TERMINALS:
        raise ValueError('terminal-config-invalid')
    if any(not isinstance(value.get(key), str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value[key])
           for key in ('socket', 'session')):
        raise ValueError('terminal-config-invalid')
    label = value.get('label')
    if not isinstance(label, str) or not label or len(label) > 30 or any(ord(c) < 32 or ord(c) == 127 for c in label):
        raise ValueError('terminal-config-invalid')
    value.setdefault('menu', value['symbol'] + 'MENU')
    return value

def tmux_path():
    return shutil.which('tmux') or '/opt/homebrew/bin/tmux'

def _read(home,role):
    path=Path(home or Path.home())/('ai/flags/'+role+'.conf')
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            st=os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size>32:return 'codex'
            value=f.read(33).decode('ascii').strip()
        return value if value in KINDS else 'codex'
    except (OSError,UnicodeError):return 'codex'

def read_head(home=None):return _read(home,'head')
def read_hands(home=None):return _read(home,'hands')

def _parts(name):
    match=re.fullmatch(r'(SM|SF|MD|BV|BM|WS)(CL|CD|GR)(\d{2})(?: (.+))?',name or '')
    return (('BV' if match[1]=='BM' else match[1]),match[2],match[3],match[4]) if match else (None,None,None,None)

def _head_role(number,title):
    return number=='01' or (number in HEAD_ROLES and (not title or title in set(HEAD_ROLES[number].values())|{'配り役（名前待ち）','配り役 (Grok)','はると (Claude)'}))

def resolve_target(name,home=None,exact=False,snapshot=None):
    if exact:return name
    terminal,family,num,title=_parts(name)
    if terminal is None or not _head_role(num,title):return name
    kind=snapshot['head'] if snapshot else read_head(home)
    label=HEAD_ROLES[num][kind]
    if terminal=='BV' and num=='01' and kind=='claude':label='コマンダー'
    return terminal+{'claude':'CL','codex':'CD','grok':'GR'}[kind]+num+(' '+label if title else '')

def resolve_work_target(name,home=None,exact=False,snapshot=None):
    if exact:return name
    terminal,family,num,title=_parts(name)
    if terminal is None or _head_role(num,title) or num=='00':return name
    kind=snapshot['hands'] if snapshot else read_hands(home)
    label=WORK_ROLES[num][kind] if num in WORK_ROLES else title
    return terminal+{'claude':'CL','codex':'CD','grok':'GR'}[kind]+num+(' '+label if title else '')

def resolve_route(name,home=None,exact=False,snapshot=None):
    if exact:return name
    snapshot=snapshot or routing_snapshot(home)
    return resolve_work_target(resolve_target(name,home,snapshot=snapshot),home,snapshot=snapshot)


def secretary(owner,home=None):
    num,name=SECRETARIES[owner];return resolve_target(terminal_config(home)['symbol']+'CD'+num+' '+name,home)

def leader(home=None):return resolve_target(terminal_config(home)['symbol']+'CD07 はると',home)

def locked(home=None):
    path=Path(home or Path.home())/'ai/flags/head.lock'
    # Presence, including malformed/symlink, conservatively disables automation; never read it.
    return path.exists() or path.is_symlink()

def _atomic(path,value):
    if value not in KINDS:raise ValueError('invalid-routing-kind')
    if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('routing-link')
    temp=None
    try:
        with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f:
            temp=Path(f.name);os.fchmod(f.fileno(),0o600);f.write(value+'\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,path);temp=None
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temp is not None:temp.unlink(missing_ok=True)

def _json_atomic(path,value):
    if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('routing-link')
    temp=None
    try:
        with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f:
            temp=Path(f.name);os.fchmod(f.fileno(),0o600);json.dump(value,f);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,path);temp=None
    finally:
        if temp is not None:temp.unlink(missing_ok=True)

def _strict_kind(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        st=os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size>32:raise ValueError('routing-kind-unconfirmed')
        value=f.read(33).decode('ascii').strip()
    if value not in KINDS:raise ValueError('routing-kind-unconfirmed')
    return value

def routing_snapshot(home=None):
    flags=Path(home or Path.home())/'ai/flags'
    if flags.is_symlink() or not flags.is_dir():raise ValueError('routing-unconfigured')
    fd=os.open(flags/'.routing.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH)
        head=_strict_kind(flags/'head.conf');hands=_strict_kind(flags/'hands.conf')
        path=flags/'routing-snapshot.json'
        if path.is_symlink():raise ValueError('routing-link')
        if not path.exists():
            return {'head':head,'hands':hands,'generation':'legacy-'+hashlib.sha256((head+'/'+hands).encode()).hexdigest()[:20],
                    'state':'legacy-unversioned','committed_at':None}
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'r') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode) or os.fstat(stream.fileno()).st_size>4096:raise ValueError('routing-snapshot-invalid')
            value=json.load(stream)
        if not isinstance(value,dict) or value.get('head')!=head or value.get('hands')!=hands or not isinstance(value.get('generation'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',value['generation']):
            raise ValueError('routing-partial-apply')
        return value

def atomic_head(home,value):
    old=routing_snapshot(home);return atomic_routing(home,value,old['hands'])

def atomic_routing(home,head,hands,generation=None,source='local'):
    if head not in KINDS or hands not in KINDS:raise ValueError('invalid-routing-kind')
    generation=generation or uuid.uuid4().hex
    if not isinstance(generation,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',generation):raise ValueError('invalid-routing-generation')
    flags=Path(home)/'ai/flags'
    if any(p.is_symlink() for p in [flags,*flags.parents]):raise ValueError('routing-link')
    flags.mkdir(parents=True,exist_ok=True)
    fd=os.open(flags/'.routing.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        value={'head':head,'hands':hands,'generation':generation,'state':'committed','source':source,
               'committed_at':datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')}
        _atomic(flags/'hands.conf',hands);_atomic(flags/'head.conf',head)
        _json_atomic(flags/'routing-snapshot.json',value)
        directory=os.open(flags,os.O_RDONLY);os.fsync(directory);os.close(directory)
    return value


def main():
    p=argparse.ArgumentParser();p.add_argument('--secretary',choices=SECRETARIES);p.add_argument('--exact',action='store_true');p.add_argument('--target');p.add_argument('--work-target');p.add_argument('--hands',action='store_true');p.add_argument('--leader',action='store_true');p.add_argument('--home',type=Path);a=p.parse_args()
    print(leader(a.home) if a.leader else secretary(a.secretary,a.home) if a.secretary else resolve_work_target(a.work_target,a.home,a.exact) if a.work_target else resolve_target(a.target,a.home,a.exact) if a.target else read_hands(a.home) if a.hands else read_head(a.home))
if __name__=='__main__':main()
