from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from mgo_brain.health import HealthEngine
from mgo_brain.models import SignalQuality, SignalReading, VehicleMode, VehicleState
from mgo_brain.sources.aggregator import StateAggregator
from mgo_brain.sources.base import SourceAdapter, SourceUpdate
from mgo_brain.sources.can import CanFrame, SocketCANTransport
from mgo_brain.sources.config import SourceFactory, load_source_config
from mgo_brain.sources.dbc import DBCDecoder, DBCSignalMapping
from mgo_brain.sources.gnss import GNSSIMUSourceAdapter, MotionPacket
from mgo_brain.sources.modbus import AnalogInputChannel, DigitalInputChannel, ModbusAnalogInputAdapter, ModbusDigitalInputAdapter
from mgo_brain.sources.mux import SourceMux
from mgo_brain.sources.sensorhub import SensorHubChannel, SensorHubCodec, SensorHubSample, SensorHubSourceAdapter, SensorValueType
from mgo_brain.sources.tpms import TPMSPacket, TPMSSourceAdapter
from mgo_brain.sources.vedirect import VEDirectParser, VEDirectSourceAdapter
from mgo_brain.state_machine import infer_mode


def ts(seconds=0):
    return datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds)


def reading(value, source, at, unit=None, quality=SignalQuality.GOOD):
    return SignalReading(value=value, unit=unit, source=source, timestamp=at, quality=quality)


def update(source, name, value, at, unit=None, reading_source=None):
    return SourceUpdate(
        source=source,
        timestamp=at,
        signals={name: reading(value, reading_source or source, at, unit)},
    )


def one(adapter):
    async def _run():
        stream = adapter.stream()
        try:
            return await anext(stream)
        finally:
            await stream.aclose()
    return asyncio.run(_run())


def test_aggregator_prefers_primary_while_fresh_then_fails_over_when_stale():
    agg = StateAggregator(
        stale_after_s=3,
        preferred_sources={"vehicle.speed": ["can.bfi", "gnss"]},
    )
    a = agg.apply(update("can", "vehicle.speed", 40, ts(0), "km/h", "can.bfi"))
    assert a.value("vehicle.speed") == 40
    assert a.signals["vehicle.speed"].source == "can.bfi"

    b = agg.apply(update("gps", "vehicle.speed", 39, ts(1), "km/h", "gnss"), now=ts(1))
    assert b.value("vehicle.speed") == 40
    assert b.signals["vehicle.speed"].source == "can.bfi"

    c = agg.apply(update("gps", "vehicle.speed", 38, ts(4), "km/h", "gnss"), now=ts(4))
    assert c.value("vehicle.speed") == 38
    assert c.signals["vehicle.speed"].source == "gnss"


def test_aggregator_marks_old_signal_stale():
    agg = StateAggregator(stale_after_s=2)
    agg.apply(update("sensor", "engine.coolant_temp", 80, ts(0), "°C"))
    snap = agg.snapshot(now=ts(3))
    assert snap.signals["engine.coolant_temp"].quality == SignalQuality.STALE


def test_stale_rpm_does_not_hold_vehicle_in_driving_mode():
    state = VehicleState(
        signals={
            "engine.rpm": reading(2800, "tach", ts(0), "rpm", SignalQuality.STALE),
            "vehicle.speed": reading(40, "can.bfi", ts(0), "km/h", SignalQuality.STALE),
            "electrical.ignition": reading(True, "digital.oem", ts(0)),
        }
    )
    assert infer_mode(state) == VehicleMode.IGNITION


def test_health_engine_does_not_call_stale_engine_normal():
    state = VehicleState(
        mode=VehicleMode.IDLE,
        signals={
            "engine.rpm": reading(900, "tach", ts(0), "rpm", SignalQuality.STALE),
            "engine.coolant_temp": reading(80, "sensor.coolant", ts(0), "°C", SignalQuality.STALE),
            "engine.oil_pressure": reading(1.5, "sensor.oil", ts(0), "bar", SignalQuality.STALE),
        },
    )
    summary = HealthEngine().summary(state, [])
    engine = next(x for x in summary["subsystems"] if x["subsystem"] == "ENGINE")
    assert engine["status"] == "UNKNOWN"


class OneShot(SourceAdapter):
    def __init__(self, name, item):
        self.name = name
        self.item = item
        self.closed = False

    async def stream(self):
        yield self.item

    async def close(self):
        self.closed = True


def test_source_mux_fans_in_multiple_sources():
    async def run():
        a = OneShot("a", update("a", "engine.rpm", 900, ts(0), "rpm"))
        b = OneShot("b", update("b", "vehicle.speed", 10, ts(0), "km/h"))
        mux = SourceMux([a, b])
        stream = mux.stream()
        got = [await anext(stream), await anext(stream)]
        await stream.aclose()
        return {x.source for x in got}, a.closed, b.closed

    names, a_closed, b_closed = asyncio.run(run())
    assert names == {"a", "b"}
    assert a_closed and b_closed


def test_socketcan_transport_has_no_transmit_api():
    transport = SocketCANTransport("can0", bus_factory=lambda **kwargs: None)
    assert not hasattr(transport, "send")


