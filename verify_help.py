#!/usr/bin/env python3
"""Check real Markdown export, a changed source, and temporary-server shutdown."""
import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
original = (ROOT / 'help.json').read_bytes()
data = json.loads(original)
changed = [dict(row) for row in data]
changed[0]['answer'] = '本次样例改为确认后的第二个工作日领取。'
changed_path = ROOT / '.runtime' / 'help-changed.json'
changed_path.parent.mkdir(exist_ok=True)
changed_path.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
checks = []
for name, entries, source in [('help-original', data, ROOT / 'help.json'), ('help-changed', changed, changed_path), ('help-restored', data, ROOT / 'help.json')]:
    proc = subprocess.run([sys.executable, str(ROOT / 'export_help.py'), '--data', str(source), '--output', name], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    out = ROOT / '.runtime' / 'results' / name
    markdown = (out / 'help.md').read_text(encoding='utf-8')
    report = json.loads((out / 'result.json').read_text(encoding='utf-8'))
    for row in entries:
        assert '## ' + row['title'] in markdown
        assert row['answer'] in markdown
    if name == 'help-changed':
        assert data[0]['answer'] not in markdown
    port = int(report['url'].split(':')[-1].split('/')[0])
    with socket.socket() as sock:
        sock.settimeout(2)
        closed = sock.connect_ex(('127.0.0.1', port)) != 0
    assert closed
    checks.append({'case': name, 'passed': True, 'entries': report['entries'], 'port_closed_after_exit': closed})
assert (ROOT / 'help.json').read_bytes() == original
result = {'passed': True, 'cases': checks, 'original_input_unchanged': True, 'scope': 'Original local dynamic help page, native Markdown dump; no downstream model integration'}
(ROOT / '.runtime' / 'help-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
