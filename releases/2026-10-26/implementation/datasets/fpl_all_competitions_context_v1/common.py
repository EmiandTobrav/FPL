"""Shared, season-aware source and identity configuration."""
import csv,gzip,lzma,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timedelta,timezone
P=Path(__file__).resolve().parent;R=P.parents[1]
PILOT=R/'datasets/fpl_international_calendar_2025_26_v1';CUP=R/'datasets/fpl_external_matches_pilot_2025_26_v1'
MASTER=R/'datasets/fpl_master_enriched_v1'
s=importlib.util.spec_from_file_location('cup_base',CUP/'build.py');cup=importlib.util.module_from_spec(s);s.loader.exec_module(cup)
cup.ALIASES.update({'Leicester City':'Leicester','Sheffield United':'Sheffield Utd','Norwich City':'Norwich','West Bromwich Albion':'West Brom'})
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def truth(s):return str(s).lower() in ['true','1','1.0']
def num(s):return str(int(float(s)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 op=gzip.open if str(p).endswith('.gz') else lzma.open if str(p).endswith('.xz') else open
 with op(p,'rt') as f:yield from csv.DictReader(f)
def write(name,rows,fields=None):
 it=iter(rows);first=next(it,None)
 if first is None and fields is None:raise ValueError(name+' has no rows')
 op=gzip.open if name.endswith('.gz') else lzma.open if name.endswith('.xz') else open
 with op(P/name,'wt',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(first));w.writeheader()
  if first is not None:w.writerow(first)
  w.writerows(it)
def config():
 seasons={};rounds={};members={}
 for row in read(MASTER/'player_matches.csv.xz'):
  season=row['season'];t=dt(row['fixture_kickoff_time']);gw=int(float(row['round']));code=num(row['code'])
  z=seasons.setdefault(season,dict(first=t,last=t,clubs=set()));z['first']=min(z['first'],t);z['last']=max(z['last'],t);z['clubs'].add(row['historical_team'])
  rounds[(season,gw)]=min(rounds.get((season,gw),t),t)
  members.setdefault((season,code),set()).add(row['historical_team'])
 for season,z in seasons.items():
  year=int(season[:4]);z['start']=datetime(year,9 if season=='2020-21' else 7,1,tzinfo=timezone.utc)
  z['history_start']=min(z['start'],z['first']-timedelta(days=90));z['end']=z['last']+timedelta(days=1)
 return seasons,rounds,members
def metadata():
 meta={};teams={}
 for file in sorted((R/'FPL_training_dataset/research/current/project/data').glob('*_players.csv.gz')):
  season=file.name.split('_')[0];meta[season]={num(r['code']):r for r in read(file)}
  teams[season]={str(int(float(r['id']))):r['name'] for r in read(file.with_name(season+'_teams.csv.gz'))}
 live=json.loads((PILOT/'raw/current_fpl_bootstrap.json').read_text())
 for row in live['elements']:
  m={k:str(v) if v is not None else '' for k,v in row.items()};m['team']=str(row['team']);m['id']=str(row['id']);meta['2026-27'][num(row['code'])]=m
 return meta,teams
CLUB_LEAGUES={'eng.fa':'FA Cup','eng.league_cup':'EFL Cup','uefa.champions':'UEFA Champions League','uefa.europa':'UEFA Europa League','uefa.europa.conf':'UEFA Conference League','uefa.champions_qual':'UEFA Champions League qualifying','uefa.europa_qual':'UEFA Europa League qualifying','uefa.europa.conf_qual':'UEFA Conference League qualifying'}
INT_LEAGUES=['fifa.worldq.uefa','fifa.worldq.conmebol','fifa.worldq.concacaf','fifa.worldq.afc','fifa.worldq.caf','fifa.worldq.ofc','fifa.wcq.ply','fifa.friendly','uefa.nations','caf.nations','caf.nations_qual','concacaf.gold','concacaf.nations.league','uefa.euro_u21','uefa.euro_u21_qual','fifa.friendly_u21','fifa.world.u20','fifa.world.u17','uefa.euro.u19','afc.cupq','caf.cosafa','fifa.world','uefa.euro','uefa.euroq','conmebol.america','afc.cup','fifa.olympics','concacaf.gold_qual','fifa.conmebol.olympicsq','fifa.concacaf.olympicsq','afc.saff.championship']
def locate(filename):
 for root in [P/'raw',PILOT/'raw',CUP/'raw']:
  path=root/filename
  if path.exists():return path
 return P/'raw'/filename
