#!/usr/bin/env python3
"""ICDFA CCSE-102 offline Azure-style operations teaching simulator.
NOT Azure CLI, NOT connected to Microsoft Azure. Standard library only.
"""
import argparse, datetime as dt, hashlib, ipaddress, json, os, pathlib, shutil, sys, uuid

ROOT = pathlib.Path(__file__).resolve().parent
STATE_DIR = pathlib.Path(os.environ.get('CCSE102_HOME', ROOT / 'workspace')).resolve()
STATE_FILE = STATE_DIR / 'state.json'
AUDIT_FILE = STATE_DIR / 'audit.jsonl'
BLOB_DIR = STATE_DIR / 'blobs'
BACKUP_DIR = STATE_DIR / 'backups'
VERSION = '1.0'

def fail(message, exit_code=2):
    print('ERROR:', message, file=sys.stderr)
    raise SystemExit(exit_code)

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
def event(action, actor, outcome, detail):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(dict(time=now(), actor=actor, action=action, outcome=outcome, detail=detail), sort_keys=True)+'\n')

def safe_name(name):
    if not name or len(name)>40 or not all(c.isalnum() or c in '-_' for c in name):
        fail('Use a 1-40 character name containing letters, digits, hyphens or underscores.')
    return name

def read_state():
    if not STATE_FILE.exists(): fail('Lab not initialised. Run: python3 azlocal.py init')
    try: return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception: fail('State could not be read. Restore a backup or ask your instructor.')

