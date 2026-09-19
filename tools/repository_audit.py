"""Reproducible whole-repository inventory and static checks. No network calls."""
from __future__ import annotations
import ast
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    paths = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    inventory, findings = [], []
    for rel in filter(None, paths):
        path = ROOT / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        inventory.append({'path': rel, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if path.suffix == '.py':
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as exc:
                findings.append({'kind':'syntax','path':rel,'detail':str(exc)})
        if path.suffix in {'.json','.webmanifest'}:
            try:
                json.loads(text)
            except ValueError as exc:
                findings.append({'kind':'json','path':rel,'detail':str(exc)})
        scripts = [text] if path.suffix == '.js' else re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',text) if path.suffix == '.html' else []
        for i, script in enumerate(scripts):
            with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as tmp:
                tmp.write(script); tmp.flush()
                result = subprocess.run(['node','--check',tmp.name],capture_output=True,text=True)
                if result.returncode:
                    findings.append({'kind':'javascript','path':rel,'script':i,'detail':result.stderr})
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if not target or '://' in target or target.startswith(('#','mailto:','sandbox:')):
                    continue
                target=target.split('#',1)[0]
                if target and not (path.parent/target).exists():
                    findings.append({'kind':'broken_local_link','path':rel,'target':target})
        if rel.startswith('data/') and rel != 'data/.gitkeep':
            findings.append({'kind':'tracked_runtime_data','path':rel})
    report={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'tracked_files':len(inventory),'python_files':sum(x['path'].endswith('.py') for x in inventory),
            'findings':findings,'files':inventory}
    out=ROOT/'audit-output';out.mkdir(exist_ok=True)
    (out/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
    return bool(findings)

if __name__ == '__main__':
    raise SystemExit(main())
