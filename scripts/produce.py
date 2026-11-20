"""Execute an evidence-backed episode job. Editorial planning is intentionally external.
No generated placeholder footage, paid providers or publishing actions.
"""
import argparse,asyncio,hashlib,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from awl.engine import render,qa,validate
from narrate import synth

def main(job_path):
 job_path=Path(job_path).resolve();base=job_path.parent;job=json.loads(job_path.read_text())
 manifest={'status':'preflight','events':[],'paid_generation_calls':0,'publications':0}
 def save(state,**detail):
  manifest['status']=state;manifest['events'].append({'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'state':state,**detail});(base/'production_status.json').write_text(json.dumps(manifest,indent=2))
 try:
  if job.get('budget_credits',0)!=0: raise ValueError('This worker supports zero-credit execution only')
  timeline=base/job['timeline'];d=json.loads(timeline.read_text())
  for s in d['scenes']:
   if not (timeline.parent/s['source']).is_file():raise FileNotFoundError('Real captured material is missing; refusing placeholder')
  save('materials_verified')
  if job.get('generate_prototype_voice',False):
   asyncio.run(synth((base/job['script']).read_text(),timeline.parent/d['narration']))
   save('narrated',rights='prototype_voice_rights_unverified')
  validate(timeline);save('timeline_validated')
  out=base/job['output'];r=render(timeline,out);save('rough_render',render_seconds=r['render_elapsed_seconds'])
  q=qa(out,timeline);save('technical_qa_pass' if q['technical_pass'] else 'technical_qa_failed',errors=q['errors'])
  if not q['technical_pass']:return 2
  for short in job.get('shorts',[]):
   st=base/short['timeline'];so=base/short['output'];render(st,so);sq=qa(so,st)
   if not sq['technical_pass']:raise RuntimeError('Short failed QA: '+str(so))
  save('awaiting_editorial_review',publishable=False)
  return 0
 except Exception as exc:
  save('blocked',error=str(exc));print(str(exc),file=sys.stderr);return 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('job');a=p.parse_args();sys.exit(main(a.job))
