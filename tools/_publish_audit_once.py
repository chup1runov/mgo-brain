"""One-time preservation of tested changes; never pushes main or prints credentials."""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'audit/2026-09-19-handoff'
assert os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

expected = os.environ['GITHUB_SHA']
remote = git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0]
assert remote == expected, 'Concurrent branch update: refusing to overwrite it'
assert git('rev-parse', 'HEAD') == expected
out = ROOT / 'audit-output'
archive = ROOT / 'docs' / 'audit' / '2026-09-19'
archive.mkdir(parents=True, exist_ok=True)
for name in ('inventory.json', 'pytest.xml', 'bench.json', 'dashboard-ru.png', 'lab-ru.png'):
    source = out / name
    if source.exists():
        shutil.copy2(source, archive / name)
xml = ET.parse(out / 'pytest.xml').getroot()
suites = list(xml.iter('testsuite'))
summary = {
    'tested_checkout': expected,
    'tested_with_reviewed_migration': True,
    'workflow_run': os.environ['GITHUB_RUN_ID'],
    'tests': sum(int(s.attrib.get('tests', '0')) for s in suites),
    'failures': sum(int(s.attrib.get('failures', '0')) for s in suites),
    'errors': sum(int(s.attrib.get('errors', '0')) for s in suites),
    'skipped': sum(int(s.attrib.get('skipped', '0')) for s in suites),
    'checks': {'static': 'passed', 'pytest': 'passed', 'bench': 'passed', 'chromium': 'passed'},
    'scope_limit': 'Software tests only; no real vehicle, external paid AI or automotive certification.'
}
(archive / 'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
(archive / 'README.md').write_text('# Audit evidence, 2026-09-19\n\n'
    + 'These are synthetic software-validation artifacts, not vehicle telemetry.\n\n'
    + 'Tested checkout: `'+expected+'` with the reviewed one-time migration applied.\n'
    + 'Workflow run: '+summary['workflow_run']+'.\n'
    + f"Tests: {summary['tests']}; failures {summary['failures']}; errors {summary['errors']}; skipped {summary['skipped']}.\n\n"
    + 'The checkpoint commit contains the resulting tested source, not a runtime dependency on migration scripts.\n'
    + 'The inventory hashes refer to tested files before this evidence directory was populated.\n')
(ROOT / '.github/workflows/audit.yml').write_text((ROOT / 'tools/_audit_final_workflow.txt').read_text())
for name in ('_apply_audit_once.py','_finalize_audit_once.py','_audit_final_workflow.txt','_publish_audit_once.py'):
    (ROOT / 'tools' / name).unlink()
# Explicit project paths only. No runtime folders, .env files, secrets or raw personal data.
subprocess.run(['git','add','-A','--','mgo_brain','config','static','tests','deployment','tools','docs',
                'pyproject.toml','.gitignore','.dockerignore','.github/workflows/audit.yml','README.md'],cwd=ROOT,check=True)
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
subprocess.run(['git','config','user.name','MGO audit automation'],cwd=ROOT,check=True)
subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','Preserve tested v0.5.10 fixes and audit evidence'],cwd=ROOT,check=True)
subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,check=True)
print('PRESERVED_AUDIT_COMMIT',git('rev-parse','HEAD'))
