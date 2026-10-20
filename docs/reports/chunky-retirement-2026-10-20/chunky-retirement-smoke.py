from pathlib import Path
import subprocess,threading,queue,time,json,re,os,sys
variant=sys.argv[1];jar=Path(sys.argv[2]);stage=Path('/tmp/chunky-retirement-'+variant);stage.mkdir(exist_ok=False)
(stage/'eula.txt').write_text('eula=true\n')
(stage/'server.properties').write_text('server-ip=127.0.0.1\nserver-port=25566\nonline-mode=false\nenforce-secure-profile=false\nwhite-list=false\nview-distance=2\nsimulation-distance=2\npause-when-empty-seconds=-1\nmanagement-server-enabled=false\nlevel-seed=1\n')
(stage/'mods').mkdir()
import zipfile
for src in Path('/tmp/chunky-retirement-current-modfarm').read_text().strip(),:
 for mod in Path(src).glob('*.jar'):
  with zipfile.ZipFile(mod) as z: ident=json.loads(z.read('fabric.mod.json'))['id']
  (stage/'mods'/mod.name).symlink_to(jar if ident=='chunky' else mod)
(stage/'config/chunky').mkdir(parents=True)
(stage/'config/chunky/config.json').write_text(json.dumps(dict(version=2,language='en',continueOnRestart=True,forceLoadExistingChunks=False,silent=False,updateInterval=1)))
(stage/'config/c2me.toml').write_text('version = 3\nglobalExecutorParallelism = 4\n')
launcher='/nix/store/z3x5r4lcpr7x20nkpghfb4bcxyv2dhs4-minecraft-server/bin/minecraft-server'
gate=str(stage/'retire');q=queue.Queue();p=None;client=None;logfile=None
results={'variant':variant,'gated_old_center':0,'replacement_center':9000}
def start():
 global p,q,logfile
 q=queue.Queue();logfile=(stage/'console-all.log').open('a')
 p=subprocess.Popen([launcher,'-Xms256M','-Xmx3G','-XX:+UseG1GC','-Dchunky.test.retirementGate='+gate],cwd=stage,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
 def read():
  for line in p.stdout:logfile.write(line);logfile.flush();q.put(line)
 threading.Thread(target=read,daemon=True).start()
 wait('Done (')
def wait(value,timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  try:l=q.get(timeout=1)
  except queue.Empty:
   if p.poll() is not None:raise RuntimeError('server exited '+str(p.returncode))
   continue
  if value in l:return l.strip()
 raise TimeoutError(value)
def cmd(*commands):
 for c in commands:p.stdin.write(c+'\n')
 p.stdin.flush()
def stop():
 if p and p.poll() is None:
  cmd('stop')
  try:p.wait(timeout=40)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
 if logfile:logfile.close()
def prop(world):
 f=stage/('config/chunky/tasks/minecraft/'+world+'.properties')
 return dict(l.split('=',1) for l in f.read_text().splitlines() if '=' in l)
def progress(text):
 ans={}
 for m in re.finditer(r'Task running for (\S+)\. Processed: (\d+) chunks',text):ans[m[1]]=int(m[2])
 return ans
def join():
 global client
 ready=stage/'Alice.ready';ready.unlink(missing_ok=True)
 client=subprocess.Popen([sys.executable,'/tmp/chunky-multiplayer-client.py','Alice',str(ready)],env=dict(os.environ,PYTHONPATH='/etc/nixos/packages/minecraft-tools/src'),stdout=(stage/'client.log').open('a'),stderr=subprocess.STDOUT)
 wait('Alice joined the game',90)
 end=time.monotonic()+30
 while not ready.exists():
  assert client.poll() is None,(stage/'client.log').read_text()
  assert time.monotonic()<end
  time.sleep(.1)
 cmd('gamemode spectator Alice','execute in minecraft:overworld run tp Alice 9000 150 0','function chunky_offline:track')
def leave():
 client.terminate();client.wait(timeout=10);wait('Alice left the game',30)
try:
 start()
 for world,center,radius in [('overworld',0,10000),('the_nether',100,1250),('the_end',1000,5000)]:
  cmd(f'chunky start minecraft:{world} square {center} 0 {radius}','chunky confirm')
  wait('Task running for minecraft:'+world,60)
 # Persist a pending recenter alongside existing saved tasks, as at production startup.
 cmd('data modify storage chunky_offline:tracking overworld.lastActivityX set value 9000','data modify storage chunky_offline:tracking overworld.pending set value 1b')
 for key,center in [('nether',100),('end',1000)]:
  cmd(f'data modify storage chunky_offline:tracking {key} set value {{enabled:1b,hasTask:1b,centerX:{center},centerZ:0,lastActivityX:{center},lastActivityZ:0,pending:0b}}')
 time.sleep(.3);stop()
 Path(gate+'.armed').touch();os.mkfifo(gate+'.release');start()
 end=time.monotonic()+30
 while not Path(gate+'.reached').exists():assert time.monotonic()<end,'retirement gate not reached';time.sleep(.1)
 cmd('data get storage chunky_offline:tracking overworld','chunky selection')
 print(wait('Center: 9000'),flush=True)
 results['old_worker_held_until_replacement_registered']=True
 # Release A only after B is registered. A's cleanup now races B's lifecycle deterministically.
 fd=os.open(gate+'.release',os.O_WRONLY|os.O_NONBLOCK);os.write(fd,b'X');os.close(fd)
 end=time.monotonic()+20
 while not Path(gate+'.released').exists():assert time.monotonic()<end;time.sleep(.05)
 time.sleep(.5)
 join();time.sleep(2)
 log=stage/'logs/latest.log';before=progress(log.read_text());time.sleep(6);after=progress(log.read_text())
 changed={w:after[w]-before.get(w,after[w]) for w in after if after[w]!=before.get(w,after[w])}
 results['progress_while_online']=changed;results['saved_overworld_after_join']=prop('overworld')
 joined_log=log.read_text().split('Alice joined the game')[-1]
 results['stop_messages_after_join']={w:('Task stopped for '+w+'.') in joined_log for w in ['minecraft:overworld','minecraft:the_nether','minecraft:the_end']}
 if variant!='baseline':assert all(results['stop_messages_after_join'].values()),results['stop_messages_after_join']
 print(json.dumps(results,indent=2),flush=True)
 if variant=='baseline':
  assert changed.get('minecraft:overworld',0)>0,'baseline race did not reproduce'
  assert prop('overworld')['center-x']=='0.0','old checkpoint was not observed'
  results['outcome']='EXPECTED_FAIL: orphan Overworld generates online; old checkpoint overwrote new lifecycle'
  leave()
 else:
  assert not changed,changed
  assert prop('overworld')['center-x']=='9000.0' and prop('overworld')['cancelled']=='false'
  before_leave=after;leave()
  deadline=time.monotonic()+60
  while True:
   cmd('chunky progress');time.sleep(1)
   resumed=progress(log.read_text())
   if all(resumed.get(w,0)>before_leave.get(w,0) for w in ['minecraft:overworld','minecraft:the_nether','minecraft:the_end']):break
   assert time.monotonic()<deadline,('resume observation timed out',resumed,before_leave)
  for world in ['minecraft:overworld','minecraft:the_nether','minecraft:the_end']:
   assert resumed.get(world,0)>before_leave.get(world,0),(world,resumed,before_leave)
  results['all_dimensions_resume']=True
  stop();start();time.sleep(3)
  cmd('data get storage chunky_offline:tracking overworld','chunky progress')
  time.sleep(1)
  assert prop('overworld')['center-x']=='9000.0'
  assert 'lastActivityX: 9000' in log.read_text()
  resumed_after_restart=progress(log.read_text());assert set(resumed_after_restart)==set(resumed),resumed_after_restart
  results['restart_correct_target']=True;results['outcome']='PASS'
finally:
 if client and client.poll() is None:client.terminate();client.wait(timeout=10)
 stop()
 (stage/'result.json').write_text(json.dumps(results,indent=2)+'\n')
print(results['outcome'],flush=True)
