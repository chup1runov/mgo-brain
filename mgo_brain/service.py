from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .alerts import AlertManager, AlertStatus
from .analytics import HistoricalAnalytics
from .baseline import BaselineManager
from .detectors import StartDetector, TripDetector
from .faults import FaultScenario
from .health import HealthEngine
from .models import AIContext, Event, Severity, TripSummary, VehicleMode, VehicleState
from .reports import PostTripReportEngine
from .rules import RulesEngine
from .simulator import MGOSimulator
from .sources.aggregator import StateAggregator
from .sources.base import SourceAdapter
from .sources.config import RuntimeSourceConfig, SourceEntry, SourceFactory, load_preferred_sources, load_source_config
from .sources.factory import register_standard_hardware_builders
from .store import Store

LOG=logging.getLogger(__name__)
SEVERITY_RANK={Severity.INFO:0,Severity.WATCH:1,Severity.ATTENTION:2,Severity.CRITICAL:3}
RULE_INPUTS={
 'OEM_OIL_PRESSURE_WARNING':('engine.rpm','engine.oil_warning'),
 'LOW_OIL_PRESSURE':('engine.rpm','engine.oil_pressure'),
 'OEM_OVERHEAT_WARNING':('engine.overheat_warning',),
 'HIGH_COOLANT_TEMP':('engine.coolant_temp',),
 'BATTERY_LOW_REST':('electrical.battery_voltage',),
 'CRANK_VOLTAGE_LOW':('engine.starter_active','electrical.battery_voltage'),
 'STARTER_SLOW_CRANK':('engine.starter_active','engine.rpm'),
 'GLOW_CURRENT_LOW':('engine.glow_active','engine.glow_current'),
 'CHARGING_LOW':('engine.rpm','electrical.battery_voltage'),
 'CHARGING_OVERVOLTAGE':('engine.rpm','electrical.battery_voltage'),
 'CVT_RATIO_DRIFT':('engine.rpm','transmission.cvt_ratio_deviation'),
 'CVT_OVERHEAT':('engine.rpm','transmission.cvt_temp_primary','transmission.cvt_temp_secondary')}


