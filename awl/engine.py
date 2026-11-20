from __future__ import annotations
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

class ValidationError(ValueError):
    pass

def run(args, timeout=1800):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): {result.stderr[-5000:]}')
    return result

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',path],60).stdout)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def duration(info):
    return float(info['format']['duration'])

def streams(info,kind):
    return [s for s in info['streams'] if s['codec_type']==kind]

def number(value, name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValidationError(f'{name} must be a finite number')
    return float(value)

def file_at(base, value, field):
    if not isinstance(value,str) or not value:
        raise ValidationError(f'{field} requires a file path')
    p=(base/value).resolve()
    if not p.is_file(): raise ValidationError(f'{field}: file does not exist: {p}')
    return p

def captions(path):
    text=Path(path).read_text(encoding='utf-8-sig').strip()
    if not text: raise ValidationError('Captions are empty')
    result=[]
    def sec(t):
        h,m,s,ms=map(int,re.split('[:,]',t))
        if m>59 or s>59: raise ValidationError('Invalid caption time')
        return h*3600+m*60+s+ms/1000
    for block in re.split(r'\r?\n\s*\r?\n',text):
        lines=block.splitlines()
        if len(lines)<3 or not lines[0].isdigit(): raise ValidationError('Invalid SRT block')
        times=re.fullmatch(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})',lines[1])
        if not times: raise ValidationError('Invalid SRT timestamps')
        start,end=map(sec,times.groups())
        if end<=start or (result and start<result[-1]['end']): raise ValidationError('Captions overlap or have invalid duration')
        result.append({'start':start,'end':end,'text':'\n'.join(lines[2:])})
    return result

def validate(timeline_path, inspect_media=True):
    timeline_path=Path(timeline_path).resolve()
    d=json.loads(timeline_path.read_text())
    base=timeline_path.parent
    if d.get('version')!=1: raise ValidationError('Only timeline version 1 is supported')
    for key in ('width','height'):
        v=d.get(key)
        if not isinstance(v,int) or isinstance(v,bool) or v<2 or v%2 or v>4096:
            raise ValidationError(f'{key} must be an even integer, 2–4096')
    if d.get('fps')!=30: raise ValidationError('MVP requires 30 fps')
    narration=file_at(base,d.get('narration'),'narration')
    subs=file_at(base,d.get('captions'),'captions')
    proof_file=file_at(base,d.get('proofs'),'proofs')
    proof_data=json.loads(proof_file.read_text())
    proof_items=proof_data.get('proofs',[])
    proofs={}
    for p in proof_items:
        if not p.get('id') or not p.get('claim') or p['id'] in proofs: raise ValidationError('Proof requires unique id and claim')
        proofs[p['id']]={**p,'resolved_path':file_at(base,p.get('path'),'proof.path')}
    scenes=d.get('scenes')
    if not isinstance(scenes,list) or not scenes: raise ValidationError('At least one scene is required')
    cursor=0.0; media={}; normalized=[]
    for i,s in enumerate(scenes):
        label=f'scenes[{i}]'
        source=file_at(base,s.get('source'),label+'.source')
        start=number(s.get('in'),label+'.in'); end=number(s.get('out'),label+'.out')
        dest=number(s.get('destination'),label+'.destination')
        if start<0 or end<=start: raise ValidationError(f'{label}: invalid source interval')
        if abs(dest-cursor)>0.04: raise ValidationError(f'{label}: gap/overlap at destination; expected {cursor:.3f}')
        if not isinstance(s.get('license'),str) or not s['license'].strip(): raise ValidationError(f'{label}: license required')
        if s.get('proof_id') not in proofs: raise ValidationError(f'{label}: unknown proof_id')
        crop=s.get('crop')
        if crop:
            if set(crop)!={'x','y','width','height'}: raise ValidationError(f'{label}: crop requires x/y/width/height')
            for k,v in crop.items():
                if not isinstance(v,int) or isinstance(v,bool) or v<0 or (k in ('width','height') and (v<2 or v%2)):
                    raise ValidationError(f'{label}: invalid crop {k}')
        if s.get('overlay') is not None and not isinstance(s['overlay'],str): raise ValidationError('overlay must be text')
        if inspect_media:
            if str(source) not in media: media[str(source)]=probe(source)
            info=media[str(source)]; video=streams(info,'video')
            if not video: raise ValidationError(f'{label}: source has no video')
            if end>duration(info)+0.04: raise ValidationError(f'{label}: out exceeds source duration')
            if crop and (crop['x']+crop['width']>video[0]['width'] or crop['y']+crop['height']>video[0]['height']):
                raise ValidationError(f'{label}: crop exceeds source bounds')
        normalized.append({**s,'resolved_source':source})
        cursor+=end-start
    cues=captions(subs)
    if cues[-1]['end']>cursor+0.05: raise ValidationError('Captions extend beyond timeline')
    if inspect_media:
        audio_info=probe(narration)
        if not streams(audio_info,'audio'): raise ValidationError('Narration has no audio stream')
        if abs(duration(audio_info)-cursor)>0.3: raise ValidationError(f'Narration ({duration(audio_info):.3f}s) and timeline ({cursor:.3f}s) differ by over 0.3 seconds')
    return {'data':d,'base':base,'scenes':normalized,'duration':cursor,'narration':narration,'captions':subs,'proofs':proofs,'media':media}