class FakeMessage:
    name = "Vehicle"

    def decode(self, data, decode_choices=False):
        return {"Speed": 42.5, "Ignored": 123}


class FakeDB:
    def get_message_by_frame_id(self, frame_id):
        if frame_id != 0x123:
            raise KeyError(frame_id)
        return FakeMessage()


def test_dbc_decoder_maps_only_selected_signals():
    decoder = DBCDecoder(
        database=FakeDB(),
        mappings=[DBCSignalMapping("Vehicle", "Speed", "vehicle.speed", "km/h")],
    )
    frame = CanFrame(0x123, b"\x00" * 8, ts(0))
    result = decoder.decode(frame)
    assert result is not None
    assert result.signals["vehicle.speed"].value == pytest.approx(42.5)
    assert result.signals["vehicle.speed"].source == "can.bfi"
    assert len(result.signals) == 1


def test_sensorhub_codec_roundtrip_and_mapping():
    sample = SensorHubSample(node_id=2, channel=7, value=81.25, flags=0, value_type=SensorValueType.FLOAT32)
    frame = SensorHubCodec.encode(sample)
    decoded = SensorHubCodec.decode(frame)
    assert decoded is not None
    assert decoded.node_id == 2
    assert decoded.channel == 7
    assert decoded.value == pytest.approx(81.25, rel=1e-5)

    class Transport:
        async def recv(self, timeout=None): return frame
        async def close(self): pass

    adapter = SensorHubSourceAdapter(
        Transport(),
        [SensorHubChannel(2, 7, "engine.coolant_temp", "°C", "sensor.coolant")],
    )
    result = one(adapter)
    r = result.signals["engine.coolant_temp"]
    assert r.value == pytest.approx(81.25, rel=1e-5)
    assert r.source == "sensor.coolant"


class FakeModbus:
    def __init__(self):
        self.closed = False
    async def read_discrete_inputs(self, address, count, *, slave):
        return [address == 3]
    async def read_input_registers(self, address, count, *, slave):
        return [1250]
    async def close(self):
        self.closed = True


def test_modbus_digital_and_analog_adapters_normalize_signals():
    di = one(ModbusDigitalInputAdapter(
        FakeModbus(),
        [DigitalInputChannel(3, "controls.brake")],
        poll_interval_s=99,
    ))
    assert di.signals["controls.brake"].value is True
    assert di.signals["controls.brake"].source == "digital.oem"

    ai = one(ModbusAnalogInputAdapter(
        FakeModbus(),
        [AnalogInputChannel(1, "engine.coolant_temp", "°C", scale=0.1, source="sensor.coolant")],
        poll_interval_s=99,
    ))
    assert ai.signals["engine.coolant_temp"].value == pytest.approx(125.0)
    assert ai.signals["engine.coolant_temp"].source == "sensor.coolant"


def test_vedirect_parser_and_adapter():
    parser = VEDirectParser()
    assert parser.feed("V\t12650\r\n") is None
    assert parser.feed("I\t2500\r\n") is None
    block = parser.feed("Checksum\tX\r\n")
    assert block == {"V": "12650", "I": "2500"}

    class Lines:
        def __init__(self):
            self.lines = iter(["V\t12650\n", "I\t2500\n", "SOC\t825\n", "Checksum\tX\n"])
        async def read_line(self):
            try: return next(self.lines)
            except StopIteration: return None
        async def close(self): pass

    result = one(VEDirectSourceAdapter(Lines()))
    assert result.signals["electrical.battery_voltage"].value == pytest.approx(12.65)
    assert result.signals["electrical.battery_current"].value == pytest.approx(2.5)
    assert result.signals["electrical.battery_soc"].value == pytest.approx(82.5)


def test_tpms_adapter_maps_wheel():
    class T:
        async def recv(self): return TPMSPacket("fl", 1.55, 23.0)
        async def close(self): pass
    result = one(TPMSSourceAdapter(T()))
    assert result.signals["tyres.fl.pressure"].value == pytest.approx(1.55)
    assert result.signals["tyres.fl.temp"].value == pytest.approx(23.0)


def test_gnss_imu_adapter_uses_logical_sources():
    class T:
        async def recv(self):
            return MotionPacket(latitude=57.7, longitude=12.0, speed_kmh=41.2, accel_x_ms2=0.3)
        async def close(self): pass
    result = one(GNSSIMUSourceAdapter(T()))
    assert result.signals["vehicle.speed_gps"].source == "gnss"
    assert result.signals["motion.accel_x"].source == "autopi.imu"


def test_source_config_and_factory(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps({
        "stale_after_s": 4.5,
        "sources": [{"type": "fake", "enabled": True, "options": {"value": 7}}],
    }), encoding="utf-8")
    config = load_source_config(path)
    assert config.stale_after_s == pytest.approx(4.5)

    factory = SourceFactory()
    factory.register(
        "fake",
        lambda options: OneShot(
            "fake",
            update("fake", "fuel.level", options["value"], ts(0), "%"),
        ),
    )
    adapter = factory.build(config)
    result = one(adapter)
    assert result.signals["fuel.level"].value == 7
