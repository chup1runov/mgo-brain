import json
from types import SimpleNamespace
import pytest
from mgo_brain.sources.can import verify_listen_only


@pytest.mark.parametrize('mode', [[], {'listen-only':False}, ['NOT-LISTEN-ONLY'], 'LISTEN-ONLY'])
def test_mode_must_be_explicitly_enabled(monkeypatch, mode):
    data=[{'flags':['UP'],'linkinfo':{'info_kind':'can','info_data':{'ctrlmode':mode}}}]
    monkeypatch.setattr('mgo_brain.sources.can.subprocess.run',lambda *a,**kw:SimpleNamespace(stdout=json.dumps(data)))
    with pytest.raises(RuntimeError):
        verify_listen_only('can0')


@pytest.mark.parametrize('mode', [['LISTEN-ONLY'], {'listen-only':True}])
def test_verified_mode_is_accepted_without_changing_link(monkeypatch, mode):
    calls=[]
    data=[{'flags':['UP'],'linkinfo':{'info_kind':'can','info_data':{'ctrlmode':mode}}}]
    def run(command,**kw):
        calls.append(command)
        return SimpleNamespace(stdout=json.dumps(data))
    monkeypatch.setattr('mgo_brain.sources.can.subprocess.run',run)
    verify_listen_only('can0')
    assert calls==[['ip','-details','-json','link','show','dev','can0']]