def ffmpeg_filter_path(path):
    # Escape twice for FFmpeg filter grammar; ordinary spaces are safe inside quotes.
    return str(path).replace('\\','\\\\').replace(':','\\:').replace("'", "'\\''")

def render(timeline_path, output):
    v=validate(timeline_path); d=v['data']; output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    if output in [v['narration'],v['captions'],Path(timeline_path).resolve()] or output in [s['resolved_source'] for s in v['scenes']]:
        raise ValidationError('Output cannot overwrite an input')
    started=time.time(); commands=[]
    def execute(cmd):
        then=time.monotonic(); result=run(cmd)
        commands.append({'argv':[str(a) for a in cmd],'elapsed_seconds':round(time.monotonic()-then,3),'returncode':result.returncode})
    # Temporary local paths are intentional: no network or publishing from this engine.
    with tempfile.TemporaryDirectory(prefix='awl-render-',dir=output.parent) as tmp:
        temp=Path(tmp); segments=[]
        for i,s in enumerate(v['scenes']):
            part=temp/f'scene-{i:04}.mp4'; segments.append(part)
            filters=[]
            c=s.get('crop')
            if c: filters.append(f"crop={c['width']}:{c['height']}:{c['x']}:{c['y']}")
            filters += [f"scale={d['width']}:{d['height']}:force_original_aspect_ratio=decrease",f"pad={d['width']}:{d['height']}:(ow-iw)/2:(oh-ih)/2:color=0x11151c",'setsar=1','fps=30']
            if s.get('overlay'):
                title=temp/f'title-{i}.txt'; title.write_text(s['overlay'])
                fontsize=42 if d['width']>d['height'] else 46
                filters += [f"drawtext=textfile='{ffmpeg_filter_path(title)}':expansion=none:fontcolor=white:fontsize={fontsize}:x=60:y=60:box=1:boxcolor=black@0.65:boxborderw=18"]
            cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-ss',s['in'],'-i',s['resolved_source'],'-t',s['out']-s['in'],'-an','-vf',','.join(filters),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-threads','2',part]
            execute(cmd)
        concat=temp/'concat.txt'; concat.write_text(''.join(f"file '{p.name}'\n" for p in segments))
        # Move captions to safe known basename to avoid user-controlled filter expressions.
        copied_subs=temp/'captions.srt'; shutil.copyfile(v['captions'],copied_subs)
        encoded=temp/'encoded.mp4'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-f','concat','-safe','1','-i',concat,'-i',v['narration'],'-map','0:v:0','-map','1:a:0']
        if d.get('burn_captions',True):
            font=22 if d['width']>d['height'] else 18
            margin=28 if d['width']>d['height'] else 60
            cmd+=['-vf',f"subtitles='{ffmpeg_filter_path(copied_subs)}':force_style='FontName=DejaVu Sans,FontSize={font},Outline=1.5,Shadow=0,MarginV={margin},MarginL=35,MarginR=35,Alignment=2'",'-c:v','libx264','-preset','veryfast','-crf','20','-threads','2']
        else: cmd+=['-c:v','copy']
        cmd+=['-af','apad,loudnorm=I=-16:TP=-1.5:LRA=11','-t',v['duration'],'-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',encoded]
        execute(cmd); encoded.replace(output)
    shutil.copyfile(v['captions'],output.with_suffix('.srt')) if v['captions']!=output.with_suffix('.srt') else None
    asset_paths={v['narration'],v['captions'],*[s['resolved_source'] for s in v['scenes']],*[p['resolved_path'] for p in v['proofs'].values()]}
    manifest={'status':'rendered_awaiting_qa','timeline':str(Path(timeline_path).resolve()),'duration_seconds':v['duration'],'render_elapsed_seconds':round(time.time()-started,3),'output_sha256':sha256(output),'assets':[{'path':str(p),'sha256':sha256(p)} for p in sorted(asset_paths)],'commands':commands,'paid_api_calls':0,'publication_performed':False}
    output.with_suffix('.render.json').write_text(json.dumps(manifest,indent=2))
    return manifest

