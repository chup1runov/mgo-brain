# UI Visual Concept

This file is the canonical design intent for the driver-facing MGO Brain interface.

## Language

Target driver UI: **Russian**.

Engineering/debug identifiers may remain English where they map directly to code/CAN terminology.

## Visual language

- dark navy/charcoal background;
- high contrast;
- green = normal;
- amber/orange = watch/attention;
- red = critical;
- grey = unknown/unavailable/stale;
- large numeric values;
- minimal text while driving;
- detailed engineering information moved into secondary screens.

## Main / driver screen

Primary visible elements:

```text
MGO BRAIN                         ● LIVE

               42 км/ч
              2 870 об/мин

ДВИГАТЕЛЬ      CVT         АКБ
НОРМА          НОРМА       НОРМА

ОЖ             81 °C
Масло          84 °C / 2.3 бар
АКБ            14.16 В
CVT drift      +1.8 %

Активных неисправностей нет

ГЛАВНАЯ | ДВИГАТЕЛЬ | CVT | ПИТАНИЕ | ПОЕЗДКИ | СЕРВИС
```

## Subsystem cards

Top-level system status should expose:

- Двигатель;
- Вариатор (CVT);
- Электрика;
- Шины;
- Тормоза;
- optional cabin/environment.

Each card uses:

- НОРМА;
- НАБЛЮДАТЬ;
- ВНИМАНИЕ;
- КРИТИЧНО;
- НЕТ ДАННЫХ / UNKNOWN.

Do not show NORMAL when required signals are missing/stale.

## ENGINE

- RPM;
- coolant temperature;
- oil temperature;
- oil pressure;
- glow current/status;
- starter current/status;
- start history;
- baseline deviations.

## CVT

- current RPM/speed ratio;
- ratio deviation from baseline;
- primary temperature;
- secondary temperature;
- gearbox temperature later;
- trend/history.

## POWER

- battery voltage;
- current;
- SoC;
- alternator voltage;
- crank minimum voltage;
- overnight/quiescent consumption later.

## TRIPS

- distance;
- duration;
- average/max speed;
- post-trip status;
- anomalies;
- compare two trips.

## SERVICE

- oil/filter;
- air filter;
- CVT inspection/replacement;
- gearbox oil;
- brake fluid;
- coolant;
- later component install/replacement history.

## ASK MGO

The HOME screen includes a compact Russian question panel:

```text
Спросить MGO
[ Почему сегодня дольше заводился? ]

[ Спросить MGO ] [ Двигатель ] [ АКБ ] [ CVT ]

Ответ строится только по данным MGO Brain.
Provider: LOCAL / OPENAI
```

The driver-facing answer shows the response and names of evidence tools used, but not the full raw evidence packet.

External AI is optional; local fallback must still work without Internet.

## LAB

LAB is explicitly an engineering screen and may contain:

- raw normalized state;
- source quality;
- fault simulator;
- CAN survey baseline/action;
- numeric discovery;
- saved survey sessions;
- generated safe DBC draft.

LAB is not intended for use while driving.

## Phone vs dedicated display

First real deployment may use a phone/PWA.

Dedicated 7–10 inch display is optional later and runs the same UI in `?kiosk=1` mode.

The display remains a client. Telemetry/logging/alerts continue if the screen/browser fails.

## Localization status

v0.5.8 implements Russian as the default driver-facing language.

- Russian: default.
- English: fallback via `?lang=en` or the RU/EN toggle.
- canonical signal/API names remain unchanged;
- LAB may still expose engineering identifiers where exact code/CAN terminology matters.
