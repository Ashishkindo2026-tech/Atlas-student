from autonomy.simulation_engine import SimulationEngine, SimulationResult
from autonomy.goal_decomposition import GoalDecomposer
from autonomy.strategy_memory import StrategyMemory
from autonomy.tool_factory import ToolFactory
from autonomy.mission_mode import Mission, MissionMode

def test_simulation_compare():
    r=SimulationEngine().compare(['a','b'], lambda p: SimulationResult(p, 2 if p=='b' else 1, 1, {}, [])); assert r[0].name=='b'

def test_goal_dependencies():
    tasks=GoalDecomposer().decompose('x',['research','build']); assert tasks[1].dependencies=={'task-1'}; assert tasks[0].id=='task-1'

def test_strategy_memory():
    s=StrategyMemory(); s.record('a',True,1); s.record('b',False); assert s.best().strategy=='a'

def test_tool_factory_requires_approval():
    p=ToolFactory().propose('csv','analyze csv',['plugins/csv.py']); assert not p.approved; ToolFactory().approve(p); assert p.approved

def test_mission_stops_without_approval():
    m=Mission('goal'); out=MissionMode().run(m,lambda _: {'next_action':'x'},lambda _: {},lambda r,s:s); assert out.get('next_action')=='x' and not m.completed
