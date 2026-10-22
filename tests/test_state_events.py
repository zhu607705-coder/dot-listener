import base64
import hashlib
import hmac
import pytest
from dot_listener.state import CaptureState, Mode, SleepWindow
from dot_listener.events import sign_headers, serialize_event, validate_callback_shape, signing_key

def test_start_requires_consent():
    with pytest.raises(ValueError): CaptureState().apply('start',True)

def test_no_background_start():
    with pytest.raises(ValueError): CaptureState(consent=True,microphone_granted=True).apply('start')

def test_sleep_releases_and_wake_does_not_record():
    s=CaptureState(consent=True,microphone_granted=True)
    s.apply('start',True);assert s.microphone_open
    s.apply('sleep');assert not s.microphone_open
    with pytest.raises(ValueError): s.apply('start',True)
    s.apply('wake',True);assert s.mode==Mode.IDLE and not s.microphone_open

def test_pause_cannot_escape_sleep():
    s=CaptureState(mode=Mode.SLEEP);s.apply('pause');assert s.mode==Mode.SLEEP

def test_interrupt_and_revoke():
    s=CaptureState(consent=True,microphone_granted=True)
    s.apply('start',True);s.apply('interrupt')
    assert not s.microphone_open and s.interruption_count==1
    s.apply('revoke');assert not s.microphone_granted

@pytest.mark.parametrize('start,end,minute,expected',[
    (1380,420,1390,True),(1380,420,30,True),(1380,420,420,False),
    (1380,420,800,False),(60,300,60,True),(60,300,299,True),(60,300,300,False)])
def test_sleep_windows(start,end,minute,expected):
    assert SleepWindow(start,end).contains(minute)==expected

def test_ambiguous_window_rejected():
    with pytest.raises(ValueError): SleepWindow(0,0)

def test_signed_body_exact_bytes():
    secret='whsec_'+base64.b64encode(b'a'*32).decode();body='{"text":"你好"}'.encode()
    headers=sign_headers('evt_1','sub_1',body,secret,1700000000)
    expected=base64.b64encode(hmac.new(b'a'*32,b'evt_1.1700000000.'+body,hashlib.sha256).digest()).decode()
    assert headers['webhook-signature']=='v1,'+expected
    assert sign_headers('evt_1','sub_1',body,secret,1700000001)!=headers

@pytest.mark.parametrize('secret',['plain','whsec_bad!', 'whsec_'+base64.b64encode(b'x'*4).decode()])
def test_bad_secrets(secret):
    with pytest.raises(ValueError): signing_key(secret)

@pytest.mark.parametrize('url',[
    'http://allowed.example/callback','https://user@allowed.example/callback',
    'https://allowed.example:444/callback','https://elsewhere.example/callback',
    'https://127.0.0.1/callback','https://169.254.169.254/callback'])
def test_callback_shape_deny(url):
    with pytest.raises(ValueError): validate_callback_shape(url,{'allowed.example','127.0.0.1','169.254.169.254'})

def test_callback_shape_only():
    assert validate_callback_shape('https://allowed.example/callback',{'allowed.example'})=='allowed.example'

def test_event_size_and_envelope():
    e={'eventId':'e1','name':'transcript.ready','timestamp':'2026-10-21T01:00:00Z','data':{'id':'f1'},'cursor':None}
    assert b'"eventId"' in serialize_event(e)
    e['data']['text']='x'*262144
    with pytest.raises(ValueError):serialize_event(e)
    with pytest.raises(ValueError):serialize_event({'data':{}})
