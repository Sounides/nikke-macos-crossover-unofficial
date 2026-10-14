#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
import argparse,csv,json,statistics
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('csv');ap.add_argument('--start',type=float);ap.add_argument('--end',type=float);ap.add_argument('--seconds',type=float,default=60);a=ap.parse_args()
rows=[r for r in csv.DictReader(Path(a.csv).open()) if all(v is not None and v != '' for v in r.values())];valid=sorted(set(float(r['presented_s']) for r in rows if float(r['presented_s'])>0));
if not valid:raise SystemExit('No actual presentation timestamps yet')
end=a.end or valid[-1];start=a.start or end-a.seconds;ts=[t for t in valid if start<=t<=end]
if len(ts)<2:raise SystemExit('Need two positive presentation times in phase')
dt=[(y-x)*1000 for x,y in zip(ts,ts[1:])];d=sorted(dt)
def q(f):return d[min(int((len(d)-1)*f),len(d)-1)]
out={'start_s':ts[0],'end_s':ts[-1],'window_s':ts[-1]-ts[0],'frames':len(ts),'fps':(len(ts)-1)/(ts[-1]-ts[0]),'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99),'worst_ms':max(dt),'intervals_gt_20ms':sum(t>20 for t in dt),'intervals_gt_33_4ms':sum(t>33.4 for t in dt),'zero_callbacks_in_phase':sum(float(r['presented_s'])==0 and start<=float(r['acquired_s'])<=end for r in rows),'surface':{k:v for k,v in next(r for r in reversed(rows) if start <= float(r['presented_s']) <= end).items() if k!='presented_s'}}
print(json.dumps(out,indent=2))
