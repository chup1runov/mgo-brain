from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from mgo_brain.alerts import AlertManager, AlertStatus
from mgo_brain.health import HealthEngine
from mgo_brain.models import Event, Severity, SignalQuality, SignalReading, VehicleMode, VehicleState
from mgo_brain.rules import RulesEngine
from mgo_brain.service import MGOBrainService
from mgo_brain.sources.aggregator import StateAggregator
from mgo_brain.sources.base import SourceAdapter, SourceUpdate
from mgo_brain.sources.mux import SourceMux

NOW = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)

def reading(value, source='sensor', when=NOW, quality=SignalQuality.GOOD):
    return SignalReading(value=value, source=source, timestamp=when, quality=quality)

def update(value, source='sensor', when=NOW, quality=SignalQuality.GOOD):
    return SourceUpdate(source=source, timestamp=when, signals={'engine.oil_pressure': reading(value, source, when, quality)})

@pytest.mark.parametrize('quality', [SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID, SignalQuality.SUSPECT, SignalQuality.UNVERIFIED])
def test_unusable_data_is_not_computed(quality):
    state = VehicleState(mode=VehicleMode.IDLE, signals={'engine.oil_pressure': reading(0.1, quality=quality)})
    assert state.value('engine.oil_pressure') is None
    assert not any(e.code == 'LOW_OIL_PRESSURE' for e in RulesEngine().evaluate(state))

@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_sensor_becomes_invalid(value):
    r = reading(value)
    assert r.value is None and r.quality == SignalQuality.INVALID
    assert 'NaN' not in r.model_dump_json()


def test_empty_vehicle_is_unknown_not_normal():
    from mgo_brain.state_machine import infer_mode
    state = VehicleState()
    assert infer_mode(state) == VehicleMode.UNKNOWN
    assert HealthEngine().summary(state, [])['overall'] == 'UNKNOWN'


def test_new_sensor_failure_supersedes_old_good_value():
    agg = StateAggregator()
    agg.apply(update(2.5))
    state = agg.apply(update(None, when=NOW + timedelta(seconds=1), quality=SignalQuality.INVALID))
    assert state.value('engine.oil_pressure') is None
    assert state.signals['engine.oil_pressure'].quality == SignalQuality.INVALID


def test_retained_fallback_is_selected_when_primary_expires():
    agg = StateAggregator(stale_after_s=2, preferred_sources={'engine.oil_pressure': ['primary', 'backup']})
    agg.apply(update(2.5, 'primary'))
    agg.apply(update(2.4, 'backup', NOW + timedelta(seconds=1)))
    state = agg.snapshot(now=NOW + timedelta(seconds=2.5))
    assert state.value('engine.oil_pressure') == 2.4
    assert state.signals['engine.oil_pressure'].source == 'backup'


def test_backwards_source_update_does_not_replace_latest():
    agg = StateAggregator()
    agg.apply(update(2.5, when=NOW + timedelta(seconds=1)))
    state = agg.apply(update(0.0))
    assert state.value('engine.oil_pressure') == 2.5


def test_lost_evidence_does_not_clear_critical_alarm():
    manager = AlertManager(clear_after_s=1)
    event = Event(severity=Severity.CRITICAL, code='LOW_OIL_PRESSURE', message='test')
    manager.update([event], NOW)
    manager.update([], NOW + timedelta(seconds=10), unavailable_codes={'LOW_OIL_PRESSURE'})
    assert manager.active()[0].severity == Severity.CRITICAL
    assert manager.active()[0].data['recovery_confirmed'] is False
    manager.update([], NOW + timedelta(seconds=11))
    assert not manager.active()


def test_severity_change_is_a_persistable_transition():
    manager = AlertManager()
    manager.update([Event(code='TEST', message='test', severity=Severity.WATCH)], NOW)
    result = manager.update([Event(code='TEST', message='test', severity=Severity.CRITICAL)], NOW + timedelta(seconds=1))
    assert result[0].transition == AlertStatus.UPDATED


class Finite(SourceAdapter):
    name = 'test-finite'
    async def stream(self):
        yield update(2.5)


class Broken(SourceAdapter):
    name = 'test-broken'
    async def stream(self):
        if False:
            yield update(1)
        raise OSError('transport failed')


def test_mux_reaches_eof_and_reports_failed_source():
    async def scenario():
        mux = SourceMux([Finite()])
        values = [item async for item in mux.stream()]
        assert len(values) == 1
        broken = SourceMux([Finite(), Broken()])
        with pytest.raises(RuntimeError):
            async for _ in broken.stream():
                pass
        assert broken.errors
    asyncio.run(asyncio.wait_for(scenario(), timeout=2))


def test_history_failure_cannot_prevent_live_alert(tmp_path, monkeypatch):
    service = MGOBrainService(tmp_path)
    monkeypatch.setattr(service.store, 'add_event', lambda *a, **k: (_ for _ in ()).throw(OSError('disk full')))
    state = VehicleState(mode=VehicleMode.IDLE, signals={
        'engine.rpm': reading(930), 'engine.oil_pressure': reading(0.1), 'engine.oil_warning': reading(True),
        'engine.coolant_temp': reading(80), 'electrical.battery_voltage': reading(14.1)})
    service.process_state(state)
    assert any(a.code == 'LOW_OIL_PRESSURE' for a in service.alerts.active())
    assert service.health_summary()['overall'] == 'CRITICAL'
    assert service.runtime_errors


