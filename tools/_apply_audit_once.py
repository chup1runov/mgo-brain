"""One-time, guarded source migration for the 2026-09-19 audit branch.
The publishing job removes this file after preserving the tested source changes.
"""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
CHANGED=[]
def edit(rel,old,new,*,required=True):
    p=ROOT/rel;s=p.read_text()
    if old not in s:
        if new in s or not required:
            return
        raise RuntimeError(f'Unexpected source, refusing blind edit: {rel}: {old[:70]!r}')
    s=s.replace(old,new)
    p.write_text(s)
    CHANGED.append(rel)

def rewrite_function(rel,name,text):
    p=ROOT/rel;s=p.read_text()
    pattern=rf'(?m)^function {name}\([^\n]*\n'
    replacement,count=re.subn(pattern,lambda _:text+'\n',s,count=1)
    if count!=1:raise RuntimeError(f'Cannot find function {name}')
    p.write_text(replacement);CHANGED.append(rel)

edit('mgo_brain/main.py','from fastapi.responses import FileResponse','from fastapi.responses import FileResponse, JSONResponse')
edit('mgo_brain/main.py','    yield\n    await service.stop()','    try:\n        yield\n    finally:\n        await service.stop()')
edit('mgo_brain/main.py','def health():\n    return {','def health():\n    status = service.readiness()\n    return JSONResponse({',required=True)
edit('mgo_brain/main.py','        "status": "ok",','        **status,\n        "status": "ok" if status["ready"] else "degraded",')
edit('mgo_brain/main.py','        "ai": ai_gateway.status().model_dump(mode="json"),\n    }','        "ai": ai_gateway.status().model_dump(mode="json"),\n    }, status_code=200 if status["ready"] else 503)')
edit('mgo_brain/main.py','            include_evidence=request.include_evidence,','            include_evidence=request.include_evidence,\n            language=request.language,')
edit('mgo_brain/main.py','from .main_paths import configure_paths','from .main_paths import configure_paths\nfrom .request_limits import RequestLimitMiddleware')
edit('mgo_brain/main.py','app.mount("/static",','app.add_middleware(RequestLimitMiddleware)\napp.mount("/static",')
edit('mgo_brain/runtime.py','host: str = "0.0.0.0"','host: str = "127.0.0.1"')
edit('mgo_brain/runtime.py','env.get("MGO_BRAIN_HOST", "0.0.0.0")','env.get("MGO_BRAIN_HOST", "127.0.0.1")')

# Short replies from Modbus are invalid evidence, never a fabricated zero/False.
edit('mgo_brain/sources/modbus.py','value = bool(bits[0]) if bits else False','value = bool(bits[0]) if len(bits) == 1 else None')
edit('mgo_brain/sources/modbus.py','if channel.invert:\n                    value = not value','if channel.invert and value is not None:\n                    value = not value')
edit('mgo_brain/sources/modbus.py','value=value, quality=SignalQuality.GOOD','value=value, quality=SignalQuality.GOOD if value is not None else SignalQuality.INVALID')
edit('mgo_brain/sources/modbus.py','raw = int(regs[0]) if regs else 0','raw = int(regs[0]) if len(regs) == 1 else None')
edit('mgo_brain/sources/modbus.py','if channel.signed and raw >= 0x8000:','if channel.signed and raw is not None and raw >= 0x8000:')
edit('mgo_brain/sources/modbus.py','value = raw * channel.scale + channel.offset','value = raw * channel.scale + channel.offset if raw is not None else None')
edit('mgo_brain/sources/modbus.py','value=value, unit=channel.unit, quality=SignalQuality.GOOD','value=value, unit=channel.unit, quality=SignalQuality.GOOD if value is not None else SignalQuality.INVALID')

