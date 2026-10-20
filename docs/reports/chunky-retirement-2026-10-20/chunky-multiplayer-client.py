import importlib.util,sys,time,argparse
from pathlib import Path
spec=importlib.util.spec_from_file_location('probe','/etc/nixos/tests/workstation/minecraft-staging/probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.PLAYER=sys.argv[1]
original=p.Connection.__init__
def init(self,*a,**kw):
 original(self,*a,**kw);self.deadline=time.monotonic()+600
p.Connection.__init__=init
p.game_probe(argparse.Namespace(host='127.0.0.1',port=25566,expected_version='26.3',hold_seconds=550,ready_file=Path(sys.argv[2])))