class MGOBrainService:
    def __init__(self,data_dir:Path,*,source_adapter:SourceAdapter|None=None,
                 source_config_path:Path|None=None,signal_registry_path:Path|None=None):
        self.simulator=MGOSimulator(hz=5)
        self.source_config=self._load_runtime_config(source_config_path)
        factory=SourceFactory(simulator=self.simulator)
        register_standard_hardware_builders(factory)
        self.source=source_adapter or factory.build(self.source_config)
        self.simulator_active=_contains_source(self.source,'simulator')
        self.bench_controller=getattr(self.source,'controller',None)
        self.bench_active=self.bench_controller is not None
        self.data_origin='bench' if self.bench_active else 'simulator' if self.simulator_active else 'vehicle'
        # A synthetic baseline must not become the future vehicle's baseline.
        self.store=Store(Path(data_dir)/self.data_origin)
        self.aggregator=StateAggregator(stale_after_s=self.source_config.stale_after_s,
            preferred_sources=load_preferred_sources(signal_registry_path) if signal_registry_path else {})
        self.rules=RulesEngine()
        self.alerts=AlertManager(clear_after_s=1.0)
        self.health=HealthEngine()
        self.baselines=BaselineManager()
        self.analytics=HistoricalAnalytics(self.store.trip_dir)
        self.report_engine=PostTripReportEngine()
        self.start_detector=StartDetector()
        self.trip_detector=TripDetector(self.store.trip_dir)
        self.state=VehicleState()
        self._subscribers:set[asyncio.Queue]=set()
        self.task:asyncio.Task|None=None
        self._history_task:asyncio.Task|None=None
        self._history_queue:asyncio.Queue|None=None
        self._history_lock=RLock()
        self.runtime_errors:dict[str,str]={}
        self._last_update_mono:float|None=None
        self._start_baseline_eligible=True
        self._trip_baseline_eligible=True
        self._trip_worst_severity=Severity.INFO
        try:
            self.baselines.rebuild(self.store.list_starts(10000),self.store.list_trips(10000))
        except Exception as exc:
            self.runtime_errors['baseline_rebuild']=type(exc).__name__

    @staticmethod
    def _load_runtime_config(path:Path|None)->RuntimeSourceConfig:
        if path is not None:
            return load_source_config(path)  # Missing explicit configuration must fail closed.
        return RuntimeSourceConfig(stale_after_s=3.0,sources=(SourceEntry(type='simulator',enabled=True,options={}),))

    async def start(self):
        if self.task is not None:
            return
        self._history_queue=asyncio.Queue(maxsize=512)
        self._history_task=asyncio.create_task(self._history_worker(),name='mgo-history')
        self.task=asyncio.create_task(self._loop(),name='mgo-acquisition')

    async def stop(self):
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task,return_exceptions=True)
            self.task=None
        if self._history_task is not None:
            try:
                await asyncio.wait_for(self._history_queue.join(),timeout=5.0)
            except asyncio.TimeoutError:
                self.runtime_errors['history_shutdown']='timeout'
            self._history_task.cancel()
            await asyncio.gather(self._history_task,return_exceptions=True)
            self._history_task=None
        await self.source.close()
        # Preserve the partial JSONL; do not invent an engine-stop observation.
        if self.trip_detector.file is not None:
            self.trip_detector.file.close()
            self.trip_detector.file=None
            self.trip_detector.active=None

    def _clock_now(self):
        if self.bench_active:
            return self.bench_controller.wall_started+timedelta(seconds=self.bench_controller.virtual_elapsed())
        return datetime.now(timezone.utc)

    async def _loop(self):
        stream=self.source.stream()
        pending=asyncio.create_task(anext(stream))
        try:
            while True:
                done,_=await asyncio.wait({pending},timeout=0.25)
                if done:
                    try:
                        update=pending.result()
                    except StopAsyncIteration:
                        self.runtime_errors['source']='exhausted'
                        break
                    self._last_update_mono=time.monotonic()
                    state=self.aggregator.apply(update)
                    pending=asyncio.create_task(anext(stream))
                else:
                    # Age signals even when ALL sources stop publishing.
                    state=self.aggregator.snapshot(now=self._clock_now())
                self.process_state(state,background_history=True)
                await self._publish(state)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.runtime_errors['source']=type(exc).__name__
            LOG.exception('Acquisition failed')
        finally:
            pending.cancel()
            await asyncio.gather(pending,return_exceptions=True)
            await stream.aclose()
            if self.runtime_errors.get('source'):
                ts=max(self.state.timestamp,self._clock_now())+timedelta(seconds=self.source_config.stale_after_s+0.01)
                self.process_state(self.aggregator.snapshot(now=ts),background_history=True)
                await self._publish(self.state)

    def process_state(self,state:VehicleState,*,background_history:bool=False)->None:
        """Local rules always run before optional persistence/analytics."""
        self.state=state
        rule_events=self.rules.evaluate(state)
        unavailable={code for code,names in RULE_INPUTS.items() if any(state.value(n) is None for n in names)}
        transitions=self.alerts.update(rule_events,state.timestamp,unavailable_codes=unavailable)
        job=(state.model_copy(deep=True),rule_events,transitions)
        if background_history and self._history_queue is not None:
            try:
                self._history_queue.put_nowait(job)
            except asyncio.QueueFull:
                self.runtime_errors['history_backpressure']='samples_dropped'
        else:
            self._history_job(job)

    async def _history_worker(self):
        while True:
            job=await self._history_queue.get()
            try:
                await asyncio.to_thread(self._history_job,job)
            finally:
                self._history_queue.task_done()

    def _history_job(self,job):
        state,events,transitions=job
        with self._history_lock:
            for transition in transitions:
                record=transition.alert
                try:
                    self.store.add_event(Event(timestamp=state.timestamp,
                        severity=Severity.INFO if transition.transition==AlertStatus.CLEARED else record.severity,
                        code=f'ALERT_{transition.transition.value}:{record.code}',message=record.message,
                        data=record.model_dump(mode='json')))
                except Exception as exc:
                    self.runtime_errors['event_store']=type(exc).__name__
            try:
                self._record_history(state,events)
            except Exception as exc:
                self.runtime_errors['history']=type(exc).__name__
                LOG.exception('History failed; live diagnostics remain active')

    def _record_history(self,state,rule_events):
        if state.mode==VehicleMode.UNKNOWN:
            self._trip_baseline_eligible=False
            self._start_baseline_eligible=False
            return
        flagged=any(SEVERITY_RANK[e.severity]>=SEVERITY_RANK[Severity.WATCH] for e in rule_events)
        incomplete=any(not r.usable for name,r in state.signals.items() if name in ('engine.rpm','engine.coolant_temp','engine.oil_pressure','electrical.battery_voltage'))
        excluded=flagged or incomplete or bool(self.runtime_errors)
        start_was_active=self.start_detector.active is not None
        start_event=self.start_detector.update(state)
        start_is_active=self.start_detector.active is not None
        if not start_was_active and start_is_active:
            self._start_baseline_eligible=True
        if excluded and (start_was_active or start_is_active):
            self._start_baseline_eligible=False
        if start_event:
            start_event.baseline_eligible=self._start_baseline_eligible
            start_anomalies=self.baselines.start_anomalies(start_event)
            if any(a.get('status') in {'WATCH','ATTENTION'} for a in start_anomalies):
                start_event.baseline_eligible=False
            start_event.id=self.store.add_start(start_event)
            self.baselines.add_start_event(start_event)
            self.store.add_event(Event(timestamp=state.timestamp,severity=Severity.INFO,code='ENGINE_START',
                message='Engine start completed.',data={**start_event.model_dump(mode='json'),'historical_anomalies':start_anomalies}))
        trip_was_active=self.trip_detector.active is not None
        trip=self.trip_detector.update(state)
        trip_is_active=self.trip_detector.active is not None
        if not trip_was_active and trip_is_active:
            self._trip_baseline_eligible=True
            self._trip_worst_severity=Severity.INFO
        if trip_was_active or trip_is_active:
            for event in rule_events:
                if SEVERITY_RANK[event.severity]>SEVERITY_RANK[self._trip_worst_severity]:
                    self._trip_worst_severity=event.severity
            if excluded:
                self._trip_baseline_eligible=False
        if trip:
            trip.baseline_eligible=self._trip_baseline_eligible
            trip.diagnostic_status=self._trip_worst_severity.value if self._trip_worst_severity!=Severity.INFO else 'NORMAL'
            try:
                trip.telemetry_path=self.analytics.finalize_trip(trip.telemetry_path)
            except Exception as exc:
                self.runtime_errors['parquet']=type(exc).__name__
                trip.baseline_eligible=False
            anomalies=self.baselines.trip_anomalies(trip)
            if any(a.get('status') in {'WATCH','ATTENTION'} for a in anomalies):
                trip.baseline_eligible=False
            trip.id=self.store.add_trip(trip)
            self.store.add_report(self.report_engine.generate(trip,anomalies,trip.baseline_eligible))
            self.baselines.add_trip(trip)
            self.store.add_event(Event(timestamp=state.timestamp,severity=Severity.INFO,code='TRIP_COMPLETE',
                message='Trip completed.',data=trip.model_dump(mode='json')))

    async def _publish(self,state:VehicleState):
        payload=state.model_dump(mode='json')
        for q in tuple(self._subscribers):
            if q.full():
                q.get_nowait()
            q.put_nowait(payload)

    def subscribe(self)->asyncio.Queue:
        q=asyncio.Queue(maxsize=2)
        self._subscribers.add(q)
        return q

    def unsubscribe(self,q):
        self._subscribers.discard(q)

    def health_summary(self):
        active=self.alerts.active()
        summary=self.health.summary(self.state,active)
        if self.runtime_errors and summary['overall'] not in {'CRITICAL','ATTENTION'}:
            summary['overall']='ATTENTION'
        summary.update(mode=self.state.mode,active_alerts=[a.model_dump(mode='json') for a in active],
                       baseline=self.baselines.summary(),simulator_faults=self.simulator.faults.names() if self.simulator_active else [],
                       runtime_errors=dict(self.runtime_errors),data_origin=self.data_origin)
        return summary

    def readiness(self):
        age=None if self._last_update_mono is None else time.monotonic()-self._last_update_mono
        acquisition=bool(self.task and not self.task.done() and age is not None and age<=self.source_config.stale_after_s)
        return {'ready':acquisition and not self.runtime_errors,'acquisition_live':acquisition,
                'last_update_age_s':age,'runtime_errors':dict(self.runtime_errors),'data_origin':self.data_origin}

    def ai_context(self)->AIContext:
        trips=self.store.list_trips(1)
        return AIContext(current_state=self.state,
            active_alerts=[Event(timestamp=a.last_seen,severity=a.severity,code=a.code,message=a.message,data=a.data) for a in self.alerts.active()],
            recent_trip=TripSummary.model_validate(trips[0]) if trips else None,
            baseline_deviations=[{'metric':name,**metric.stats()} for name,metric in self.baselines.metrics.items()],maintenance_due=[])

    def source_status(self):
        return {'adapter':self.source.name,'stale_after_s':self.source_config.stale_after_s,
                'sources':[{'type':x.type,'enabled':x.enabled} for x in self.source_config.sources],
                'simulator_active':self.simulator_active,'bench_active':self.bench_active,'data_origin':self.data_origin,
                'bench':self.bench_status() if self.bench_active else None,'readiness':self.readiness(),
                'source_errors':dict(getattr(self.source,'errors',{}))}

    def bench_status(self):
        return self.bench_controller.status() if self.bench_active else {'active':False}

    def set_bench_scenario(self,scenario):
        if not self.bench_active:
            raise RuntimeError('Bench source is not active')
        self.bench_controller.set_scenario(scenario)
        return self.bench_status()

    def reset_bench(self):
        if not self.bench_active:
            raise RuntimeError('Bench source is not active')
        self.bench_controller.reset()
        return self.bench_status()

    def alert_snapshot(self):
        return self.alerts.snapshot()

    def fault_catalog(self):
        return self.simulator.faults.catalog() if self.simulator_active else []

    def enable_fault(self,fault:FaultScenario|str):
        if not self.simulator_active:
            raise RuntimeError('Simulator source is not active')
        self.simulator.faults.enable(fault)
        return self.fault_catalog()

    def disable_fault(self,fault:FaultScenario|str):
        if not self.simulator_active:
            raise RuntimeError('Simulator source is not active')
        self.simulator.faults.disable(fault)
        return self.fault_catalog()

    def clear_faults(self):
        if not self.simulator_active:
            return []
        self.simulator.faults.clear()
        return self.fault_catalog()

    def analytics_summary(self):
        return self.analytics.summary()

    def compare_trips(self,trip_a:int,trip_b:int)->dict[str,Any]|None:
        a=self.store.get_trip(trip_a)
        b=self.store.get_trip(trip_b)
        if not a or not b:
            return None
        metrics=('distance_km','duration_s','avg_speed_kmh','max_speed_kmh','max_coolant_c','max_oil_temp_c',
                 'min_oil_pressure_bar','avg_running_voltage_v','avg_cvt_ratio_deviation_pct','max_cvt_temp_c')
        comparison={}
        for name in metrics:
            av,bv=a.get(name),b.get(name)
            delta=None if av is None or bv is None else bv-av
            pct=delta/abs(av)*100.0 if delta is not None and abs(av)>1e-12 else None
            comparison[name]={'a':av,'b':bv,'delta':delta,'delta_pct':pct}
        return {'trip_a':a,'trip_b':b,'comparison':comparison}


def _contains_source(source,name):
    return getattr(source,'name',None)==name or any(_contains_source(a,name) for a in getattr(source,'adapters',[]) or [])
