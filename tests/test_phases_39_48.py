from atlas_core.phases_39_48 import *

def test_context_fusion(): assert ContextFusion(task='study').build()['task']=='study'
def test_reasoning_verifier():
    v=ReasoningVerifier(); assert v.verify(4,[lambda x:x==4])['passed']; assert not v.verify(4,[lambda x:x==5])['passed']
def test_prediction():
    p=OutcomePredictor(); assert p.score(p.predict(lambda x:x+1,1),2)==1.0; assert p.score(2,3)==0.0
def test_protected_evolution():
    try: CapabilityEvolution().propose('core limit','rewrite',protected=True)
    except PermissionError: pass
    else: assert False
def test_federation_filters(): assert Federation().share({'a':1,'secret':2},['a'])=={'a':1}
def test_discovery(): assert DiscoveryEngine().experiment('h',1,1)['supported']; assert not DiscoveryEngine().experiment('h',1,2)['supported']
def test_meta_learning():
    m=MetaLearning(); m.record('flashcards','math',{},.8); m.record('practice','math',{},.9); assert m.best('math')['strategy']=='practice'
def test_creation(): assert 'test' in CreationEngine().plan('x')['steps']
def test_recovery_snapshot_restore(tmp_path):
    p=tmp_path/'data.txt'; p.write_text('good'); r=RecoveryManager(tmp_path); snap=r.snapshot(['data.txt']); p.write_text('broken'); assert r.restore(snap)==['data.txt']; assert p.read_text()=='good'
def test_recovery_quarantine(tmp_path):
    p=tmp_path/'bad.txt'; p.write_text('bad'); r=RecoveryManager(tmp_path); q=r.quarantine('bad.txt'); assert q.exists() and not p.exists()
def test_constitution_store(tmp_path):
    c=Constitution(); s=ConstitutionStore(tmp_path/'.atlas'/'constitution.json'); s.save(c); assert s.fingerprint(); assert s.path.exists()
