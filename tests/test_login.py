import sys
from pathlib import Path
import types
import pytest

# Insert path to the login backend so we can import app.py
backend_path = Path(__file__).resolve().parents[1] / 'se-backend' / 'login'
sys.path.insert(0, str(backend_path))

# Provide stub of flask_mailman so that app.py can be imported without dependency
flask_mailman = types.ModuleType('flask_mailman')
class DummyConnection:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def send_messages(self, messages):
        pass
class DummyMail:
    def __init__(self, app=None):
        pass
    def get_connection(self):
        return DummyConnection()
class DummyEmailMessage:
    def __init__(self, *args, **kwargs):
        pass
flask_mailman.Mail = DummyMail
flask_mailman.EmailMessage = DummyEmailMessage
sys.modules['flask_mailman'] = flask_mailman

# Import the Flask app after stubbing dependencies
import app as app_module
app = app_module.app

# Dummy in-memory user store used by stubbed db functions
user_store = {}

def stub_register_user(useremail, username, password, role):
    if useremail in user_store:
        return False, '该邮箱已被注册'
    user_store[useremail] = {'username': username, 'password': password, 'role': role}
    return True, '注册成功'

def stub_login_user(useremail, password, role):
    user = user_store.get(useremail)
    if not user or user['role'] != role:
        return False, '用户不存在', None
    if user['password'] != password:
        return False, '密码错误', None
    return True, '登录成功', {
        'token': 'fake-token',
        'expire_at': 0,
        'username': user['username'],
        'role': role,
    }

class DummyDB:
    def close(self):
        pass

def dummy_get_db_connection():
    return DummyDB()

@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    # Patch db functions and connection for each test
    monkeypatch.setattr(app_module, 'register_user', stub_register_user)
    monkeypatch.setattr(app_module, 'login_user', stub_login_user)
    monkeypatch.setattr(app_module, 'get_db_connection', dummy_get_db_connection)
    user_store.clear()
    yield

@pytest.fixture
def client():
    return app.test_client()

def test_register_success(client):
    resp = client.post('/api/register', json={
        'useremail': 'alice@qq.com',
        'username': 'Alice',
        'password': 'pass',
        'role': 'student'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'

def test_register_missing_field(client):
    resp = client.post('/api/register', json={
        'useremail': 'bob@qq.com',
        'password': 'pass',
        'role': 'student'
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['status'] == 'error'

def test_register_invalid_domain(client):
    resp = client.post('/api/register', json={
        'useremail': 'eve@invalid.com',
        'username': 'Eve',
        'password': 'pass',
        'role': 'student'
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['status'] == 'error'


def test_login_success(client):
    # first register user
    client.post('/api/register', json={
        'useremail': 'charlie@qq.com',
        'username': 'Charlie',
        'password': 'secret',
        'role': 'student'
    })
    resp = client.post('/api/login', json={
        'useremail': 'charlie@qq.com',
        'password': 'secret',
        'role': 'student'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert data['data']['username'] == 'Charlie'

def test_login_wrong_password(client):
    client.post('/api/register', json={
        'useremail': 'dave@qq.com',
        'username': 'Dave',
        'password': 'right',
        'role': 'student'
    })
    resp = client.post('/api/login', json={
        'useremail': 'dave@qq.com',
        'password': 'wrong',
        'role': 'student'
    })
    assert resp.status_code == 401
    data = resp.get_json()
    assert data['status'] == 'error'
