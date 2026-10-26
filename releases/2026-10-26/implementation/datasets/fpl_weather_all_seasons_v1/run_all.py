"""Run the same explicitly selected stage for each included season."""
import argparse
import subprocess
import sys
from pathlib import Path

BASE=Path(__file__).resolve().parent
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2027)]
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','fetch','build','verify'])
    args=parser.parse_args()
    for season in SEASONS:
        name='verify_independently.py' if args.stage=='verify' else 'weather.py'
        command=[sys.executable,str(BASE/name)]
        if args.stage!='verify':command.append(args.stage)
        subprocess.run(command+['--season',season],check=True)
