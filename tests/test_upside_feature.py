from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from upside_feature.policy import captain_choice

def test_captain_gate_excludes_high_tail_outside_mean_margin():
    assert captain_choice([1,2,3],{1:6,2:5.5,3:5.49},{1:1,2:2,3:99},1,2)==(2,1)

def test_captain_gate_preserves_vice_when_unchanged_and_breaks_ties():
    assert captain_choice([3,2,1],{1:6,2:6,3:5.9},{1:2,2:2,3:2},1,2)==(1,2)

def test_captain_gate_ignores_players_outside_starting_xi():
    assert captain_choice([1,2],{1:6,2:5,3:10},{1:1,2:2,3:99},1,2)==(1,2)
