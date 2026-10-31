#!/usr/bin/env python3
"""Only exercise our original loopback fixture. No third-party website automation."""
import argparse,datetime,hashlib,http.server,json,os,pathlib,platform,shutil,subprocess,sys,threading,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
RUNTIME=ROOT/'.runtime'
ASSETS={
 ('Darwin','arm64'):('lightpanda-aarch64-macos','273a4659510f8c48e6c5f26a2eee6aa20051632210cbf0f59975ac705056c44f'),
 ('Darwin','x86_64'):('lightpanda-x86_64-macos','35733281cd3ce96070c5c9ce101efd35c9cabd94ab02eea125ad894933abf293'),
 ('Linux','x86_64'):('lightpanda-x86_64-linux','19f3fee25fb14bb75a1e0c1e0f8ab9cce842950544e4a144fbad3884c94b98a3'),
 ('Linux','aarch64'):('lightpanda-aarch64-linux','97710997faea70bb0f22f9b07ba3a9701b47dbb6a71f679150b040e70c565cf3')}
VERSION='1.1.0-nightly.11423+56980afde'
def binary():
 key=(platform.system(),platform.machine())
 if key not in ASSETS:raise RuntimeError('此系统没有本练习原生入口。Windows 请在已经安装的 WSL2 内按 Linux 说明运行；不会自动安装 WSL。')
 name,expected=ASSETS[key];p=RUNTIME/name
 if not p.exists():
  print('下载官方 nightly 快照（锁定 2026-10-31 公布摘要）……',flush=True)
  temp=p.with_suffix('.download')
  req=urllib.request.Request('https://github.com/lightpanda-io/browser/releases/download/nightly/'+name,headers={'User-Agent':'RepoGo-Lightpanda-Demo/1.0'})
  with urllib.request.urlopen(req,timeout=120) as src,temp.open('wb') as dst:shutil.copyfileobj(src,dst)
  if hashlib.sha256(temp.read_bytes()).hexdigest()!=expected:
   temp.unlink();raise RuntimeError('官方 nightly 已滚动或下载损坏，摘要不符，已拒绝执行。请等待本交付的新版本核验；勿跳过校验。')
  temp.replace(p)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=expected:raise RuntimeError('缓存二进制摘要不符，拒绝执行；不要覆盖预期摘要绕过验证。')
 p.chmod(0o755);return p,actual
def main():
 ap=argparse.ArgumentParser(description='本地动态商品页 → 筛选 → Lightpanda 提取 JSON')
 ap.add_argument('--budget',type=int,default=100);ap.add_argument('--category',choices=['全部','文具','图书','生活'],default='文具');ap.add_argument('--catalog',type=pathlib.Path,default=ROOT/'catalog.json');ap.add_argument('--output',default='latest');ap.add_argument('--serve-only',action='store_true')
 args=ap.parse_args()
 if args.budget<0:ap.error('预算不能小于0')
 if not args.output.replace('-','').replace('_','').isalnum():ap.error('output只用字母数字和-_')
 catalog=json.loads(args.catalog.read_text(encoding='utf-8'))
 if not isinstance(catalog,list) or not all(set(['id','name','category','price','stock'])<=set(p) for p in catalog):raise RuntimeError('catalog.json 格式错误')
 data=json.dumps(catalog,ensure_ascii=False).encode();RUNTIME.mkdir(exist_ok=True);out=RUNTIME/'results'/args.output;out.mkdir(parents=True,exist_ok=True)
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'site'),**kw)
  def log_message(self,*a):pass
  def do_GET(self):
   if self.path=='/catalog.json':self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   elif self.path in ['/','/index.html']:super().do_GET()
   else:self.send_error(404)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/'
 try:
  if args.serve_only:
   print(url,flush=True)
   try:thread.join()
   except KeyboardInterrupt:pass
   return
  exe,digest=binary();env=os.environ.copy();env.update(LIGHTPANDA_DISABLE_TELEMETRY='true',LIGHTPANDA_DISABLE_CORE_DUMP='1')
  version=subprocess.check_output([str(exe),'version'],env=env,text=True,timeout=15).strip()
  if version!=VERSION:raise RuntimeError('版本输出与已核验快照不一致：'+version)
  source=urllib.request.urlopen(url,timeout=5).read().decode();(out/'source.html').write_text(source,encoding='utf-8')
  script='''const page = new Page();
await page.goto(URL);
await page.waitForScript("document.querySelector('#status').dataset.state === 'ready'", {timeout:10000});
const initial = await page.extract({status:'#status', names:['.product .name']});
await page.selectOption('#category', CATEGORY);
await page.fill('#budget', BUDGET);
await page.click('#apply');
const selected = await page.extract({status:'#status', products:[{selector:'.product',fields:{id:{selector:'',attr:'data-id'},name:'.name',category:'.category',price:'.price',stock:'.stock'}}]});
console.log('REPOGO_RESULT:'+JSON.stringify({initial, selected}));
page.close();
'''.replace('URL',json.dumps(url)).replace('CATEGORY',json.dumps(args.category,ensure_ascii=False)).replace('BUDGET',json.dumps(str(args.budget)))
  scriptfile=out/'extract.js';scriptfile.write_text(script,encoding='utf-8')
  proc=subprocess.run([str(exe),'run',str(scriptfile)],env=env,cwd=ROOT,text=True,capture_output=True,timeout=45)
  (out/'stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'stderr.txt').write_text(proc.stderr,encoding='utf-8')
  if proc.returncode:raise RuntimeError(f'Lightpanda 返回 {proc.returncode}，查看 {out}/stderr.txt')
  lines=[s for s in proc.stdout.splitlines() if s.startswith('REPOGO_RESULT:')]
  if len(lines)!=1:raise RuntimeError('没有取得唯一结构化结果，请查看 stdout.txt')
  observed=json.loads(lines[0].split(':',1)[1]);expected=[p for p in catalog if (args.category=='全部' or p['category']==args.category) and p['price']<=args.budget and p['stock']>0]
  products=observed['selected']['products'];assert [p['id'] for p in products]==[p['id'] for p in expected],(products,expected)
  assert len(observed['initial']['names'])==len(catalog)
  for got,want in zip(products,expected):assert got=={k:str(v) for k,v in want.items()}
  result={'passed':True,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'system':platform.system(),'machine':platform.machine(),'python':platform.python_version()},'browser_version':version,'binary_sha256':digest,'catalog_sha256':hashlib.sha256(data).hexdigest(),'url':url,'input':{'category':args.category,'budget':args.budget},'raw_html_product_rows':source.count('class="product"'),'initial':observed['initial'],'selected':observed['selected'],'process_exit_code':proc.returncode,'telemetry_disabled':True,'core_dump_disabled':True}
  (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));print(f'提取成功：{len(products)} 件；结果 {out}/result.json。Lightpanda 已退出。')
 finally:server.shutdown();server.server_close();thread.join(timeout=5)
if __name__=='__main__':
 try:main()
 except Exception as e:print('运行失败：'+str(e),file=sys.stderr);sys.exit(1)
