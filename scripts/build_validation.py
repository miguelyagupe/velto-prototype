"""Assemble a disclosed technical validation from a real terminal capture.
The current channel episode spec is separate: this is not EP001 final.
"""
import json,subprocess,wave,textwrap,hashlib,argparse
from pathlib import Path
from piper import PiperVoice
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'episodes/EP001'
LINES=[
'This technical test uses real commands and synthetic sales data.',
'The first calculation returns twelve thousand across six monthly entries.',
'Here is the exact change: June increases from three thousand to forty five hundred.',
'Running the calculation again produces a total of thirteen thousand five hundred.',
'We deliberately supply invalid input. The program rejects it with an error.',
'Restoring the original data returns the original total. The result is reproducible.',
'Sorting changes the order of the bars, while preserving the underlying values.',
'The filter keeps three months. Their combined total is seven thousand five hundred.',
'This structured output contains the same calculation, ready for another tool to consume.',
'A separate test checks the original app calculations, invalid input and filtering.',
'The production engine exposes three operations: validate the timeline, render, and check quality.',
'Fourteen tests pass here, including an actual video render, decode and audio check.',
'The encoder is FFmpeg. This footage replays a real recorded terminal session.',
'The source hashes preserve provenance. This validates components, not a finished autonomous channel.'
]
def run(a):subprocess.run([str(x) for x in a],check=True)
def stamp(t):
 m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
def build(model):
 voice=PiperVoice.load(model);ev=json.loads((OUT/'terminal_events.json').read_text())['events'];bounds=[0]+[e['in'] for e in ev[1:]]+[75.4]
 voice_dir=OUT/'voice_parts';voice_dir.mkdir(exist_ok=True);cues=[];parts=[];scenes=[];logs=[]
 for i,line in enumerate(LINES):
  start,end=bounds[i:i+2];length=end-start;raw=voice_dir/f'{i:02}-raw.wav';fit=voice_dir/f'{i:02}.wav'
  with wave.open(str(raw),'wb') as w:voice.synthesize_wav(line,w)
  with wave.open(str(raw)) as w:dur=w.getnframes()/w.getframerate()
  speed=max(.8,min(1.5,dur/(length-.35)))
  run(['ffmpeg','-v','error','-y','-i',raw,'-af',f'atempo={speed},apad','-t',length,'-ar','48000','-ac','1',fit])
  parts.append(fit);logs.append({'text':line,'start':start,'end':end,'raw_duration':dur,'tempo':speed})
  cues.append(f'{i+1}\n{stamp(start)} --> {stamp(end-.03)}\n'+textwrap.fill(line,48))
  scene={'source':'terminal_capture.mp4','in':start,'out':end,'destination':start,'license':'Original real terminal session; synthetic data','proof_id':'terminal'}
  if i in (1,3,4,7):scene['crop']={'x':40,'y':120,'width':1600,'height':900}
  scenes.append(scene)
 with wave.open(str(OUT/'validation_voice.wav'),'wb') as target:
  target.setparams((1,2,48000,0,'NONE','not compressed'))
  for part in parts:
   with wave.open(str(part)) as s:target.writeframes(s.readframes(s.getnframes()))
 (OUT/'validation_voice.srt').write_text('\n\n'.join(cues)+'\n')
 (OUT/'validation_script.txt').write_text('\n'.join(LINES)+'\n')
 (OUT/'validation_voice.json').write_text(json.dumps({'provider':'local Piper','voice':'en_US-ljspeech-medium','synthetic':True,'paid_generation_calls':0,'commercial_rights':'LJ Speech public-domain dataset per model card; final distribution review pending','alignment':'sentence segments fitted to measured source intervals, not word-level forced alignment','segments':logs,'model_sha256':hashlib.sha256(Path(model).read_bytes()).hexdigest()},indent=2))
 (OUT/'proofs.json').write_text(json.dumps({'proofs':[{'id':'terminal','path':'terminal.cast','claim':'Actual recorded terminal inputs and outputs; see terminal_events.json. Controlled invalid input is intentional.'}]},indent=2))
 (OUT/'validation_timeline.json').write_text(json.dumps({'version':1,'width':1920,'height':1080,'fps':30,'narration':'validation_voice.wav','captions':'validation_voice.srt','proofs':'proofs.json','scenes':scenes},indent=2))
 print('Built validation assets; duration 75.4 seconds')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('model');a=p.parse_args();build(a.model)
