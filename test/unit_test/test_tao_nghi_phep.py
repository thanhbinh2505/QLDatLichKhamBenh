import pytest
from datetime import date, timedelta, time
import json
from app import dao
from app.models import BacSi, User, UserRole, TrangThaiDuyet, NgayNghiBacSi, PhanCa, CaLam, LichLamViec, NgayLamViec, TrangThaiBacSi
from .test_base import test_session, test_app, test_client

@pytest.fixture
def setup_bacsi(test_session):
    u = User(username='bs_test_nghi', hoTen='BS Nghi', email='bs_nghi@test.com', gioiTinh=True, role=UserRole.BACSI, password='123')
    test_session.add(u)
    test_session.flush()
    bs = BacSi(user_id=u.id, chuyenKhoa='Nội Khoa')
    test_session.add(bs)
    test_session.commit()
    return bs

def test_tao_nghi_phep_bac_si_da_co_lich_nghi_phep(test_session, setup_bacsi):
    today = date.today()
    ngay_nghi = NgayNghiBacSi(
        bacsi_id=setup_bacsi.id,
        ngayBatDau=today,
        ngayKetThuc=today + timedelta(days=2),
        trangThai=TrangThaiDuyet.DaDuyet
    )
    test_session.add(ngay_nghi)
    test_session.commit()

    success, msg = dao.tao_nghi_phep_bac_si(setup_bacsi.id, today, today + timedelta(days=1), "Nghỉ ốm")
    assert success is False
    assert msg == "Bác sĩ đã có lịch nghỉ phép hoặc đang chờ duyệt trong khoảng thời gian này."

def test_tao_nghi_phep_bac_si_da_co_lich_nghi_phep_cho_duyet(test_session, setup_bacsi):
    today = date.today()
    ngay_nghi = NgayNghiBacSi(
        bacsi_id=setup_bacsi.id,
        ngayBatDau=today,
        ngayKetThuc=today + timedelta(days=2),
        trangThai=TrangThaiDuyet.ChoDuyet
    )
    test_session.add(ngay_nghi)
    test_session.commit()

    success, msg = dao.tao_nghi_phep_bac_si(setup_bacsi.id, today + timedelta(days=1), today + timedelta(days=3), "Nghỉ ốm")
    assert success is False
    assert msg == "Bác sĩ đã có lịch nghỉ phép hoặc đang chờ duyệt trong khoảng thời gian này."

def test_tao_nghi_phep_bac_si_thanh_cong_khong_co_phan_ca(test_session, setup_bacsi):
    today = date.today()
    success, msg = dao.tao_nghi_phep_bac_si(setup_bacsi.id, today, today, "Việc bận")
    
    assert success is True
    assert msg == "Tạo nghỉ phép thành công."
    
    nghi_phep_db = NgayNghiBacSi.query.filter_by(bacsi_id=setup_bacsi.id, ngayBatDau=today).first()
    assert nghi_phep_db is not None
    assert nghi_phep_db.trangThai == TrangThaiDuyet.DaDuyet
    assert nghi_phep_db.lyDo == "Việc bận"

def test_tao_nghi_phep_bac_si_thanh_cong_co_phan_ca(test_session, setup_bacsi):
    today = date.today()
    ca = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    test_session.add(ca)
    test_session.flush()

    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=today)
    test_session.add(lich)
    test_session.flush()

    nlv = NgayLamViec(ngay=today, id_LichLamViec=lich.id)
    test_session.add(nlv)
    test_session.flush()

    pc = PhanCa(id_BacSi=setup_bacsi.id, thuocNgay=today, id_CaLam=ca.id, trangThai=TrangThaiBacSi.HoatDong)
    test_session.add(pc)
    test_session.commit()

    success, msg = dao.tao_nghi_phep_bac_si(setup_bacsi.id, today, today, "Việc bận")
    
    assert success is True
    assert msg == "Tạo nghỉ phép thành công."
    
    nghi_phep_db = NgayNghiBacSi.query.filter_by(bacsi_id=setup_bacsi.id, ngayBatDau=today).first()
    assert nghi_phep_db is not None
    assert nghi_phep_db.trangThai == TrangThaiDuyet.DaDuyet

    pc_db = PhanCa.query.filter_by(id_BacSi=setup_bacsi.id, thuocNgay=today).first()
    assert pc_db is not None
    assert pc_db.trangThai == TrangThaiBacSi.NghiPhep


@pytest.fixture
def admin_login(test_app, test_client, mocker):
    class FakeAdmin:
        is_authenticated = True
        id = 1
        role = UserRole.ADMIN

    mocker.patch('flask_login.utils._get_user', return_value=FakeAdmin())
    return test_client

def _valid_nghi_phep_payload(**overrides):
    today = date.today()
    payload = {
        'bacsi_id': 1,
        'ngayBatDau': today.strftime('%Y-%m-%d'),
        'ngayKetThuc': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
        'lyDo': 'Lý do hợp lệ'
    }
    payload.update(overrides)
    return payload

