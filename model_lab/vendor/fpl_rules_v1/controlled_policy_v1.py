"""Experimental node-limited adapter. Old source files remain untouched.

Fresh process with one HiGHS thread required. Node limits control search work,
not elapsed time, LP work, memory or total multi-call manager effort. No fallback
or retry is performed here; no incumbent and call-budget exhaustion fail closed.
"""
from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, time, warnings
from dataclasses import dataclass
from pathlib import Path
sys.dont_write_bytecode = True  # Old read-only modules must never gain .pyc files.
import numpy as np
import scipy
from scipy.optimize import milp
from scipy.optimize._highspy import _core

OLD = Path(__file__).resolve().parents[2]/'fpl_simulator_2026_10_13'
VERSION='controlled_nodes_v3'

class ControlledSolverError(ValueError):
    """Must propagate past frozen planner's RuntimeError keep-plan fallback."""
    pass
EXPECTED={
 'engine.py':'1ebd69de4bdc0b8535bbe8ecc14d67a3c09db1940e4d25f0e3384e6e810852ce',
 'planner.py':'0b1e7ee711958f0d8e1865d7b2df3461bb228d06d540afe74112e11b5805b3e8',
 'initial_optimizer.py':'bfe9cba33d0cba3e7a1cacba6141123d1dbbc6c2de3a6cf49419ad24762c39cd',
 'policy.py':'df50227cdacccc1a78c86f4a7ae073d3287c331b357419fa5dd254929905a901'}

def clean(v):
    if isinstance(v,dict):return {str(k):clean(x)for k,x in v.items()}
    if isinstance(v,set):return [clean(x)for x in sorted(v)]
    if isinstance(v,(tuple,list)):return [clean(x)for x in v]
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,Path):return str(v)
    return v

