"""Fixture effects; no outcomes or future player states accepted at inference."""
import numpy as np

def design(mean,minutes,team_gf,team_ga,home,opp_ga,opp_gf):
    mean=np.nan_to_num(np.asarray(mean,float),nan=2.)
    exposure=np.clip(np.nan_to_num(np.asarray(minutes,float),nan=45.)/90,0,1)
    clean=lambda x: np.nan_to_num(np.asarray(x,float),nan=1.35)-1.35
    return np.column_stack([np.ones(len(mean)),mean,exposure,clean(team_gf),clean(team_ga),exposure*(np.asarray(home)-.5),exposure*clean(opp_ga),exposure*clean(opp_gf)])

def effect(pos,minutes,home,opp_ga,opp_gf,coefficients,variant):
    pos=np.asarray(pos); exposure=np.clip(np.nan_to_num(np.asarray(minutes,float),nan=45.)/90,0,1)
    out=np.zeros(len(pos))
    for k,b in coefficients.items():
        ix=pos==int(k); b=np.asarray(b)
        if variant in ['venue','full']:out[ix]+=b[5]*exposure[ix]*(home-.5)
        if variant in ['opponent','full']:out[ix]+=exposure[ix]*(b[6]*(opp_ga-1.35)+b[7]*(opp_gf-1.35))
    return np.clip(out,-2,2)

def assemble(base,current_effect,fixture_effects,age_days):
    """fixture_effects[j] is a list of per-player effect vectors for each club fixture.
    Each vector has NaN for players whose club is not in that fixture.
    """
    result=np.asarray(base,float).copy()
    if age_days>14:return result
    for j,fx in fixture_effects.items():
        result[:,j]=0
        for e in fx:
            e=np.asarray(e);mask=np.isfinite(e)
            result[mask,j]+=np.maximum(0,base[mask,j]-current_effect[mask]*(.5**j)+e[mask])
    return result
