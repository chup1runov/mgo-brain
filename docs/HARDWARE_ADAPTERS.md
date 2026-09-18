# Hardware Adapter Layer

## SourceAdapter contract

Adapters emit `SourceUpdate` objects containing only the canonical signals they currently know. They do not need to produce a complete VehicleState.

## Implemented adapters

### Simulator
`SimulatorSourceAdapter` wraps the diagnostic simulator and remains the default source.

### Factory CAN / DBC
`SocketCANTransport` receives raw frames. `DBCDecoder` maps selected DBC message/signal pairs to canonical MGO Brain names. No send API exists in this layer.

**Deployment requirement:** configure the Linux CAN interface in listen-only mode before connecting to the factory bus.

### SensorHub CAN
Sensor CAN v1 is intended for the separate CAN1 bus. Default ID range starts at `0x600`, with node ID added to the base. This range is for the private Sensor CAN only and must not be assumed safe on factory CAN.

### Modbus / RS485
`ModbusDigitalInputAdapter` is intended for isolated OEM 12 V state acquisition. `ModbusAnalogInputAdapter` supports scaling, offset, signed values and logical source labels for independent sensors.

### VE.Direct
`VEDirectSourceAdapter` converts configurable fields into canonical battery signals. Default mappings cover voltage, current and SoC. Transport/checksum handling remains separate from canonical normalization.

### TPMS
`TPMSSourceAdapter` defines the normalized wheel pressure/temperature boundary. A vendor-specific RF/BLE transport still needs to be chosen.

### GNSS / IMU
`GNSSIMUSourceAdapter` normalizes position, GPS speed and acceleration. The actual AutoPi/GNSS provider transport is deployment-specific.

## Runtime config

`config/sources.json` currently enables the simulator only. The `SourceFactory` can build multiple adapters and combine them through `SourceMux`.

Hardware-specific settings and MGO CAN mappings must not be filled with guessed values. They are added only after the physical survey.
