#!/usr/bin/env python3
"""Export our original dynamic help page to Markdown, using official Lightpanda."""
import argparse
import datetime
import http.server
import json
import os
import subprocess
import threading
from pathlib import Path
from run import ROOT, RUNTIME, binary, VERSION


def main():
    parser = argparse.ArgumentParser(description='Export the original Chinese help-page example to Markdown')
    parser.add_argument('--data', type=Path, default=ROOT / 'help.json')
    parser.add_argument('--output', default='help')
    args = parser.parse_args()
    if not args.output.replace('-', '').replace('_', '').isalnum():
        parser.error('output only accepts letters, numbers, - and _')
    content = json.loads(args.data.read_text(encoding='utf-8'))
    if not isinstance(content, list) or not content:
        parser.error('help data must be a nonempty list')
    for row in content:
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('title', 'answer')):
            parser.error('each entry needs a title and answer')
    data = json.dumps(content, ensure_ascii=False).encode('utf-8')
    RUNTIME.mkdir(exist_ok=True)
    out = RUNTIME / 'results' / args.output
    out.mkdir(parents=True, exist_ok=True)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT / 'site'), **kw)

        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == '/help.json':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            elif self.path == '/help.html':
                super().do_GET()
            else:
                self.send_error(404)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/help.html'
    try:
        exe, digest = binary()
        env = dict(os.environ, LIGHTPANDA_DISABLE_TELEMETRY='true', LIGHTPANDA_DISABLE_CORE_DUMP='1')
        version = subprocess.check_output([str(exe), 'version'], env=env, text=True, timeout=15).strip()
        if version != VERSION:
            raise RuntimeError('unexpected Lightpanda version: ' + version)
        command = [str(exe), 'fetch', '--dump', 'markdown', '--wait-selector', '#articles[data-state="ready"]', url]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
        (out / 'stderr.txt').write_text(result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Lightpanda failed; see ' + str(out / 'stderr.txt'))
        markdown = result.stdout
        for row in content:
            if row['title'] not in markdown or row['answer'] not in markdown:
                raise RuntimeError('an expected help entry is missing from the exported Markdown')
        (out / 'help.md').write_text(markdown, encoding='utf-8')
        report = {'passed': True, 'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'browser_version': version, 'binary_sha256': digest, 'url': url,
                  'entries': len(content), 'command': command, 'exit_code': result.returncode,
                  'output': 'help.md', 'scope': 'Original fictional local help page only; no external website or AI knowledge-base integration tested'}
        (out / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(str(out / 'help.md'))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
