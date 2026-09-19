"""Guarded one-time finishing migration, removed from the final checkpoint."""
from pathlib import Path
import runpy

ns = runpy.run_path(str(Path(__file__).with_name('_apply_audit_once.py')))
edit = ns['edit']
ROOT = ns['ROOT']

edit('mgo_brain/ai_gateway.py', '    if len(selected) == 1:', '    if len(selected) == 2:')
edit('tests/test_v057_ai.py', 'OpenAIResponsesProvider(client=client, allow_location=False)', 'OpenAIResponsesProvider(model="fixture-model", client=client, allow_location=False)')
edit('tests/test_v057_ai.py', 'OpenAIResponsesProvider(client=FakeClient())', 'OpenAIResponsesProvider(model="fixture-model", client=FakeClient())')
# An explicit fake model in an offline unit test is not a production API recommendation.
edit('tests/test_v057_ai.py', 'gpt-5.6-terra', 'fixture-model')
edit('mgo_brain/sources/factory.py',
     '    def sensorhub_socketcan(options: dict):\n        transport = SocketCANTransport(\n            channel=str(options["channel"]),',
     '    def sensorhub_socketcan(options: dict):\n        transport = SocketCANTransport(\n            require_listen_only=False,  # Separate private Sensor CAN only.\n            channel=str(options["channel"]),')
edit('mgo_brain/sources/bench.py',
     '    def reset(self) -> None:\n        self.started = self.clock()\n        self.wall_started = datetime.now(timezone.utc)',
     '    def reset(self) -> None:\n        next_epoch = self.wall_started + timedelta(seconds=self.virtual_elapsed())\n        self.started = self.clock()\n        self.wall_started = next_epoch')
# Keep historical acquisition quality alongside flat telemetry. History must not strip it.
edit('mgo_brain/analytics.py',
     '        "mode": state.mode.value,',
     '        "mode": state.mode.value,\n        "signal_metadata_json": json.dumps({name: {"quality": r.quality.value, "source": r.source, "timestamp": r.timestamp.isoformat()} for name, r in state.signals.items()}, separators=(",", ":")),')
# No potentially stale pressure number should be used as a report minimum.
# VehicleState.value now enforces that rule for every existing detector/analytic caller.
# Add the migration outcome to the versioned release state, preserving historical notes.
for rel in ('README.md', 'docs/PROJECT_STATE.md', 'docs/PROJECT_HANDOFF.md', 'docs/ROADMAP.md'):
    p = ROOT / rel
    s = p.read_text()
    banner = '> Актуальная проверенная точка: **v0.5.10**, аудит 19.09.2026. Начните с [русской точки входа](' + ('START_HERE_RU.md' if rel == 'README.md' else '../START_HERE_RU.md') + '). Более ранние отметки «готово» ниже относятся к программным прототипам, не к проверке автомобиля.\n\n'
    if banner not in s:
        p.write_text(banner + s)
print('AUDIT_MIGRATION_COMPLETE')
