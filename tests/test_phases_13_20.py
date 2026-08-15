from intelligence.knowledge_network import KnowledgeNetwork, KnowledgeNode
from intelligence.gamification import GameProfile
from intelligence.collaboration import StudyGroup
from intelligence.reasoning_lab import ReasoningLab
from intelligence.multi_agent import MultiAgentAtlas
from intelligence.self_improvement import SelfImprovement

def test_knowledge_network():
    g = KnowledgeNetwork(); g.add_concept(KnowledgeNode('vectors','Vectors','Physics',.4)); g.add_concept(KnowledgeNode('trig','Trigonometry','Math',.8)); g.connect('trig','vectors','prerequisite')
    assert g.prerequisites('vectors') == ['trig']; assert len(g.gaps()) == 1

def test_gamification():
    p=GameProfile(); p.award_xp(250); assert p.level == 3

def test_collaboration_opt_in():
    g=StudyGroup('g', {'a'}, sharing_enabled=False); assert not g.share('a','note'); g.sharing_enabled=True; assert g.share('a','note')

def test_reasoning():
    r=ReasoningLab().review('x', lambda _: {'correct':False,'gaps':['assumption'],'hints':['check premise']}); assert r.retry_required

def test_multi_agent():
    class A:
        def run(self, x): return x+1
    assert MultiAgentAtlas({'tutor':A()}).dispatch('tutor', 2).result == 3

def test_self_improvement():
    s=SelfImprovement(); s.record('visual',True,1); s.record('text',False,0); assert s.best_strategy() == 'visual'
