from dataclasses import dataclass


@dataclass(frozen=True)
class SignalSpec:
    name: str
    unit: str | None
    description: str
    preferred_sources: tuple[str, ...]


SIGNALS: dict[str, SignalSpec] = {
    "vehicle.speed": SignalSpec("vehicle.speed", "km/h", "Normalized road speed", ("can.bfi", "speed.pulse", "gnss")),
    "vehicle.speed_gps": SignalSpec("vehicle.speed_gps", "km/h", "GNSS speed", ("gnss",)),
    "engine.rpm": SignalSpec("engine.rpm", "rpm", "Engine speed", ("can.bfi", "tach.signal", "hall.rpm")),
    "engine.coolant_temp": SignalSpec("engine.coolant_temp", "°C", "Coolant temperature", ("sensor.coolant", "can.bfi")),
    "engine.oil_temp": SignalSpec("engine.oil_temp", "°C", "Engine oil temperature", ("sensor.oil",)),
    "engine.oil_pressure": SignalSpec("engine.oil_pressure", "bar", "Engine oil pressure", ("sensor.oil",)),
    "engine.oil_warning": SignalSpec("engine.oil_warning", None, "OEM low-oil-pressure warning switch", ("digital.oem", "can.bfi")),
    "engine.overheat_warning": SignalSpec("engine.overheat_warning", None, "OEM high-temperature warning", ("digital.oem", "can.bfi")),
    "engine.glow_active": SignalSpec("engine.glow_active", None, "Glow relay state", ("digital.oem",)),
    "engine.starter_active": SignalSpec("engine.starter_active", None, "Starter command", ("digital.oem",)),
    "electrical.battery_voltage": SignalSpec("electrical.battery_voltage", "V", "Battery/system voltage", ("smartshunt", "adc", "autopi")),
    "electrical.battery_current": SignalSpec("electrical.battery_current", "A", "Battery current", ("smartshunt", "hall.current")),
    "electrical.battery_soc": SignalSpec("electrical.battery_soc", "%", "Estimated battery state of charge", ("smartshunt",)),
    "transmission.gear": SignalSpec("transmission.gear", None, "D/N/R selector state", ("can.bfi", "digital.oem")),
    "transmission.cvt_ratio": SignalSpec("transmission.cvt_ratio", "rpm/(km/h)", "Derived RPM/speed CVT indicator", ("derived",)),
    "fuel.level": SignalSpec("fuel.level", "%", "Fuel level", ("can.bfi", "analog.oem")),
    "body.driver_door": SignalSpec("body.driver_door", None, "Driver door state", ("can.bfi", "digital.oem")),
    "controls.brake": SignalSpec("controls.brake", None, "Brake switch", ("can.bfi", "digital.oem")),
    "controls.parking_brake": SignalSpec("controls.parking_brake", None, "Parking brake switch", ("can.bfi", "digital.oem")),
    "environment.ambient_temp": SignalSpec("environment.ambient_temp", "°C", "Ambient temperature", ("can.bfi", "sensor.ambient")),
}
