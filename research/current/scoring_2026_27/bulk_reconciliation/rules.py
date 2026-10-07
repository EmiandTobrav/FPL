"""Nonnegative conservation: no global missing-to-zero substitution."""
import math

def number(x):
 return isinstance(x,(int,float)) and math.isfinite(x) and x>=0 and int(x)==x

def residual(total,values):
 """Return zeros only if explicit nonnegative contributions exhaust total."""
 if not number(total):return None,'missing_or_invalid_team_total'
 known=[v for v in values if v is not None and not (isinstance(v,float) and math.isnan(v))]
 if any(not number(v) for v in known):return None,'invalid_player_counter'
 subtotal=sum(known)
 if subtotal>total:return None,'aggregate_conflict'
 if subtotal<total:return None,'unallocated_positive_residual'
 return 0,'explicit_team_total_exhausted'

def zero_subset(parent):return 0 if number(parent) and parent==0 else None

def signed_net(total,won):
 if not number(total) or not number(won) or won>total:return None
 return int(2*won-total)