def digest(v):return hashlib.sha256(json.dumps(clean(v),sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def action(choice):
    return {k:clean(choice[k])for k in ['squad','starters','bench','captain','vice','incoming','outgoing','transfers','paid','bank_after','prices']}

@dataclass(frozen=True)
class Budget:
    node_limit:int=16
    max_calls:int=40
    seed:int=20261014
    mip_rel_gap:float=.001
    def __post_init__(self):
        if type(self.node_limit)is not int or self.node_limit<1:raise ValueError('node_limit must be a positive integer')
        if type(self.max_calls)is not int or self.max_calls<1:raise ValueError('max_calls must be a positive integer')
        if type(self.seed)is not int or self.seed<0:raise ValueError('seed must be a nonnegative integer')
        if not np.isfinite(self.mip_rel_gap) or not 0<=self.mip_rel_gap<=1:raise ValueError('invalid gap')

class ControlledPolicy:
    def __init__(self,budget=Budget(),event_sink=None):
        self.budget=budget;self.ledger=[];self.event_sink=event_sink
        self.options={'node_limit':budget.node_limit,'mip_rel_gap':budget.mip_rel_gap,
                      'threads':1,'parallel':'off','random_seed':budget.seed,'presolve':True}
        high=_core._Highs()
        checked={}
        for key,value in self.options.items():
            native='mip_max_nodes' if key=='node_limit' else key
            if native=='presolve':value='on'
            status=high.setOptionValue(native,value)
            if status!=_core.HighsStatus.kOk:raise ControlledSolverError(f'Unsupported solver option {native}')
            status,actual=high.getOptionValue(native)
            if status!=_core.HighsStatus.kOk or actual!=value:raise ControlledSolverError(f'Option mismatch {native}')
            checked[native]=actual
        self.runtime={'scipy':scipy.__version__,'highs':f'{_core.HIGHS_VERSION_MAJOR}.{_core.HIGHS_VERSION_MINOR}.{_core.HIGHS_VERSION_PATCH}',
                      'verified_native_options':checked,'wallclock_limit':None,'source_hashes':EXPECTED.copy(),'adapter_sha256':file_sha(__file__)}
        # Private module instances, restored aliases. Never modify an imported
        # production planner or its on-disk source. Construction is not thread-safe.
        aliases={n:sys.modules.get(n)for n in ['engine','planner','initial_optimizer','policy']}
        modules={}
        try:
            for name in aliases:
                path=OLD/f'{name}.py'
                if file_sha(path)!=EXPECTED[path.name]:raise ControlledSolverError(f'Frozen source changed: {path.name}')
                spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
                sys.modules[name]=mod;spec.loader.exec_module(mod);modules[name]=mod
        finally:
            for name,prior in aliases.items():
                if prior is None:sys.modules.pop(name,None)
                else:sys.modules[name]=prior
        self.policy=modules['policy'];self.engine=modules['engine']
        modules['planner'].milp=self._milp;modules['initial_optimizer'].milp=self._milp

    def _milp(self,c,*,integrality=None,bounds=None,constraints=None,options=None):
        if len(self.ledger)>=self.budget.max_calls:raise ControlledSolverError('Declared total solver-call cap exhausted; no retry')
        # Hash exactly the numerical MIP, including array shapes and ordering.
        h=hashlib.sha256()
        def add(a):
            a=np.ascontiguousarray(a);h.update(str((a.dtype.str,a.shape)).encode());h.update(a.tobytes())
        add(c);add(integrality);add(bounds.lb);add(bounds.ub)
        from scipy.sparse import csc_matrix
        A=csc_matrix(constraints.A);A.sort_indices()
        for x in [A.data,A.indices,A.indptr,constraints.lb,constraints.ub]:add(x)
        row={'call':len(self.ledger)+1,'model_sha256':h.hexdigest(),'variables':len(c),'constraints':A.shape[0],
             'options':self.options.copy(),'replaced_options':dict(options or {})}
        if self.event_sink:self.event_sink(dict(event="solver_started",**row))
        started=time.perf_counter()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                result=milp(c,integrality=integrality,bounds=bounds,constraints=constraints,options=self.options.copy())
        except Exception as exc:
            row.update(seconds=time.perf_counter()-started,termination_class='native_exception',error_type=type(exc).__name__,error=str(exc))
            self.ledger.append(row)
            if self.event_sink:self.event_sink(dict(event='solver_failed',**row))
            raise ControlledSolverError('Native MILP exception; no fallback or retry') from exc
        invalid=[]
        def finite_metric(name,value,integer=False):
            if value is None:return None
            try:
                value=float(value)
                if not np.isfinite(value) or (integer and value!=round(value)):raise ValueError()
                return int(value) if integer else value
            except (TypeError,ValueError,OverflowError):
                invalid.append(name);return None
        row.update(seconds=time.perf_counter()-started,status=int(result.status),message=str(result.message),
                   objective=finite_metric('objective',result.fun),
                   nodes=finite_metric('nodes',getattr(result,'mip_node_count',None),True),
                   gap=finite_metric('gap',getattr(result,'mip_gap',None)),
                   dual_bound=finite_metric('dual_bound',getattr(result,'mip_dual_bound',None)),
                   warnings=[str(w.message)for w in caught],has_incumbent=result.x is not None)
        x=None if result.x is None else np.asarray(result.x,dtype=float)
        x_finite=x is not None and x.shape==np.asarray(c).shape and np.isfinite(x).all()
        row.update(solution_finite=bool(x_finite),max_integrality_residual=None,max_bound_violation=None,
                   max_constraint_violation=None,full_mip_feasible=False)
        if x is not None:row['raw_solution_sha256']=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
        if x_finite:
            integer=np.broadcast_to(np.asarray(integrality)!=0,x.shape)
            row['integer_solution_sha256']=digest(np.rint(x[integer]).astype(int).tolist())
            row['max_integrality_residual']=finite_metric('integrality_residual',np.max(np.abs(x[integer]-np.rint(x[integer]))) if integer.any() else 0.)
            ax=A@x
            row['max_bound_violation']=finite_metric('bound_violation',max(0.,np.max(np.asarray(bounds.lb)-x),np.max(x-np.asarray(bounds.ub))))
            row['max_constraint_violation']=finite_metric('constraint_violation',max(0.,np.max(np.asarray(constraints.lb)-ax),np.max(ax-np.asarray(constraints.ub))))
            residuals=[row[k] for k in ('max_integrality_residual','max_bound_violation','max_constraint_violation')]
            row['full_mip_feasible']=all(v is not None and v<=1e-6 for v in residuals)
        # Native HiGHS node stop (16) is status 4 in SciPy 1.18. Never accept
        # arbitrary errors, wallclock stops, missing or nonfinite telemetry.
        node_stop=(int(result.status)==4 and 'HiGHS Status 16: Solution limit reached' in str(result.message))
        row['termination_class']='optimal_within_gap' if result.status==0 else ('node_limit_incumbent' if node_stop and x_finite else 'failure')
        row['invalid_result_fields']=invalid
        if invalid or any(row[k] is None for k in ('objective','nodes','gap','dual_bound')):
            row['termination_class']='failure'
        self.ledger.append(row)
        if self.event_sink:self.event_sink(dict(event="solver_finished",**row))
        if result.x is None or row['termination_class']=='failure' or not row.get('full_mip_feasible',False):
            raise ControlledSolverError('Solver failed controlled incumbent/termination/feasibility contract; no retry')
        if row['nodes'] is not None and row['nodes']>self.budget.node_limit:
            raise ControlledSolverError('Solver exceeded declared node limit')
        return result

    def plan(self,pool,xp,state,gw,chip=None,fixed=None):
        """Existing common policy numerical objective; only solver effort changes."""
        choice,score,_=self.policy.select_plan(pool,xp,copy.deepcopy(state),gw,fixed or {},chip)
        after,validated=self.engine.apply_decision(state,choice,pool.to_dict('records'),gw,chip)
        return {'chip':chip,'choice':clean(validated),'state_after':clean(after),'prospective_score':float(score),
                'action_sha256':digest(action(validated)),'state_sha256':digest(after)}

    def decide(self,pool,xp,state,gw,fixed=None):
        """All available chips, same old manager rule and no outcomes accepted."""
        remaining=self.engine.available_chips(state,gw)
        chip,choice,audit,_=self.policy.decide(pool,xp,copy.deepcopy(state),gw,fixed or {},remaining,state['last_chip'])
        after,validated=self.engine.apply_decision(state,choice,pool.to_dict('records'),gw,chip)
        return {'chip':chip,'choice':clean(validated),'state_after':clean(after),'chip_candidates':clean(audit),
                'action_sha256':digest(action(validated)),'state_sha256':digest(after)}