def qa(video, timeline_path=None):
    video=Path(video).resolve(); info=probe(video); errors=[]; warnings=[]
    v=validate(timeline_path) if timeline_path else None
    videos=streams(info,'video'); audios=streams(info,'audio')
    if len(videos)!=1 or not audios: errors.append('Expected one video and an audio stream')
    if videos:
        s=videos[0]
        if s['codec_name']!='h264' or s.get('pix_fmt')!='yuv420p': errors.append('Video must be H.264 yuv420p')
        if s.get('r_frame_rate')!='30/1': errors.append('Video must be 30 fps')
        if v and (s['width'],s['height'])!=(v['data']['width'],v['data']['height']): errors.append('Resolution mismatch')
    if audios and (audios[0]['codec_name']!='aac' or audios[0].get('sample_rate')!='48000'): errors.append('Audio must be AAC 48 kHz')
    if v and abs(duration(info)-v['duration'])>0.15: errors.append('Render duration mismatch')
    decoded=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=1800)
    if decoded.returncode or decoded.stderr.strip(): errors.append('Decode errors: '+decoded.stderr[-1000:])
    detect=run(['ffmpeg','-hide_banner','-i',video,'-vf','blackdetect=d=0.5:pix_th=0.08:pic_th=0.98','-af','silencedetect=noise=-45dB:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',detect.stderr)
    silence=re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',detect.stderr)
    if black: errors.append('Black intervals require review')
    if silence: warnings.append('Silence intervals require review')
    loudness={}
    match=re.search(r'\{\s*"input_i".*?\}',detect.stderr,re.S)
    if match:
        loudness=json.loads(match.group())
        try:
            if float(loudness['input_i']) < -24 or float(loudness['input_i']) > -12: errors.append('Integrated loudness outside -24 to -12 LUFS')
            if float(loudness['input_tp'])>0: errors.append('Audio true peak exceeds 0 dBTP')
        except (ValueError,KeyError): errors.append('Invalid loudness measurement')
    else: errors.append('Loudness unavailable')
    report={'technical_pass':not errors,'editorial_approved':False,'publishable':False,'requires_human_review':['Full playback','Narration clarity and sync','Sensitive data','Claims match proof','Vertical readability and safe areas','Rights and disclosures'],'errors':errors,'warnings':warnings,'probe':info,'black_intervals':black,'silence_intervals':silence,'loudness':loudness,'sha256':sha256(video)}
    video.with_suffix('.qa.json').write_text(json.dumps(report,indent=2))
    return report
