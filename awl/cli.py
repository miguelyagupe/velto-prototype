import argparse
import json
import sys
from .engine import validate,render,qa

def main():
    parser=argparse.ArgumentParser(prog='awl')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('validate'); p.add_argument('timeline')
    p=sub.add_parser('render'); p.add_argument('timeline'); p.add_argument('--output',required=True)
    p=sub.add_parser('qa'); p.add_argument('video'); p.add_argument('--timeline')
    args=parser.parse_args()
    try:
        if args.command=='validate':
            v=validate(args.timeline); result={'valid':True,'duration_seconds':v['duration'],'scene_count':len(v['scenes'])}
        elif args.command=='render':
            r=render(args.timeline,args.output); result={k:r[k] for k in ('status','duration_seconds','render_elapsed_seconds','output_sha256')}
        else:
            r=qa(args.video,args.timeline); result={k:r[k] for k in ('technical_pass','editorial_approved','errors','warnings')}
        print(json.dumps(result,indent=2))
        if args.command=='qa' and not result['technical_pass']: sys.exit(1)
    except Exception as exc:
        print(json.dumps({'error':str(exc),'type':type(exc).__name__}),file=sys.stderr);sys.exit(2)
