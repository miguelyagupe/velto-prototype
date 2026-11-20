"""Capture a real PTY, save asciicast, faithfully rasterize via pyte.

The video is a terminal replay of actual captured input/output. It is NOT a
browser screen recording or fabricated terminal. Commands run before narration.
"""
import argparse,asyncio,fcntl,hashlib,json,os,pty,select,struct,subprocess,termios,time
from pathlib import Path
from datetime import datetime,timezone
import pyte
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
COMMANDS=[
('Inspect synthetic source data','cat demo/sales.csv'),
('Compute original totals','python demo/analyze.py demo/sales.csv'),
('Inspect deliberate input change','diff -u demo/sales.csv demo/changed.csv'),
('Compute changed input','python demo/analyze.py demo/changed.csv'),
('Run deliberate invalid-input test','python demo/analyze.py demo/invalid.csv'),
('Restore original valid data','python demo/analyze.py demo/sales.csv'),
('Sort calculated bars','python demo/analyze.py demo/sales.csv --order desc'),
('Filter and recompute','python demo/analyze.py demo/sales.csv --minimum 2000'),
('Inspect exact computed values','python demo/analyze.py demo/sales.csv --minimum 2000 --json'),
('Verify original app handlers','node demo/test_calculations.cjs'),
('Inspect real production CLI','python -m awl --help'),
('Run production engine tests','python -m unittest discover -s tests -v'),
('Inspect real encoder availability','ffmpeg -version | head -n 3'),
('Verify source hashes','sha256sum demo/analyze.py demo/sales.csv'),
]
async def capture(out):
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',27,104,0,0))
    env=dict(os.environ,PS1='awl$ ',TERM='xterm-256color',COLUMNS='104',LINES='27',PYTHONUNBUFFERED='1')
    proc=subprocess.Popen(['/bin/bash','--noprofile','--norc','-i'],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,env=env,start_new_session=True)
    os.close(slave);os.set_blocking(master,False);start=time.monotonic();events=[];marks=[];output=''
    def read():
        nonlocal output
        while True:
            try:b=os.read(master,65536)
            except (BlockingIOError,OSError):break
            if not b:break
            text=b.decode('utf8',errors='replace');output+=text;events.append([round(time.monotonic()-start,4),'o',text])
    async def wait(n):
        end=time.monotonic()+n
        while time.monotonic()<end:read();await asyncio.sleep(.02)
        read()
    await wait(.5)
    for title,cmd in COMMANDS:
        # A real terminal clear and real command entry, both preserved in cast.
        os.write(master,b'clear\n');await wait(.2)
        begin=time.monotonic()-start
        for c in cmd+'\n':
            os.write(master,c.encode());events.append([round(time.monotonic()-start,4),'i',c]);await wait(.025)
        cutoff=time.monotonic()+35;oldlen=len(output)
        await wait(.3)
        while not output.endswith('awl$ ') and time.monotonic()<cutoff:await wait(.1)
        await wait(3.2)
        marks.append({'title':title,'command':cmd,'in':round(begin,3),'out':round(time.monotonic()-start,3),'captured_output':output[oldlen:]})
    duration=time.monotonic()-start
    os.write(master,b'exit\n');await wait(.2);proc.wait(timeout=3);os.close(master)
    header={'version':2,'width':104,'height':27,'timestamp':int(time.time()),'env':{'TERM':'xterm-256color'},'title':'Actual AI Workflow Lab terminal session; synthetic data'}
    with (out/'terminal.cast').open('w') as f:
        f.write(json.dumps(header)+'\n')
        for ev in events:f.write(json.dumps(ev)+'\n')
    (out/'terminal_events.json').write_text(json.dumps({'recorded_at':datetime.now(timezone.utc).isoformat(),'duration':duration,'type':'Faithful replay of captured real PTY input/output','negative_test':'Invalid CSV intentionally supplied, not an unexpected AI failure','events':marks},indent=2)+'\n')
    return events,duration

def render(events,duration,out):
    screen=pyte.Screen(104,27);stream=pyte.Stream(screen);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',27);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
    dest=out/'terminal_capture.mp4';log=(out/'terminal_render.log').open('w')
    proc=subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','10','-i','-','-an','-vf','fps=30','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE,stderr=log)
    outputs=[x for x in events if x[1]=='o'];idx=0;last=None
    for frame in range(int(duration*10)):
        t=frame/10;changed=last is None
        while idx<len(outputs) and outputs[idx][0]<=t:
            stream.feed(outputs[idx][2]);idx+=1;changed=True
        if changed:
            im=Image.new('RGB',(1920,1080),'#0c111c');d=ImageDraw.Draw(im)
            d.text((62,33),'AI WORKFLOW LAB  /  ACTUAL TERMINAL RECORDING',font=small,fill='#91e5c3')
            d.text((62,70),'Synthetic data • Faithful PTY replay • Commands and results preserved',font=small,fill='#9babc0')
            d.line((62,116,1858,116),fill='#2b3a50',width=2)
            for row,line in enumerate(screen.display):d.text((62,140+row*32),line,font=font,fill='#e6edf7')
            last=im.tobytes()
            if t>duration-1:im.save(out/'terminal_verified.png')
        proc.stdin.write(last)
    proc.stdin.close();code=proc.wait();log.close()
    if code:raise RuntimeError(f'ffmpeg failed {code}')
    print(json.dumps({'video':str(dest),'duration':duration,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--render-only',action='store_true');a=p.parse_args();out=ROOT/'episodes/EP001';out.mkdir(exist_ok=True,parents=True)
    if a.render_only:
        events=[json.loads(x) for x in (out/'terminal.cast').read_text().splitlines()[1:]];duration=json.loads((out/'terminal_events.json').read_text())['duration']
    else:events,duration=asyncio.run(capture(out))
    render(events,duration,out)
