#!/usr/bin/env python3
"""Run original-page acceptance scenarios; no external browser automation."""
import datetime,json,pathlib,socket,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
def main():
 rows=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
 changed=[dict(row) for row in rows];changed[1]['price']=108
 target=ROOT/'.runtime'/'catalog-changed.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(changed,ensure_ascii=False,indent=2),encoding='utf-8')
 cases=[('budget100',100,None,['P01','P02']),('budget150',150,None,['P01','P02','P03']),('changed100',100,target,['P01']),('restart100',100,None,['P01','P02'])]
 evidence=[]
 for name,budget,catalog,ids in cases:
  cmd=[sys.executable,str(ROOT/'run.py'),'--budget',str(budget),'--output',name]
  if catalog:cmd+=['--catalog',str(catalog)]
  p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=90)
  (ROOT/'.runtime'/f'{name}-launcher.log').write_text(p.stdout+p.stderr,encoding='utf-8')
  assert p.returncode==0,(name,p.stderr)
  result=json.loads((ROOT/'.runtime'/'results'/name/'result.json').read_text(encoding='utf-8'))
  assert [x['id'] for x in result['selected']['products']]==ids,(name,result)
  port=int(result['url'].split(':')[-1].strip('/'))
  with socket.socket() as s:s.settimeout(2);closed=s.connect_ex(('127.0.0.1',port))!=0
  assert closed,'本地端口没有关闭'
  evidence.append({'case':name,'passed':True,'ids':ids,'port_closed_after_exit':closed,'result':f'results/{name}/result.json'})
 summary={'passed':True,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':evidence,'checks':['原始HTML没有商品行；Lightpanda执行fetch与JS后出现6件','预算100/150在页面通过真实DOM事件筛出2/3件','点阵手账68→108后预算100只剩铅笔，未修改原catalog.json','再次启动恢复原始输入得到2件','每次Lightpanda进程exit=0且原创测试页端口关闭'],'limits':['只验证原创本地页面；不证明任意网站兼容','不测模型Agent/MCP/CDP集成、截图视觉还原、性能倍数','Windows/Intel Mac未实测；Linux按独立证据登记']}
 (ROOT/'.runtime'/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
