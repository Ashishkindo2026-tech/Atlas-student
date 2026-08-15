from extension.protected_core import is_protected
from extension.self_extension import SelfExtensionEngine
from extension.capability_registry import Capability, CapabilityRegistry
from extension.debugger import SelfDebugger

def test_protected_core():
    assert is_protected('security/auth.py')
    assert is_protected('memory/memory.py')
    assert is_protected('extension/self_extension.py')
    assert not is_protected('plugins/example.py')

def test_extension_permissions_and_protected_boundary():
    e=SelfExtensionEngine(permission_level=2)
    assert e.can_edit(['plugins/example.py'], 2)
    assert not e.can_edit(['plugins/example.py'], 3)
    assert not e.can_edit(['security/auth.py'], 2)
    try: e.validate(['security/auth.py'], 'improve security')
    except PermissionError: pass
    else: assert False

def test_extension_requires_reason_and_unique_files():
    e=SelfExtensionEngine()
    try: e.validate(['plugins/a.py'], '')
    except ValueError: pass
    else: assert False
    try: e.validate(['plugins/a.py','plugins/a.py'], 'fix bug')
    except ValueError: pass
    else: assert False

def test_capability_registry():
    r=CapabilityRegistry(); r.register(Capability('voice')); r.register(Capability('calendar', risk='high'))
    assert r.has('voice'); assert not r.has('calendar')
    r.register(Capability('calendar', risk='high', approved=True)); assert r.has('calendar')

def test_debugger():
    d=SelfDebugger().diagnose('module failed', lambda _: {'cause':'bad import','fix':'repair import','tests':['import test']})
    assert d.cause == 'bad import'
    assert d.tests == ['import test']
