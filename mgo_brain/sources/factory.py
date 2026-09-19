from __future__ import annotations

from .can import SocketCANTransport
from .config import SourceFactory
from .dbc import DBCDecoder, DBCSignalMapping, DBCSourceAdapter
from .modbus import (
    AnalogInputChannel,
    DigitalInputChannel,
    ModbusAnalogInputAdapter,
    ModbusDigitalInputAdapter,
    PymodbusSerialTransport,
)
from .sensorhub import SensorHubChannel, SensorHubSourceAdapter
from .vedirect import SerialLineTransport, VEDirectSourceAdapter
from .bench import BenchRigSourceAdapter


def register_standard_hardware_builders(factory: SourceFactory) -> SourceFactory:
    """Register hardware builders without importing optional third-party packages yet.

    Optional packages are imported only if the corresponding configured source is
    actually instantiated.
    """

    def dbc_socketcan(options: dict):
        transport = SocketCANTransport(
            channel=str(options["channel"]),
            receive_timeout_s=float(options.get("receive_timeout_s", 1.0)),
        )
        mappings = [
            DBCSignalMapping(
                message=str(x["message"]),
                signal=str(x["signal"]),
                canonical=str(x["canonical"]),
                unit=x.get("unit"),
                scale=float(x.get("scale", 1.0)),
                offset=float(x.get("offset", 0.0)),
            )
            for x in options.get("mappings", [])
        ]
        source = str(options.get("source", "can.bfi"))
        decoder = DBCDecoder(
            dbc_path=options["dbc_path"],
            mappings=mappings,
            source=source,
        )
        return DBCSourceAdapter(transport, decoder, name=source)

    def sensorhub_socketcan(options: dict):
        transport = SocketCANTransport(
            channel=str(options["channel"]),
            receive_timeout_s=float(options.get("receive_timeout_s", 1.0)),
        )
        channels = [
            SensorHubChannel(
                node_id=int(x["node_id"]),
                channel=int(x["channel"]),
                canonical=str(x["canonical"]),
                unit=x.get("unit"),
                source=x.get("source"),
            )
            for x in options.get("channels", [])
        ]
        return SensorHubSourceAdapter(
            transport,
            channels,
            base_id=int(options.get("base_id", 0x600)),
        )

    def modbus_di(options: dict):
        transport = PymodbusSerialTransport(
            port=str(options["port"]),
            baudrate=int(options.get("baudrate", 9600)),
            parity=str(options.get("parity", "N")),
            stopbits=int(options.get("stopbits", 1)),
        )
        channels = [
            DigitalInputChannel(
                address=int(x["address"]),
                canonical=str(x["canonical"]),
                invert=bool(x.get("invert", False)),
                source=str(x.get("source", "digital.oem")),
            )
            for x in options.get("channels", [])
        ]
        return ModbusDigitalInputAdapter(
            transport,
            channels,
            slave=int(options.get("slave", 1)),
            poll_interval_s=float(options.get("poll_interval_s", 0.2)),
        )

    def modbus_ai(options: dict):
        transport = PymodbusSerialTransport(
            port=str(options["port"]),
            baudrate=int(options.get("baudrate", 9600)),
            parity=str(options.get("parity", "N")),
            stopbits=int(options.get("stopbits", 1)),
        )
        channels = [
            AnalogInputChannel(
                address=int(x["address"]),
                canonical=str(x["canonical"]),
                unit=x.get("unit"),
                scale=float(x.get("scale", 1.0)),
                offset=float(x.get("offset", 0.0)),
                signed=bool(x.get("signed", False)),
                source=str(x.get("source", "modbus.ai")),
            )
            for x in options.get("channels", [])
        ]
        return ModbusAnalogInputAdapter(
            transport,
            channels,
            slave=int(options.get("slave", 1)),
            poll_interval_s=float(options.get("poll_interval_s", 0.2)),
        )

    def vedirect_serial(options: dict):
        return VEDirectSourceAdapter(
            SerialLineTransport(
                port=str(options["port"]),
                baudrate=int(options.get("baudrate", 19200)),
            )
        )

    factory.register("dbc_socketcan", dbc_socketcan)
    factory.register("sensorhub_socketcan", sensorhub_socketcan)
    factory.register("modbus_di", modbus_di)
    factory.register("modbus_ai", modbus_ai)
    factory.register("vedirect_serial", vedirect_serial)
    factory.register(
        "bench",
        lambda options: BenchRigSourceAdapter(
            scenario=str(options.get("scenario", "normal")),
            time_scale=float(options.get("time_scale", 4.0)),
        ),
    )
    return factory
