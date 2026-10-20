#!/usr/bin/env python3
"""Client/current-specific status slots and matching navigation; metadata only."""
import argparse
from pathlib import Path
import subprocess
import unicodedata
from hq_head import terminal_config, tmux_path


def run(socket,*args):
    return subprocess.check_output([tmux_path(),'-L',socket,*args],text=True,stderr=subprocess.DEVNULL).strip()

def state(socket=None,home=None,session=None,current='',client='',live_current=False):
    config=terminal_config(home);socket=socket or config['socket'];session=session or config['session'];prefix=config['symbol']
    rows=[line.split('\t') for line in run(socket,'list-windows','-t',session,'-F','#{window_index}\t#{window_id}\t#{window_name}\t#{window_active}').splitlines()]
    if not rows or any(len(row)!=4 for row in rows):raise ValueError('windows-unconfirmed')
    if client and (live_current or not current):
        clients=[line.split('\t') for line in run(socket,'list-clients','-F','#{client_name}\t#{window_id}\t#{session_id}').splitlines()]
        actual=next((r for r in clients if r[0]==client),None)
        if actual:
            current=actual[1]
        elif live_current:raise ValueError('client-not-attached')
    if not any(r[1]==current for r in rows):
        current=next((r[1] for r in rows if r[3]=='1'),rows[0][1])
    chosen=[]
    def group(row):
        code=row[2].split(' ',1)[0]
        return next((i for i,prefix in enumerate((prefix+'CD',prefix+'CL',prefix+'GR')) if code.startswith(prefix) and len(code)==6 and code[4:].isdigit()),3)
    for row in rows:
        if group(row)<3 or row[1]==current:chosen.append(row)
    chosen.sort(key=lambda row:(group(row),int(row[0])))
    return chosen,current

def clip(value,width):
    result='';used=0
    for char in value:
        n=2 if unicodedata.east_asian_width(char) in 'WF' else 1
        if used+n>width:break
        result+=char;used+=n
    return result+' '*(width-used)

def render(socket=None,home=None,width=50,session=None,current='',client=''):
    chosen,current=state(socket,home,session,current,client)
    active=next(i for i,r in enumerate(chosen) if r[1]==current)
    count=min(2 if width<80 else 3,len(chosen))
    available=max(count,width-17)
    slot_width=max(1,(available-(count-1))//count)
    visible=[chosen[(active+i)%len(chosen)] for i in range(count)]
    out=''
    for n,(index,wid,name,_) in enumerate(visible):
        code,separator,title=name.partition(' ')
        for brand in ('Claude','Codex','Grok'):
            if title.startswith(brand):
                title=title[len(brand):];break
        label=code+separator+title
        style='bg=colour32 fg=colour231 bold' if wid==current else 'bg=colour236 fg=colour250'
        out+=f'#[range=window|{index} {style}]'+clip(label,slot_width).replace('#','##')+'#[norange default]'
        if n+1<count:out+=' '
    return out

def move(socket,home,session,client,direction):
    config=terminal_config(home);socket=socket or config['socket'];session=session or config['session']
    chosen,current=state(socket,home,session,client=client,live_current=True)
    active=next(i for i,r in enumerate(chosen) if r[1]==current)
    target=chosen[(active+direction)%len(chosen)]
    run(socket,'select-window','-t',f'{session}:{target[0]}')
    return target[1]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--socket');p.add_argument('--home',type=Path);p.add_argument('--width',type=int,default=50);p.add_argument('--session');p.add_argument('--current',default='');p.add_argument('--client',default='');p.add_argument('--move',type=int,choices=(-1,1));a=p.parse_args()
    try:
        if a.move is not None:move(a.socket,a.home,a.session,a.client,a.move)
        else:print(render(a.socket,a.home,a.width,a.session,a.current,a.client))
    except (OSError,subprocess.SubprocessError,ValueError,IndexError):
        # Nonzero/empty output activates the native status fallback.
        raise SystemExit(1)