def save(s):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp=STATE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(s, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    tmp.replace(STATE_FILE)

def out(data): print(json.dumps(data, indent=2, sort_keys=True, default=str))

def initial_state():
    return {'lab':'CCSE-102 Azure Operations - offline simulation','subscription':'ICDFA-SIM-001', 'location':'local-linux', 'groups':{}, 'vms':{}, 'nsgs':{}, 'storage':{}, 'assignments':[{'user':'student-admin','role':'Owner','scope':'subscription'},{'user':'auditor','role':'Reader','scope':'subscription'}], 'alert_rules':{}, 'metrics':[], 'maintenance':[], 'created_at':now()}

def has_permission(s, actor, action, scope='subscription'):
    for item in s['assignments']:
        if item['user']!=actor: continue
        if item['scope']!='subscription' and item['scope']!=scope: continue
        role=item['role']
        if role=='Owner': return True
        if role=='Contributor' and action not in ('assign', 'lock'): return True
        if role=='Reader' and action=='read': return True
        if role=='Storage Blob Data Contributor' and action in ('blob-read','blob-write') and item['scope']==scope: return True
    return False

def require(s,args,action,scope='subscription'):
    if not has_permission(s,args.actor,action,scope):
        event('authorisation',args.actor,'denied',f'{action} on {scope}')
        fail(f'RBAC DENIED: {args.actor} lacks permission {action} on {scope}', 3)

def rg_check(s, rg):
    if rg not in s['groups']: fail(f'Resource group not found: {rg}')

def is_locked(s, rg): return s['groups'][rg].get('locked', False)

def require_unlocked(s, rg):
    if is_locked(s,rg): fail(f'Resource group {rg} has a simulated delete/read-only lock. Unlock before changes.')

def cmd_init(a):
    if STATE_FILE.exists() and not a.reset: fail('Already initialised. Use init --reset only when starting over.')
    if a.reset and not a.confirm: fail('Reset requires --confirm (destructive to existing simulated state).')
    if a.reset and STATE_DIR.exists(): shutil.rmtree(STATE_DIR)
    STATE_DIR.mkdir(parents=True, exist_ok=True); BLOB_DIR.mkdir(); BACKUP_DIR.mkdir()
    save(initial_state())
    event('init','student-admin','ok','new offline lab initialised')
    out({'result':'ready','workspace':str(STATE_DIR),'subscription':'ICDFA-SIM-001','notice':'Offline simulation; NOT Microsoft Azure'})

def cmd_status(a):
    s=read_state(); require(s,a,'read')
    out({'subscription':s['subscription'],'groups':list(s['groups']),'vms':len(s['vms']),'networks':len(s['nsgs']),'storage_accounts':len(s['storage']),'monitor_rules':len(s['alert_rules']),'notice':'No Azure resources are created.'})

def cmd_group(a):
    s=read_state(); name=getattr(a,'name',None)
    if a.verb=='list': require(s,a,'read'); out(s['groups']); return
    safe_name(name)
    if a.verb=='create':
        require(s,a,'write')
        if name in s['groups']: fail('Resource group already exists.')
        s['groups'][name]={'tags':{'owner':a.owner,'environment':a.environment},'locked':False,'location':'local-linux'}
    else:
        rg_check(s,name); require(s,a,'write',f'group:{name}')
        if a.verb=='tag': require_unlocked(s,name); s['groups'][name]['tags'][a.key]=a.value
        elif a.verb=='lock': require(s,a,'lock',f'group:{name}'); s['groups'][name]['locked']=True
        elif a.verb=='unlock': require(s,a,'lock',f'group:{name}'); s['groups'][name]['locked']=False
    save(s); event('group-'+a.verb,a.actor,'ok',name); out({'group':name, **s['groups'][name]})

def cmd_access(a):
    s=read_state()
    if a.verb=='list': require(s,a,'read'); out(s['assignments']); return
    if a.verb=='assign':
        require(s,a,'assign')
        if a.scope!='subscription' and not a.scope.startswith('group:') and not a.scope.startswith('storage:'): fail('Allowed scope: subscription, group:NAME, storage:NAME')
        if a.scope.startswith('group:'): rg_check(s,a.scope.split(':',1)[1])
        if a.scope.startswith('storage:') and a.scope[8:] not in s['storage']: fail('Storage account not found.')
        item={'user':safe_name(a.user),'role':a.role,'scope':a.scope}
        if item not in s['assignments']: s['assignments'].append(item)
        save(s); event('rbac-assign',a.actor,'ok',item); out(item)
    else:
        require(s,a,'read'); decision=has_permission(s,a.user,a.action,a.scope)
        event('rbac-check',a.actor,'ok',{'user':a.user,'action':a.action,'permitted':decision})
        out({'user':a.user,'scope':a.scope,'action':a.action,'permitted':decision})

def cmd_vm(a):
    s=read_state()
    if a.verb=='list': require(s,a,'read'); out(s['vms']); return
    if a.verb=='create':
        safe_name(a.name); rg_check(s,a.group); require(s,a,'write',f'group:{a.group}'); require_unlocked(s,a.group)
        if a.name in s['vms']: fail('VM record already exists.')
        s['vms'][a.name]={'group':a.group,'size':a.size,'state':'stopped','os':'Ubuntu (simulated record)','created_at':now()}
    else:
        if a.name not in s['vms']: fail('VM record not found.')
        vm=s['vms'][a.name]; require(s,a,'write',f'group:{vm["group"]}'); require_unlocked(s,vm['group'])
        vm['state']='running' if a.verb=='start' else 'stopped'
    save(s); event('vm-'+a.verb,a.actor,'ok',a.name); out({'name':a.name, **s['vms'][a.name], 'notice':'VM operations change simulated inventory only.'})

def cmd_nsg(a):
    s=read_state()
    if a.verb=='list': require(s,a,'read'); out(s['nsgs']); return
    if a.verb=='create':
        safe_name(a.name); rg_check(s,a.group); require(s,a,'write',f'group:{a.group}'); require_unlocked(s,a.group)
        if a.name in s['nsgs']: fail('NSG already exists.')
        s['nsgs'][a.name]={'group':a.group,'rules':[],'default':'deny'}
    else:
        if a.name not in s['nsgs']: fail('NSG not found.')
        nsg=s['nsgs'][a.name]; require(s,a,'read' if a.verb=='test' else 'write',f'group:{nsg["group"]}')
        if a.verb=='remove':
            require_unlocked(s,nsg['group'])
            before=len(nsg['rules'])
            nsg['rules']=[r for r in nsg['rules'] if r['priority']!=a.priority]
            if len(nsg['rules'])==before: fail('No NSG rule at that priority.')
        if a.verb=='rule':
            require_unlocked(s,nsg['group'])
            if not (1<=a.port<=65535): fail('Invalid TCP port.')
            try: ipaddress.ip_network(a.source, strict=False)
            except ValueError: fail('Source must be a valid CIDR, e.g. 192.168.56.0/24')
            if any(r['priority']==a.priority for r in nsg['rules']): fail('NSG priorities must be unique.')
            nsg['rules'].append({'priority':a.priority,'source':a.source,'port':a.port,'decision':a.decision})
        elif a.verb=='test':
            try: source=ipaddress.ip_address(a.source)
            except ValueError: fail('Use an IP address for a test.')
            rules=sorted(nsg['rules'],key=lambda x:x['priority'])
            matched=next((r for r in rules if source in ipaddress.ip_network(r['source']) and r['port']==a.port),None)
            decision=matched['decision'] if matched else nsg['default']
            event('nsg-test',a.actor,'ok',{'name':a.name,'source':a.source,'port':a.port,'decision':decision})
            out({'name':a.name,'source':a.source,'port':a.port,'decision':decision,'matched_rule':matched}); return
    save(s); event('nsg-'+a.verb,a.actor,'ok',a.name); out({'name':a.name, **s['nsgs'][a.name]})

def cmd_storage(a):
    s=read_state()
    if a.verb=='list': require(s,a,'read'); out(s['storage']); return
    safe_name(a.name)
    if a.verb=='set':
        if a.name not in s['storage']: fail('Storage account not found.')
        acc=s['storage'][a.name]; require(s,a,'write',f'group:{acc["group"]}'); require_unlocked(s,acc['group'])
        acc['public_access']=a.public_access=='true' if a.public_access is not None else acc['public_access']
        acc['https_only']=a.https_only=='true' if a.https_only is not None else acc['https_only']
        save(s); event('storage-set',a.actor,'ok',a.name); out({'name':a.name, **acc}); return
    rg_check(s,a.group); require(s,a,'write',f'group:{a.group}'); require_unlocked(s,a.group)
    if a.name in s['storage']: fail('Storage account already exists.')
    s['storage'][a.name]={'group':a.group,'public_access':False,'https_only':True,'blobs':{}}
    (BLOB_DIR/a.name).mkdir(parents=True,exist_ok=True)
    save(s); event('storage-create',a.actor,'ok',a.name); out({'name':a.name, **s['storage'][a.name]})

def blob_account(s,a,action):
    if a.account not in s['storage']: fail('Storage account not found.')
    acc=s['storage'][a.account]
    if not (has_permission(s,a.actor,action,'storage:'+a.account) or has_permission(s,a.actor,'write' if action=='blob-write' else 'read','group:'+acc['group'])):
        event('authorisation',a.actor,'denied',f'{action} on storage:{a.account}')
        fail('RBAC DENIED for blob data operation',3)
    return acc

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            x=f.read(65536)
            if not x: break
            h.update(x)
    return h.hexdigest()

def cmd_blob(a):
    s=read_state(); action='blob-write' if a.verb in ('upload','restore') else 'blob-read'; acc=blob_account(s,a,action)
    if a.verb=='list': out(acc['blobs']); return
    if a.verb=='upload':
        safe_name(a.name); src=pathlib.Path(a.file).expanduser().resolve()
        if not src.is_file(): fail('Local upload file not found.')
        if src.stat().st_size>5*1024*1024: fail('Educational lab upload limit is 5 MB per file.')
        dst=BLOB_DIR/a.account/a.name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        acc['blobs'][a.name]={'sha256':digest(dst),'bytes':dst.stat().st_size,'uploaded_at':now()}
        save(s); event('blob-upload',a.actor,'ok',f'{a.account}/{a.name}'); out(acc['blobs'][a.name]); return
    if a.name not in acc['blobs']: fail('Blob not found.')
    src=BLOB_DIR/a.account/a.name
    if a.verb=='verify':
        actual=digest(src) if src.exists() else None
        out({'name':a.name,'expected':acc['blobs'][a.name]['sha256'],'actual':actual,'integrity_ok':actual==acc['blobs'][a.name]['sha256']}); return
    if a.verb=='download':
        dest=pathlib.Path(a.dest).expanduser().resolve()
        if dest.exists(): fail('Destination already exists. Choose a new output filename.')
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
        event('blob-download',a.actor,'ok',a.name); out({'downloaded_to':str(dest),'sha256':digest(dest)})

def cmd_backup(a):
    s=read_state()
    if a.verb=='list': require(s,a,'read'); out([p.name for p in BACKUP_DIR.glob('*.json')]); return
    require(s,a,'write')
    if a.verb=='create':
        label=safe_name(a.label); dest=BACKUP_DIR/(label+'.json')
        if dest.exists(): fail('Backup label already exists.')
        snapshot={'state':s,'checksum':hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest(),'created_at':now()}
        dest.write_text(json.dumps(snapshot,indent=2), encoding='utf-8')
        event('backup-create',a.actor,'ok',label); out({'backup':label,'path':str(dest),'checksum':snapshot['checksum']}); return
    if a.verb=='restore':
        label=safe_name(a.label); src=BACKUP_DIR/(label+'.json')
        if not src.exists(): fail('Backup label not found.')
        snapshot=json.loads(src.read_text(encoding='utf-8'))
        checksum=hashlib.sha256(json.dumps(snapshot['state'],sort_keys=True).encode()).hexdigest()
        if checksum!=snapshot['checksum']: fail('Backup integrity verification failed. No changes made.')
        if not a.confirm: fail('Restore requires --confirm because it replaces current simulated inventory.')
        save(snapshot['state']); event('backup-restore',a.actor,'ok',label)
        out({'restored':label,'verified':True,'note':'Inventory only; uploaded blob files are not reverted.'})

def cmd_monitor(a):
    s=read_state()
    if a.verb=='sample':
        require(s,a,'write')
        readings=[{'resource':'vm-demo','cpu_percent':32,'time':now()},{'resource':'vm-demo','cpu_percent':86,'time':now()},{'resource':'vm-demo','cpu_percent':94,'time':now()},{'resource':'storage-demo','cpu_percent':8,'time':now()}]
        s['metrics'].extend(readings); save(s); event('monitor-sample',a.actor,'ok',len(readings)); out({'added':len(readings),'samples':readings})
    elif a.verb=='rule':
        require(s,a,'write'); safe_name(a.name)
        s['alert_rules'][a.name]={'metric':'cpu_percent','threshold':a.threshold,'enabled':True}
        save(s); event('monitor-rule',a.actor,'ok',a.name); out({a.name:s['alert_rules'][a.name]})
    elif a.verb=='alerts':
        require(s,a,'read'); alerts=[]
        for label,rule in s['alert_rules'].items():
            for m in s['metrics']:
                if m.get('cpu_percent',0)>=rule['threshold']:
                    alerts.append({'rule':label,'resource':m['resource'],'value':m['cpu_percent'],'threshold':rule['threshold'],'time':m['time']})
        out({'count':len(alerts),'alerts':alerts})
    elif a.verb=='logs':
        require(s,a,'read'); rows=[json.loads(x) for x in AUDIT_FILE.read_text(encoding='utf-8').splitlines()] if AUDIT_FILE.exists() else []
        out({'count':len(rows),'recent_events':rows[-a.limit:]})

def cmd_policy(a):
    s=read_state(); require(s,a,'read')
    findings=[]
    for name,g in s['groups'].items():
        for tag in ('owner','environment'):
            if not g['tags'].get(tag): findings.append({'resource':name,'control':'required-tags','finding':'Missing '+tag})
    for name,acc in s['storage'].items():
        if acc['public_access']: findings.append({'resource':name,'control':'storage-private','finding':'Public access enabled'})
        if not acc['https_only']: findings.append({'resource':name,'control':'storage-https','finding':'HTTPS not enforced'})
    for name,nsg in s['nsgs'].items():
        for rule in nsg['rules']:
            if rule['source']=='0.0.0.0/0' and rule['decision']=='allow' and rule['port']==22:
                findings.append({'resource':name,'control':'ssh-exposure','finding':'SSH allowed from any IPv4 source'})
    out({'checked':len(s['groups'])+len(s['storage'])+len(s['nsgs']),'findings_count':len(findings),'findings':findings,'simulation':True})

def cmd_report(a):
    s=read_state(); require(s,a,'read')
    output={'generated_at':now(),'course':'CCSE-102','notice':'This report concerns local simulated Azure-style resources only.','groups':len(s['groups']),'vms':s['vms'],'nsgs':s['nsgs'],'storage':{k:{'group':v['group'],'blob_count':len(v['blobs'])} for k,v in s['storage'].items()},'access_assignments':s['assignments'],'alerts_defined':s['alert_rules']}
    p=pathlib.Path(a.output).expanduser().resolve()
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    out({'report':str(p),'sha256':digest(p)})

def build():
    p=argparse.ArgumentParser(description='ICDFA CCSE-102 - offline Azure administration simulator (not Azure CLI)')
    p.add_argument('--actor',default='student-admin',help='Fictional RBAC identity')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('init'); x.add_argument('--reset',action='store_true'); x.add_argument('--confirm',action='store_true')
    sub.add_parser('status')
    g=sub.add_parser('group'); gs=g.add_subparsers(dest='verb',required=True)
    x=gs.add_parser('create'); x.add_argument('name'); x.add_argument('--owner',default=''); x.add_argument('--environment',default='')
    gs.add_parser('list')
    for action in ('lock','unlock'):
        x=gs.add_parser(action); x.add_argument('name')
    x=gs.add_parser('tag'); x.add_argument('name'); x.add_argument('key'); x.add_argument('value')
    ac=sub.add_parser('access'); aa=ac.add_subparsers(dest='verb',required=True)
    aa.add_parser('list')
    x=aa.add_parser('assign'); x.add_argument('user'); x.add_argument('role',choices=['Owner','Contributor','Reader','Storage Blob Data Contributor']); x.add_argument('scope')
    x=aa.add_parser('check'); x.add_argument('user'); x.add_argument('action',choices=['read','write','assign','lock','blob-read','blob-write']); x.add_argument('scope')
    vm=sub.add_parser('vm'); vv=vm.add_subparsers(dest='verb',required=True)
    x=vv.add_parser('create'); x.add_argument('name'); x.add_argument('--group',required=True); x.add_argument('--size',default='B1s')
    vv.add_parser('list')
    for op in ('start','stop'):
        x=vv.add_parser(op); x.add_argument('name')
    n=sub.add_parser('nsg'); nn=n.add_subparsers(dest='verb',required=True)
    x=nn.add_parser('create'); x.add_argument('name'); x.add_argument('--group',required=True)
    nn.add_parser('list')
    x=nn.add_parser('rule'); x.add_argument('name'); x.add_argument('--source',required=True); x.add_argument('--port',type=int,required=True); x.add_argument('--decision',choices=['allow','deny'],required=True); x.add_argument('--priority',type=int,required=True)
    x=nn.add_parser('test'); x.add_argument('name'); x.add_argument('--source',required=True); x.add_argument('--port',type=int,required=True)
    x=nn.add_parser('remove'); x.add_argument('name'); x.add_argument('--priority',type=int,required=True)
    st=sub.add_parser('storage'); ss=st.add_subparsers(dest='verb',required=True)
    x=ss.add_parser('create'); x.add_argument('name'); x.add_argument('--group',required=True)
    ss.add_parser('list')
    x=ss.add_parser('set'); x.add_argument('name'); x.add_argument('--public-access',choices=['true','false']); x.add_argument('--https-only',choices=['true','false'])
    bl=sub.add_parser('blob'); bb=bl.add_subparsers(dest='verb',required=True)
    for op in ('list','upload','verify','download'):
        x=bb.add_parser(op); x.add_argument('account')
        if op!='list': x.add_argument('name')
        if op=='upload': x.add_argument('--file',required=True)
        if op=='download': x.add_argument('--dest',required=True)
    ba=sub.add_parser('backup'); bs=ba.add_subparsers(dest='verb',required=True)
    bs.add_parser('list'); x=bs.add_parser('create'); x.add_argument('label')
    x=bs.add_parser('restore'); x.add_argument('label'); x.add_argument('--confirm',action='store_true')
    mo=sub.add_parser('monitor'); mm=mo.add_subparsers(dest='verb',required=True)
    mm.add_parser('sample'); x=mm.add_parser('rule'); x.add_argument('name'); x.add_argument('--threshold',type=int,default=80)
    mm.add_parser('alerts'); x=mm.add_parser('logs'); x.add_argument('--limit',type=int,default=15)
    sub.add_parser('policy')
    rp=sub.add_parser('report'); rp.add_argument('--output',default='evidence/summary.json')
    return p

def main():
    p=build(); a=p.parse_args()
    if a.command=='init': cmd_init(a)
    elif a.command=='status': cmd_status(a)
    elif a.command=='group': cmd_group(a)
    elif a.command=='access': cmd_access(a)
    elif a.command=='vm': cmd_vm(a)
    elif a.command=='nsg': cmd_nsg(a)
    elif a.command=='storage': cmd_storage(a)
    elif a.command=='blob': cmd_blob(a)
    elif a.command=='backup': cmd_backup(a)
    elif a.command=='monitor': cmd_monitor(a)
    elif a.command=='policy': cmd_policy(a)
    elif a.command=='report': cmd_report(a)
if __name__=='__main__': main()
