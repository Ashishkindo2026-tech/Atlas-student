from student.phase_21_30 import Atlas30, RealTimeContext

def test_realtime_router():
    a=Atlas30(); assert a.context.choose_action(RealTimeContext(subject='Physics',task='test',minutes_available=20,deadline='tomorrow')) == 'prioritize_deadline'

def test_socratic():
    assert Atlas30().socratic.next_step('2+2').get('reveal_solution') is False

def test_project_builder():
    p=Atlas30().projects.create('Robot',requirements=['motor']); assert p.title=='Robot' and p.requirements==['motor']

def test_permissions_default_off():
    c=Atlas30().controls; assert not c.camera and not c.microphone and not c.internet

def test_why_engine():
    assert len(Atlas30().why.ask('vectors')['why_questions']) == 4

def test_autonomous_pipeline():
    r=Atlas30().autonomous.prepare('physics test',60,{'weak':['vectors']}); assert r['steps'][0]=='analyze_history' and r['steps'][-1]=='report'
