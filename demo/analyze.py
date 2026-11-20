"""Original synthetic CSV calculation experiment; console rendering is real output."""
import argparse,csv,json
from pathlib import Path

def summarize(path, minimum=0, order='input'):
    with open(path,newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['month','sales']:raise ValueError('Header must be month,sales')
        rows=[]
        for i,row in enumerate(reader,2):
            try: value=float(row['sales'])
            except (TypeError,ValueError):raise ValueError(f'Row {i}: sales must be numeric')
            if value<0:raise ValueError(f'Row {i}: sales must be non-negative')
            if value>=minimum:rows.append({'month':row['month'],'sales':value})
    if order!='input':rows.sort(key=lambda r:r['sales'],reverse=order=='desc')
    total=sum(r['sales'] for r in rows)
    return {'rows':rows,'total':total,'mean':total/len(rows) if rows else 0,'count':len(rows)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--minimum',type=float,default=0);p.add_argument('--order',choices=['input','asc','desc'],default='input');p.add_argument('--json',action='store_true');a=p.parse_args()
    try:r=summarize(a.csv,a.minimum,a.order)
    except ValueError as e:p.exit(2,'VALIDATION ERROR: '+str(e)+'\n')
    if a.json:print(json.dumps(r,indent=2))
    else:
        print('\nSYNTHETIC SALES / computed locally\n')
        maximum=max((x['sales'] for x in r['rows']),default=1)
        for row in r['rows']:print(f"{row['month']:>5}  {'█'*round(row['sales']/maximum*48):48} {row['sales']:8,.0f}")
        print(f"\nTOTAL {r['total']:,.0f}    MEAN {r['mean']:,.0f}    ROWS {r['count']}\n")
