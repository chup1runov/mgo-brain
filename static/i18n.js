window.MGOI18N = (() => {
  const dictionaries = {
    ru: {
      "app.subtitle": "v0.5.8 • русский интерфейс",
      "conn.connecting": "подключение",
      "nav.home": "ГЛАВНАЯ",
      "nav.engine": "ДВИГАТЕЛЬ",
      "nav.cvt": "CVT",
      "nav.power": "ПИТАНИЕ",
      "nav.trips": "ПОЕЗДКИ",
      "nav.service": "СЕРВИС",
      "nav.lab": "LAB",
      "metric.speed": "Скорость",
      "metric.engine": "Двигатель",
      "metric.mode": "Режим",
      "metric.overall": "Общее состояние",
      "metric.coolant": "ОЖ",
      "metric.oil_pressure": "Давление масла",
      "metric.battery": "АКБ",
      "metric.cvt_drift": "Отклонение CVT",
      "section.health": "Состояние систем",
      "section.alerts": "Активные предупреждения",
      "section.latest_trip": "Последняя поездка",
      "section.ask": "Спросить MGO",
      "ask.title": "Диагностический помощник",
      "ask.subtitle": "Ответ строится только по данным MGO Brain.",
      "ask.placeholder": "Например: почему сегодня дольше заводился?",
      "ask.button": "Спросить MGO",
      "ask.engine": "Двигатель",
      "ask.battery": "АКБ",
      "ask.cvt": "CVT",
      "ask.ready": "Готово.",
      "engine.rpm": "Обороты",
      "engine.coolant": "Температура ОЖ",
      "engine.oil_temp": "Температура масла",
      "engine.oil_pressure": "Давление масла",
      "engine.glow_current": "Ток свечей накала",
      "engine.starter_current": "Ток стартера",
      "engine.start_history": "История запусков",
      "engine.baselines": "Базовые значения двигателя",
      "cvt.ratio": "Передаточное отношение CVT",
      "cvt.drift": "Отклонение отношения",
      "cvt.primary_temp": "Температура ведущего вариатора",
      "cvt.secondary_temp": "Температура ведомого вариатора",
      "cvt.baseline": "Историческая норма CVT",
      "power.battery_voltage": "Напряжение АКБ",
      "power.battery_current": "Ток АКБ",
      "power.battery_soc": "Заряд АКБ",
      "power.alternator": "Генератор",
      "power.baseline": "Электрические базовые значения",
      "trips.compare": "Сравнить поездки",
      "trips.compare_button": "Сравнить",
      "trips.history": "История поездок",
      "trips.report": "Отчёт по выбранной поездке",
      "trips.select_report": "Выберите поездку для просмотра отчёта.",
      "service.plan": "Регламент обслуживания",
      "service.note": "Регламент основан на документации Progress ACT / MGO. Он ещё не привязан к подтверждённому реальному одометру и датам замен.",
      "lab.clear_faults": "Сбросить неисправности симулятора",
      "lab.refresh": "Обновить",
      "lab.faults": "Лаборатория неисправностей",
      "lab.analytics": "Аналитика",
      "lab.baselines": "Все базовые значения",
      "lab.can_survey": "Поиск CAN-сигналов",
      "lab.baseline": "Базовый candump",
      "lab.action": "Candump после действия",
      "lab.load_demo": "Загрузить демо",
      "lab.analyze": "Сравнить логи",
      "lab.save_session": "Сохранить сессию",
      "lab.numeric": "Поиск числового сигнала",
      "lab.numeric_demo": "Загрузить числовое демо",
      "lab.numeric_analyze": "Найти числовой сигнал",
      "lab.saved_sessions": "Сохранённые сессии",
      "lab.raw_state": "Сырое текущее состояние",
      "lab.safe_dbc": "Безопасный DBC-черновик",
      "common.no_alerts": "Активных предупреждений нет.",
      "common.no_health": "Нет данных о состоянии систем.",
      "common.no_starts": "Истории запусков пока нет.",
      "common.no_trips": "Завершённых поездок пока нет.",
      "common.normal": "НОРМА",
      "common.watch": "НАБЛЮДАТЬ",
      "common.attention": "ВНИМАНИЕ",
      "common.critical": "КРИТИЧНО",
      "common.unknown": "НЕТ ДАННЫХ",
      "common.unqualified": "НЕДОСТАТОЧНО ДАННЫХ",
      "common.offline": "нет связи",
      "common.live": "● в сети",
      "common.reconnecting": "переподключение",
      "mode.OFF": "ВЫКЛ",
      "mode.ACC": "ACC",
      "mode.IGNITION": "ЗАЖИГАНИЕ",
      "mode.PREHEAT": "НАКАЛ",
      "mode.CRANKING": "ЗАПУСК",
      "mode.ENGINE_RUNNING": "ДВИГАТЕЛЬ РАБОТАЕТ",
      "mode.IDLE": "ХОЛОСТОЙ ХОД",
      "mode.DRIVING": "ДВИЖЕНИЕ",
      "mode.REVERSING": "ЗАДНИЙ ХОД",
      "mode.FAULT": "НЕИСПРАВНОСТЬ",
      "subsystem.ENGINE": "ДВИГАТЕЛЬ",
      "subsystem.CVT": "CVT",
      "subsystem.ELECTRICAL": "ЭЛЕКТРИКА",
      "subsystem.TYRES": "ШИНЫ",
      "subsystem.BRAKES": "ТОРМОЗА",
      "maintenance.engine_oil_and_filter": "Масло двигателя + фильтр",
      "maintenance.air_filter": "Воздушный фильтр",
      "maintenance.cvt_belt_inspection": "Проверка ремня CVT",
      "maintenance.cvt_belt_replacement": "Замена ремня CVT",
      "maintenance.gearbox_oil": "Масло редуктора",
      "maintenance.brake_fluid": "Тормозная жидкость",
      "maintenance.coolant": "Охлаждающая жидкость",
      "unit.kmh": "км/ч",
      "unit.rpm": "об/мин",
      "unit.bar": "бар",
      "unit.volt": "В",
      "unit.amp": "А",
      "trip.avg": "ср.",
      "trip.max_coolant": "макс. ОЖ",
      "trip.baseline": "эталон",
      "trip.excluded": "исключена"
    },
    en: {
      "app.subtitle": "v0.5.8 • English UI",
      "conn.connecting": "connecting",
      "nav.home": "HOME",
      "nav.engine": "ENGINE",
      "nav.cvt": "CVT",
      "nav.power": "POWER",
      "nav.trips": "TRIPS",
      "nav.service": "SERVICE",
      "nav.lab": "LAB",
      "metric.speed": "Speed",
      "metric.engine": "Engine",
      "metric.mode": "Mode",
      "metric.overall": "Overall",
      "metric.coolant": "Coolant",
      "metric.oil_pressure": "Oil pressure",
      "metric.battery": "Battery",
      "metric.cvt_drift": "CVT drift",
      "section.health": "Subsystem health",
      "section.alerts": "Active alerts",
      "section.latest_trip": "Latest trip",
      "section.ask": "Ask MGO",
      "ask.title": "Diagnostic assistant",
      "ask.subtitle": "The answer is based only on MGO Brain data.",
      "ask.placeholder": "For example: why did it start slower today?",
      "ask.button": "Ask MGO",
      "ask.engine": "Engine",
      "ask.battery": "Battery",
      "ask.cvt": "CVT",
      "ask.ready": "Ready.",
      "engine.rpm": "RPM",
      "engine.coolant": "Coolant",
      "engine.oil_temp": "Oil temp",
      "engine.oil_pressure": "Oil pressure",
      "engine.glow_current": "Glow current",
      "engine.starter_current": "Starter current",
      "engine.start_history": "Start history",
      "engine.baselines": "Engine baselines",
      "cvt.ratio": "CVT ratio",
      "cvt.drift": "Ratio drift",
      "cvt.primary_temp": "Primary temp",
      "cvt.secondary_temp": "Secondary temp",
      "cvt.baseline": "Historical CVT baseline",
      "power.battery_voltage": "Battery voltage",
      "power.battery_current": "Battery current",
      "power.battery_soc": "Battery SoC",
      "power.alternator": "Alternator",
      "power.baseline": "Electrical baselines",
      "trips.compare": "Compare trips",
      "trips.compare_button": "Compare",
      "trips.history": "Trip history",
      "trips.report": "Selected report",
      "trips.select_report": "Select a trip to view its report.",
      "service.plan": "Maintenance plan",
      "service.note": "The registry reflects documented Progress ACT/MGO service intervals. It is not yet tied to a verified live odometer or replacement dates.",
      "lab.clear_faults": "Clear simulator faults",
      "lab.refresh": "Refresh",
      "lab.faults": "Fault laboratory",
      "lab.analytics": "Analytics",
      "lab.baselines": "All baselines",
      "lab.can_survey": "CAN Survey Toolkit",
      "lab.baseline": "Baseline candump",
      "lab.action": "Action candump",
      "lab.load_demo": "Load demo",
      "lab.analyze": "Analyze baseline vs action",
      "lab.save_session": "Save survey session",
      "lab.numeric": "Numeric Signal Discovery",
      "lab.numeric_demo": "Load numeric demo",
      "lab.numeric_analyze": "Analyze numeric signal",
      "lab.saved_sessions": "Saved survey sessions",
      "lab.raw_state": "Raw live state",
      "lab.safe_dbc": "Safe draft DBC",
      "common.no_alerts": "No active alerts.",
      "common.no_health": "No health data.",
      "common.no_starts": "No starts yet.",
      "common.no_trips": "No completed trips.",
      "common.normal": "NORMAL",
      "common.watch": "WATCH",
      "common.attention": "ATTENTION",
      "common.critical": "CRITICAL",
      "common.unknown": "UNKNOWN",
      "common.unqualified": "UNQUALIFIED",
      "common.offline": "offline",
      "common.live": "● live",
      "common.reconnecting": "reconnecting",
      "mode.OFF": "OFF",
      "mode.ACC": "ACC",
      "mode.IGNITION": "IGNITION",
      "mode.PREHEAT": "PREHEAT",
      "mode.CRANKING": "CRANKING",
      "mode.ENGINE_RUNNING": "ENGINE RUNNING",
      "mode.IDLE": "IDLE",
      "mode.DRIVING": "DRIVING",
      "mode.REVERSING": "REVERSING",
      "mode.FAULT": "FAULT",
      "subsystem.ENGINE": "ENGINE",
      "subsystem.CVT": "CVT",
      "subsystem.ELECTRICAL": "ELECTRICAL",
      "subsystem.TYRES": "TYRES",
      "subsystem.BRAKES": "BRAKES",
      "unit.kmh": "km/h",
      "unit.rpm": "rpm",
      "unit.bar": "bar",
      "unit.volt": "V",
      "unit.amp": "A",
      "trip.avg": "avg",
      "trip.max_coolant": "max coolant",
      "trip.baseline": "baseline",
      "trip.excluded": "excluded"
    }
  };

  function detect() {
    const params = new URLSearchParams(location.search);
    const requested = (params.get("lang") || localStorage.getItem("mgo-lang") || "ru").toLowerCase();
    return dictionaries[requested] ? requested : "ru";
  }

  let current = detect();

  function t(key, fallback) {
    return dictionaries[current]?.[key] ?? dictionaries.en?.[key] ?? fallback ?? key;
  }

  function status(value) {
    const key = {
      NORMAL: "common.normal",
      WATCH: "common.watch",
      ATTENTION: "common.attention",
      CRITICAL: "common.critical",
      UNKNOWN: "common.unknown",
      UNQUALIFIED: "common.unqualified"
    }[value];
    return key ? t(key, value) : value;
  }

  function mode(value) {
    return t("mode." + value, value);
  }

  function subsystem(value) {
    return t("subsystem." + value, value);
  }

  function maintenance(value) {
    return t("maintenance." + value, value);
  }

  function apply(lang=current) {
    current = dictionaries[lang] ? lang : "ru";
    localStorage.setItem("mgo-lang", current);
    document.documentElement.lang = current;
    document.querySelectorAll("[data-i18n]").forEach(el => {
      el.textContent = t(el.dataset.i18n, el.textContent);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder, el.getAttribute("placeholder") || ""));
    });
    return current;
  }

  function language() { return current; }

  return { t, status, mode, subsystem, maintenance, apply, language };
})();