@pytest.mark.parametrize('bacsi_id, err_msg', [
    (None, 'Vui lòng cung cấp ID bác sĩ.'),
    ('abc', 'Not a valid integer.')
])
def test_api_tao_nghi_phep_bacsi_id_invalid(admin_login, bacsi_id, err_msg, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si')
    payload = _valid_nghi_phep_payload()
    if bacsi_id is None:
        del payload['bacsi_id']
    else:
        payload['bacsi_id'] = bacsi_id

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'errors' in data
    assert err_msg in str(data['errors'])
    mock_tao_nghi_phep.assert_not_called()

yesterday = date.today() - timedelta(days=1)
@pytest.mark.parametrize('ngayBatDau, err_msg', [
    (None, 'Vui lòng nhập ngày bắt đầu.'),
    ('invalid-date', 'Ngày bắt đầu không đúng định dạng (YYYY-MM-DD).'),
    (yesterday.strftime('%Y-%m-%d'), 'Không thể tạo ngày nghỉ phép trong quá khứ.')
])
def test_api_tao_nghi_phep_ngayBatDau_invalid(admin_login, ngayBatDau, err_msg, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si')
    payload = _valid_nghi_phep_payload()
    if ngayBatDau is None:
        del payload['ngayBatDau']
    else:
        payload['ngayBatDau'] = ngayBatDau

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'errors' in data
    assert err_msg in str(data['errors'])
    mock_tao_nghi_phep.assert_not_called()

@pytest.mark.parametrize('ngayKetThuc, err_msg', [
    (None, 'Vui lòng nhập ngày kết thúc.'),
    ('invalid-date', 'Ngày kết thúc không đúng định dạng (YYYY-MM-DD).')
])
def test_api_tao_nghi_phep_ngayKetThuc_invalid(admin_login, ngayKetThuc, err_msg, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si')
    payload = _valid_nghi_phep_payload()
    if ngayKetThuc is None:
        del payload['ngayKetThuc']
    else:
        payload['ngayKetThuc'] = ngayKetThuc

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'errors' in data
    assert err_msg in str(data['errors'])
    mock_tao_nghi_phep.assert_not_called()

def test_api_tao_nghi_phep_ngayKetThuc_truoc_ngayBatDau(admin_login, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si')
    today = date.today()
    payload = _valid_nghi_phep_payload(
        ngayBatDau=(today + timedelta(days=2)).strftime('%Y-%m-%d'),
        ngayKetThuc=today.strftime('%Y-%m-%d')
    )

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'errors' in data
    assert 'Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.' in str(data['errors'])
    mock_tao_nghi_phep.assert_not_called()

def test_api_tao_nghi_phep_lyDo_invalid(admin_login, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si')
    payload = _valid_nghi_phep_payload(lyDo='A' * 256)

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'errors' in data
    assert 'Longer than maximum length 255.' in str(data['errors'])
    mock_tao_nghi_phep.assert_not_called()

def test_api_tao_nghi_phep_success(admin_login, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si', return_value=(True, 'Tạo nghỉ phép thành công.'))
    payload = _valid_nghi_phep_payload()

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['message'] == 'Tạo nghỉ phép thành công.'
    mock_tao_nghi_phep.assert_called_once()

def test_api_tao_nghi_phep_that_bai(admin_login, mocker):
    mock_tao_nghi_phep = mocker.patch('app.dao.tao_nghi_phep_bac_si', return_value=(False, 'Bác sĩ đã có lịch nghỉ phép.'))
    payload = _valid_nghi_phep_payload()

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == 'Bác sĩ đã có lịch nghỉ phép.'
    mock_tao_nghi_phep.assert_called_once()

# ==========================================
# INTERGRATION TESTS
# ==========================================

def test_integration_tao_nghi_phep_chua_dang_nhap(test_app, test_client):
    payload = _valid_nghi_phep_payload()
    res = test_client.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 401

def test_integration_tao_nghi_phep_khong_phai_admin(test_client, mocker):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    
    payload = _valid_nghi_phep_payload()
    res = test_client.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 403

def test_integration_tao_nghi_phep_thanh_cong(admin_login, test_session, setup_bacsi):
    today = date.today()
    payload = {
        'bacsi_id': setup_bacsi.id,
        'ngayBatDau': today.strftime('%Y-%m-%d'),
        'ngayKetThuc': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
        'lyDo': 'Lý do xin nghỉ ốm'
    }

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['message'] == 'Tạo nghỉ phép thành công.'

    nghi_phep_db = NgayNghiBacSi.query.filter_by(bacsi_id=setup_bacsi.id, ngayBatDau=today).first()
    assert nghi_phep_db is not None
    assert nghi_phep_db.trangThai == TrangThaiDuyet.DaDuyet
    assert nghi_phep_db.lyDo == 'Lý do xin nghỉ ốm'

def test_integration_tao_nghi_phep_trung_lich(admin_login, test_session, setup_bacsi):
    today = date.today()
    
    ngay_nghi = NgayNghiBacSi(
        bacsi_id=setup_bacsi.id,
        ngayBatDau=today,
        ngayKetThuc=today + timedelta(days=2),
        trangThai=TrangThaiDuyet.DaDuyet
    )
    test_session.add(ngay_nghi)
    test_session.commit()

    payload = {
        'bacsi_id': setup_bacsi.id,
        'ngayBatDau': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
        'ngayKetThuc': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
        'lyDo': 'Lý do khác'
    }

    res = admin_login.post(
        '/api/admin/tao-nghi-phep',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == 'Bác sĩ đã có lịch nghỉ phép hoặc đang chờ duyệt trong khoảng thời gian này.'