# Configuration must never blend fabricated data into real vehicle acquisition.
edit('mgo_brain/sources/config.py','import json\n','import json\nimport os\nimport math\n')
edit('mgo_brain/sources/config.py','    return RuntimeSourceConfig(\n','    timeout = float(raw.get("stale_after_s", 3.0))\n    if not math.isfinite(timeout) or timeout <= 0:\n        raise ValueError("Invalid stale_after_s")\n    return RuntimeSourceConfig(\n')
edit('mgo_brain/sources/config.py','    def build(self, config: RuntimeSourceConfig) -> SourceAdapter:\n        adapters = []','    def build(self, config: RuntimeSourceConfig) -> SourceAdapter:\n        enabled = {x.type for x in config.sources if x.enabled}\n        hardware = enabled & {"dbc_socketcan", "sensorhub_socketcan", "modbus_di", "modbus_ai", "vedirect_serial"}\n        if hardware and enabled & {"simulator", "bench"}:\n            raise ValueError("Do not mix synthetic and real vehicle sources")\n        if hardware and os.environ.get("MGO_ALLOW_EXPERIMENTAL_HARDWARE") != "1":\n            raise ValueError("Hardware is not commissioned. Explicit MGO_ALLOW_EXPERIMENTAL_HARDWARE=1 is required after review")\n        adapters = []')

# Preserve EOF semantics in the replay path instead of busy-spinning forever.
edit('mgo_brain/replay.py','    async def recv(self, timeout: float | None = None) -> CanFrame | None:\n','    @property\n    def exhausted(self):\n        return self.closed or (not self.loop and self._index >= len(self.records))\n\n    async def recv(self, timeout: float | None = None) -> CanFrame | None:\n')
for rel in ('mgo_brain/sources/dbc.py','mgo_brain/sources/sensorhub.py'):
    edit(rel,'            if frame is None:\n                continue','            if frame is None:\n                if getattr(self.transport, "exhausted", False):\n                    return\n                continue')

# Tighten text capture parsing without inventing support for CAN FD/RTR/error frames.
edit('mgo_brain/survey.py','    match = _BRACKET_RE.match(stripped)','    match = _BRACKET_RE.fullmatch(stripped)')
edit('mgo_brain/survey.py','        if len(data_hex) % 2:','        if len(data_hex) % 2 or len(data_hex) > 16 or int(match.group("id"), 16) > 0x1FFFFFFF:')
edit('mgo_brain/survey.py','        if len(tokens) < dlc:','        if len(tokens) != dlc or dlc > 8 or int(match.group("id"), 16) > 0x1FFFFFFF:')
edit('mgo_brain/survey.py','            "changed_bytes": sorted(changed_bytes, key=lambda x: x["score"], reverse=True),','            "changed_bytes": sorted(changed_bytes, key=lambda x: x["score"], reverse=True),\n            "observed_dlc": sorted({len(x.data) for x in base_group + act_group}),')
edit('mgo_brain/survey.py','        dlc = min(8, max(1, max_index + 1))','        observed = item.get("observed_dlc", [])\n        if len(observed) != 1:\n            continue  # A variable/unknown length is not an established DBC message.\n        dlc = observed[0]')
edit('mgo_brain/survey.py','        lines.append(f"BO_ {arbitration_id} {name}: {dlc} MGO_BFI")','        dbc_id = arbitration_id | (0x80000000 if arbitration_id > 0x7FF else 0)\n        lines.append(f"BO_ {dbc_id} {name}: {dlc} MGO_BFI")')
edit('mgo_brain/survey.py',"        lines.append(f'CM_ BO_ {arbitration_id} \"{comment}\";')","        lines.append(f'CM_ BO_ {dbc_id} \"{comment}\";')")
edit('mgo_brain/survey.py','        ).replace(\'"\', "\'")','        ).replace(\'"\', "\'").replace("\\n", " ").replace("\\r", " ").replace("\\\\", "/")')

# Avoid non-finite reference data and signal discovery on empty/invalid samples.
edit('mgo_brain/numeric_discovery.py','            samples.append(ReferenceSample(float(row[0]), float(row[1])))','            timestamp, value = float(row[0]), float(row[1])\n            if not math.isfinite(timestamp) or not math.isfinite(value):\n                raise ValueError("Non-finite reference")\n            samples.append(ReferenceSample(timestamp, value))')

