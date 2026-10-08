"""Exact conservation only; a missing parent is not a zero parent."""
import math

def exhausts(total,values):
 if total is None or not math.isfinite(total) or total<0 or total%1:return False
 known=[v for v in values if v is not None and not math.isnan(v)]
 if any(not math.isfinite(v) or v<0 or v%1 for v in known):return False
 return sum(known)==total

def cbi(values):
 if len(values)!=3 or any(v is None or not math.isfinite(v) or v<0 or v%1 for v in values):return None
 return sum(values)

def legacy_net(won,total):
 if any(v is None or not math.isfinite(v) or v<0 or v%1 for v in [won,total]) or won>total:return None
 return 2*won-total
