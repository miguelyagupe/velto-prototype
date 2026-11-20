"""Zero-credit prototype TTS. Production rights/service stability require review."""
import argparse, asyncio, json, subprocess, pathlib, time
import edge_tts

def stamp(s):
 m=round(s*1000); return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
async def synth(text, output, voice='en-US-GuyNeural', rate='+0%'):
 output=pathlib.Path(output); output.parent.mkdir(parents=True,exist_ok=True)
 words=[]; started=time.monotonic()
 stream=edge_tts.Communicate(text,voice,rate=rate,boundary='WordBoundary')
 with output.with_suffix('.mp3').open('wb') as f:
  async for c in stream.stream():
   if c['type']=='audio':f.write(c['data'])
   elif c['type']=='WordBoundary':words.append({'text':c['text'],'start':c['offset']/1e7,'end':(c['offset']+c['duration'])/1e7})
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(output.with_suffix('.mp3')),'-ar','48000','-ac','1',str(output)],check=True)
 cues=[]
 for i in range(0,len(words),7):
  chunk=words[i:i+7];cues.append(f'{len(cues)+1}\n{stamp(chunk[0]["start"])} --> {stamp(chunk[-1]["end"])}\n'+ ' '.join(w['text'] for w in chunk))
 output.with_suffix('.srt').write_text('\n\n'.join(cues)+'\n')
 output.with_suffix('.words.json').write_text(json.dumps(words,indent=2))
 output.with_suffix('.voice.json').write_text(json.dumps({'provider':'Microsoft Edge online via edge-tts','voice':voice,'synthetic':True,'rate':rate,'paid_credits_used':0,'commercial_rights_status':'not_verified; prototype only','elapsed_seconds':time.monotonic()-started},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('text');p.add_argument('output');p.add_argument('--rate',default='+0%');a=p.parse_args();asyncio.run(synth(pathlib.Path(a.text).read_text(),a.output,rate=a.rate))