# Backups must not recurse into themselves, follow links, or accidentally copy secrets.
edit('mgo_brain/backup.py','    output.parent.mkdir(parents=True, exist_ok=True)','    data_dir, config_dir, output = data_dir.resolve(), config_dir.resolve(), output.resolve()\n    if output.is_relative_to(data_dir) or output.is_relative_to(config_dir):\n        raise ValueError("Backup output must be outside data/config directories")\n    if output.exists():\n        raise FileExistsError(output)\n    output.parent.mkdir(parents=True, exist_ok=True)')
edit('mgo_brain/backup.py','                if path.is_dir():','                if path.is_dir() or path.is_symlink():')
edit('mgo_brain/backup.py','        if path.is_dir():','        if path.is_dir() or path.is_symlink() or path.suffix in {".env", ".key", ".pem", ".p12"} or path.name.startswith(".env"):\n            continue\n        if False:')
edit('tests/test_v053_deployment.py','archive.extractall(extract)','archive.extractall(extract, filter="data")')

# New algorithmic definitions are not verified physical telemetry.
edit('mgo_brain/ai_models.py','    language: str = Field(default="ru", max_length=16)','    language: Literal["ru", "en"] = "ru"')
edit('mgo_brain/ai_models.py','class EvidencePacket(BaseModel):\n    question: str','class EvidencePacket(BaseModel):\n    language: Literal["ru", "en"] = "ru"\n    question: str')
edit('mgo_brain/ai_gateway.py','def build_evidence(self, question: str) -> EvidencePacket:','def build_evidence(self, question: str, *, language: str = "ru") -> EvidencePacket:')
edit('mgo_brain/ai_gateway.py','            question=question,','            question=question,\n            language=language,')
edit('mgo_brain/ai_gateway.py','def ask(self, question: str, *, include_evidence: bool = False) -> AskMGOResponse:\n        packet = self.build_evidence(question)\n        response = self.provider.answer(packet)','def ask(self, question: str, *, include_evidence: bool = False, language: str = "ru") -> AskMGOResponse:\n        packet = self.build_evidence(question, language=language)\n        try:\n            response = self.provider.answer(packet)\n        except Exception as exc:\n            if self.provider_name == "local":\n                raise\n            packet.warnings.append("External AI unavailable: " + type(exc).__name__)\n            response = LocalEvidenceProvider().answer(packet)')
edit('mgo_brain/ai_provider.py','os.environ.get("MGO_AI_MODEL", "gpt-5.6-terra")','os.environ.get("MGO_AI_MODEL", "")')
edit('mgo_brain/ai_provider.py','        self._client = OpenAI()','        self._client = OpenAI(timeout=20.0, max_retries=0)')
edit('mgo_brain/ai_provider.py','        configured = bool(sdk and key) or self._client is not None','        configured = bool(self.model) and (bool(sdk and key) or self._client is not None)')
edit('mgo_brain/ai_provider.py','        client = self._client_or_raise()','        if not self.model:\n            raise RuntimeError("Set MGO_AI_MODEL to an API model available to your account")\n        client = self._client_or_raise()')
edit('mgo_brain/ai_provider.py','            instructions=SYSTEM_INSTRUCTIONS_RU,','            instructions=SYSTEM_INSTRUCTIONS_RU + ("\\nAnswer in English." if packet.language == "en" else ""),\n            store=False,\n            max_output_tokens=1200,')
edit('mgo_brain/ai_provider.py','if v.get("value") is not None:','if v.get("value") is not None and v.get("quality") == "GOOD":')
edit('mgo_brain/ai_provider.py','if dev.get("value") is not None:','if dev.get("value") is not None and dev.get("quality") == "GOOD":')
edit('mgo_brain/ai_provider.py','in {"STALE", "MISSING", "INVALID"}','in {"STALE", "MISSING", "INVALID", "UNVERIFIED", "SUSPECT"}')
edit('mgo_brain/ai_provider.py','        return AskMGOResponse(\n            answer=" ".join(lines),','        if packet.language == "en":\n            lines = ["Local evidence report. " + str((health or {}).get("health", {}).get("status", "UNKNOWN")),\n                     "No cloud model was used. Unverified or stale readings are not current evidence."]\n        return AskMGOResponse(\n            answer=" ".join(lines),')
edit('mgo_brain/ai_toolbox.py','UNUSABLE = {SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID}','UNUSABLE = {SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID, SignalQuality.UNVERIFIED, SignalQuality.SUSPECT}')
edit('mgo_brain/ai_toolbox.py','"usable": reading.quality not in UNUSABLE,','"usable": reading.usable,')
edit('mgo_brain/ai_gateway.py','    selected = ["get_live_state"]','    selected = ["get_live_state", "get_source_status"]')