def test_all_sources_silent_eventually_marks_data_stale(tmp_path):
    class Silent(SourceAdapter):
        name = 'silent'
        async def stream(self):
            now = datetime.now(timezone.utc)
            yield update(2.5, when=now)
            await asyncio.Event().wait()
    async def scenario():
        service = MGOBrainService(tmp_path, source_adapter=Silent())
        service.aggregator.stale_after_s = 0.02
        await service.start()
        try:
            await asyncio.sleep(0.35)
            assert service.state.signals['engine.oil_pressure'].quality == SignalQuality.STALE
        finally:
            await service.stop()
    asyncio.run(scenario())


def test_explicit_missing_source_config_fails_instead_of_simulating(tmp_path):
    with pytest.raises(FileNotFoundError):
        MGOBrainService(tmp_path / 'data', source_config_path=tmp_path / 'missing.json')


def test_synthetic_and_vehicle_history_use_different_namespaces(tmp_path):
    simulated = MGOBrainService(tmp_path)
    vehicle = MGOBrainService(tmp_path, source_adapter=Finite())
    assert simulated.store.db_path != vehicle.store.db_path
    assert simulated.store.db_path.parent.name == 'simulator'
    assert vehicle.store.db_path.parent.name == 'vehicle'


def test_vedirect_byte_checksum_is_required():
    from mgo_brain.sources.vedirect import VEDirectByteParser
    body = b'\r\nV\t12650\r\nI\t2500\r\nChecksum\t'
    block = body + bytes([(-sum(body)) & 255])
    parser = VEDirectByteParser()
    assert parser.feed(block[:10]) == []
    result = parser.feed(block[10:])
    assert result == [{'V': '12650', 'I': '2500'}]
    damaged = block[:-1] + bytes([(block[-1]+1) & 255])
    assert parser.feed(damaged) == []
    assert parser.rejected_blocks == 1


def test_modbus_empty_reply_is_invalid_not_zero():
    from mgo_brain.sources.modbus import DigitalInputChannel, ModbusDigitalInputAdapter
    class Empty:
        async def read_discrete_inputs(self, *a, **kw): return []
        async def close(self): pass
    async def scenario():
        adapter = ModbusDigitalInputAdapter(Empty(), [DigitalInputChannel(0, 'controls.brake')])
        stream = adapter.stream()
        try:
            result = await anext(stream)
            assert result.signals['controls.brake'].value is None
            assert result.signals['controls.brake'].quality == SignalQuality.INVALID
        finally:
            await stream.aclose()
    asyncio.run(scenario())


def test_replay_decoder_reaches_eof():
    from mgo_brain.replay import CandumpReplayTransport
    from mgo_brain.sources.dbc import DBCSourceAdapter
    class Decoder:
        def decode(self, frame): return update(2.5)
    async def scenario():
        transport = CandumpReplayTransport.from_text('(1000.0) can0 123#01')
        adapter = DBCSourceAdapter(transport, Decoder())
        assert len([item async for item in adapter.stream()]) == 1
    asyncio.run(asyncio.wait_for(scenario(), timeout=1))


@pytest.mark.parametrize('line', ['can0 123 [1] AA trailing', 'can0 123 [9] 00 00 00 00 00 00 00 00 00', 'can0 FFFFFFFF#AA', 'can0 123#000000000000000000'])
def test_unsupported_candump_does_not_silently_parse(line):
    from mgo_brain.survey import parse_candump_line
    assert parse_candump_line(line) is None


def test_dbc_draft_uses_observed_length():
    from mgo_brain.survey import analyze_text
    result = analyze_text('can0 310#0000000000000000', 'can0 310#0001000000000000')
    assert 'MGO_310: 8 MGO_BFI' in result['draft_dbc']
    assert 'SG_' not in result['draft_dbc']


def test_backup_rejects_output_inside_its_input(tmp_path):
    from mgo_brain.backup import create_backup
    data = tmp_path / 'data'; data.mkdir()
    config = tmp_path / 'config'; config.mkdir()
    with pytest.raises(ValueError):
        create_backup(data_dir=data, config_dir=config, output=data / 'backup.tar.gz')


def test_cloud_model_must_be_configured(monkeypatch):
    from mgo_brain.ai_provider import OpenAIResponsesProvider
    from mgo_brain.ai_models import EvidencePacket
    monkeypatch.delenv('MGO_AI_MODEL', raising=False)
    provider = OpenAIResponsesProvider(client=SimpleNamespace())
    assert not provider.status().configured
    with pytest.raises(RuntimeError, match='MGO_AI_MODEL'):
        provider.answer(EvidencePacket(question='test'))


def test_requested_english_language_reaches_local_provider(tmp_path):
    from mgo_brain.ai_gateway import AIGateway
    service = MGOBrainService(tmp_path)
    response = AIGateway(service, provider_name='local').ask('How is the engine?', language='en')
    assert 'Local evidence report' in response.answer


def test_factory_can_requires_verified_listen_only(monkeypatch):
    from mgo_brain.sources.can import verify_listen_only
    monkeypatch.setattr('mgo_brain.sources.can.subprocess.run', lambda *a, **k: SimpleNamespace(stdout='[{"flags":["UP"],"linkinfo":{"info_kind":"can","info_data":{"ctrlmode":[]}}}]'))
    with pytest.raises(RuntimeError, match='LISTEN-ONLY'):
        verify_listen_only('can0')


def test_request_limit_is_enforced_on_streamed_body():
    from mgo_brain.request_limits import RequestLimitMiddleware
    sent = []
    async def app(scope, receive, send):
        raise AssertionError('Oversized input must not reach the application')
    async def scenario():
        async def receive(): return {'type':'http.request','body':b'x'*20,'more_body':False}
        async def send(item): sent.append(item)
        middleware = RequestLimitMiddleware(app, max_bytes=10)
        await middleware({'type':'http','method':'POST','headers':[]}, receive, send)
    asyncio.run(scenario())
    assert sent[0]['status'] == 413
