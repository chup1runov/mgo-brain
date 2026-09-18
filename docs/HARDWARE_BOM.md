# Hardware BOM / Decision Register

This is a planning BOM, not a purchase receipt. Re-check current price, availability, revision and electrical specifications before ordering.

| Item | Role | Current status | Notes |
|---|---|---|---|
| AutoPi TMU CM4 or equivalent automotive Linux computer | Main Brain | Preferred | Automotive power management, Linux, CAN, GNSS/connectivity |
| ESP32-S3 CAN/RS485 protected board | SensorHub | Preferred class | Separate Sensor CAN; local acquisition |
| Isolated Modbus RTU digital input modules | OEM 12 V states | Planned | Use only when reliable signal not available over factory CAN |
| Protected analog acquisition | Pressure/temp sensors | Planned | Accuracy chosen per sensor, not one generic ADC for all |
| Victron SmartShunt IP65 500 A class | Battery current/SoC | Candidate | Must be installed in correct negative-current path |
| Bosch Motorsport PST-F 1 class | Oil pressure + temperature | Candidate | Do not buy adaptor until engine thread is confirmed |
| Independent coolant temperature sensor | Cooling | Candidate | Final sensor/adaptor depends on actual hose/port dimensions |
| ADXL355-class low-noise accelerometer | Engine vibration | Candidate | Fixed to engine/structure; condition monitoring |
| TPMS set | Tyre pressure/temp | Planned | Vendor/protocol not selected |
| 7–10 inch display or Android tablet | Dedicated UI | Deferred | First test UI on phone/tablet before final screen purchase |
| Automotive fuse/distribution hardware | Power | Required later | Dedicated fused MGO Brain branch |
| Automotive twisted pair | CAN wiring | Required later | Factory CAN stub kept short; private Sensor CAN wired separately |
| Deutsch/automotive connectors | Removable harness | Preferred | Avoid permanent improvised splices |

## Purchasing rule

Do not buy a sensor or adaptor whose physical interface is still unknown.

Examples:

- oil sender thread → measure/confirm first;
- coolant hose/adaptor size → measure first;
- permanent display → test viewing geometry first;
- factory CAN connector parts → identify connector first.

## No-control rule

The BOM intentionally excludes actuators for:

- throttle/governor;
- brake;
- steering;
- D/N/R;
- starter;
- glow control;
- speed limiter.

MGO Brain is an observer/diagnostic system, not a replacement controller.