# The UI must distinguish a live connection from a live measurement.
ui='static/index.html'
edit(ui,"function value(name){return lastState.signals?.[name]?.value}","let lastLiveReceipt=0;\nfunction value(name){const r=lastState.signals?.[name];return performance.now()-lastLiveReceipt<3000 && r?.quality==='GOOD' ? r.value : null}")
edit(ui,'ws.onmessage=e=>{lastState=JSON.parse(e.data);setSignals()}',"ws.onmessage=e=>{lastLiveReceipt=performance.now();lastState=JSON.parse(e.data);setSignals()}")
edit(ui,"ws.onclose=()=>{", "ws.onclose=()=>{lastLiveReceipt=0;setSignals();")
edit(ui,"const proto=location.protocol", "setInterval(()=>{if(performance.now()-lastLiveReceipt>=3000){setSignals();$('conn').textContent=tr('common.offline','нет связи');$('conn').className='badge offline'}},500);\nconst proto=location.protocol")
edit(ui,"$('conn').textContent=tr('common.live','● в сети');", "$('conn').textContent=performance.now()-lastLiveReceipt<3000 ? tr('common.live','● в сети') : tr('common.offline','нет связи');")
edit(ui,"statusHtml(I18N.status(x.qualified?'NORMAL':'UNQUALIFIED'))", "statusHtml(x.qualified?'NORMAL':'UNQUALIFIED')",required=False)
edit(ui,'</header>','</header>\n<div id="dataOrigin" class="panel small" role="status">Нет подтверждённых данных автомобиля</div>')
edit(ui,'function renderHealth(){','function renderHealth(){$(\'dataOrigin\').textContent=health.data_origin===\'vehicle\'?\'Источник: автомобиль — экспериментальная телеметрия\':\'ДЕМОНСТРАЦИЯ / \' +(health.data_origin||\'ожидание\')+\' — это не показания автомобиля\';')
edit(ui,'<small>km/h</small>','<small data-i18n="unit.kmh">км/ч</small>')
edit(ui,'<small>rpm</small>','<small data-i18n="unit.rpm">об/мин</small>')
# Do not suppress Chromium security updates on a connected vehicle computer.
edit('mgo_brain/display.py','        "--check-for-update-interval=31536000",\n','')
# Avoid an executable guessed model name in the deployment example.
edit('deployment/mgo-brain.env.example','# MGO_AI_MODEL=gpt-5.6-terra','# MGO_AI_MODEL=<set-a-verified-API-model-id>')

for rel in ('pyproject.toml','mgo_brain/main.py','config/project.json','static/i18n.js','static/index.html'):
    p=ROOT/rel;p.write_text(p.read_text().replace('0.5.9','0.5.10'));CHANGED.append(rel)
edit('static/service-worker.js','mgo-brain-v059-shell','mgo-brain-v0510-shell')
edit('.gitignore','# Python / tooling','# Audit runner output (persistent selected results live under docs/audit/)\naudit-output/\n\n# Python / tooling')
# Sensitive files must never be sent to a Docker build context.
(ROOT/'.dockerignore').write_text('.git\n.venv\n__pycache__\n.pytest_cache\ndata\naudit-output\n.env\n.env.*\n*.key\n*.pem\n*.p12\n*.pfx\n*.sqlite3\n*.parquet\n*.log\n*.tar.gz\n')
print('AUDIT_SOURCE_EDITS',json.dumps(sorted(set(CHANGED))))
