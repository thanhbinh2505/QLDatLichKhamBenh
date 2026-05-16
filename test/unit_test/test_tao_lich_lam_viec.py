import pytest
from datetime import date, timedelta, time, datetime
from app import dao
from app.models import LichLamViec, NgayLamViec, PhanCa, BacSi, CaLam, User, UserRole, TrangThaiBacSi, NgayNghiBacSi, TrangThaiDuyet, BenhNhan
from .test_base import test_session, test_app, test_client
from unittest.mock import MagicMock, call


# ==========================================
# TEST: get_ngay_chua_sap_lich_gan_nhat
# ==========================================
def test_get_ngay_chua_sap_lich_gan_nhat_no_lich(test_session):
    today = date.today()
    result = dao.get_ngay_chua_sap_lich_gan_nhat()
    assert result == today

def test_get_ngay_chua_sap_lich_gan_nhat_past_lich(test_session):
    today = date.today()
    past_date = today - timedelta(days=10)
    lich = LichLamViec(ngayBatDau=past_date - timedelta(days=5), ngayKetThuc=past_date)
    test_session.add(lich)
    test_session.commit()
    
    result = dao.get_ngay_chua_sap_lich_gan_nhat()
    assert result == today

def test_get_ngay_chua_sap_lich_gan_nhat_future_lich(test_session):
    today = date.today()
    future_date = today + timedelta(days=5)
    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=future_date)
    test_session.add(lich)
    test_session.commit()
    
    result = dao.get_ngay_chua_sap_lich_gan_nhat()
    assert result == future_date + timedelta(days=1)

# ==========================================
# TEST: lay_ngay_lam_viec
# ==========================================
def test_lay_ngay_lam_viec(test_session):
    today = date.today()
    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=today + timedelta(days=2))
    test_session.add(lich)
    test_session.flush()

    nlv1 = NgayLamViec(ngay=today, id_LichLamViec=lich.id)
    nlv2 = NgayLamViec(ngay=today + timedelta(days=1), id_LichLamViec=lich.id)
    nlv3 = NgayLamViec(ngay=today + timedelta(days=2), id_LichLamViec=lich.id)
    test_session.add_all([nlv1, nlv2, nlv3])
    test_session.commit()

    result = dao.lay_ngay_lam_viec(today, today + timedelta(days=1))
    assert len(result) == 2
    assert result[0].ngay == today
    assert result[1].ngay == today + timedelta(days=1)

    result = dao.lay_ngay_lam_viec(date.today() - timedelta(days=3), date.today() - timedelta(days=1))
    assert len(result) == 0

# ==========================================
# TEST: lay_danh_sach_phan_ca
# ==========================================
def test_lay_danh_sach_phan_ca_khong_ton_tai(test_session):
    result = dao.lay_danh_sach_phan_ca(date.today())
    assert result == []

def test_lay_danh_sach_phan_ca_thanh_cong(test_session):
    today = date.today()
    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=today)
    test_session.add(lich)
    test_session.flush()

    nlv = NgayLamViec(ngay=today, id_LichLamViec=lich.id)
    test_session.add(nlv)
    test_session.flush()

    u = User(username='bs_test', hoTen='BS Test', email='bs@test.com', gioiTinh=True, role=UserRole.BACSI, password='123')
    test_session.add(u)
    test_session.flush()
    bs = BacSi(user_id=u.id, chuyenKhoa='Nhi Khoa')
    test_session.add(bs)
    
    ca = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    test_session.add(ca)
    test_session.flush()

    pc = PhanCa(id_BacSi=bs.id, thuocNgay=nlv.ngay, id_CaLam=ca.id)
    test_session.add(pc)
    test_session.commit()

    result = dao.lay_danh_sach_phan_ca(today)
    assert len(result) == 1
    assert result[0].id_BacSi == bs.id
    assert result[0].id_CaLam == ca.id

# ==========================================
# TEST: lay_lich_tuan
# ==========================================
@pytest.fixture
def setup_lich(test_session):
    ca_lam = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    test_session.add(ca_lam)
    test_session.flush()

    start = date.today() - timedelta(days=7)
    end = start + timedelta(days=14)
    lich = LichLamViec(ngayBatDau=start, ngayKetThuc=end)
    test_session.add(lich)
    test_session.flush()
    
    for i in range(14):
        ngay = start + timedelta(days=i)
        nlv = NgayLamViec(ngay=ngay, id_LichLamViec=lich.id)
        test_session.add(nlv)

    u = User(username='bs_test', hoTen='BS Test', email='bs@test.com', gioiTinh=True, role=UserRole.BACSI, password='123')
    test_session.add(u)
    test_session.flush()
    bs = BacSi(user_id=u.id, chuyenKhoa='Nhi Khoa')
    test_session.add(bs)
    test_session.commit()

    for i in range(14):
        ngay = start + timedelta(days=i)
        pc = PhanCa(id_BacSi=bs.id, thuocNgay=ngay, id_CaLam=ca_lam.id)
        test_session.add(pc)
    
    test_session.commit()
    return {
        "start": start,
        "end": end,
        "bs": bs,
        "ca_lam": ca_lam,
        "pc": pc,
        "lich": lich,
        "nlv": nlv
    }

def test_lay_lich_tuan_thanh_cong(test_session, setup_lich):
    today = date.today().weekday()
    mon_day = date.today() - timedelta(days=today)
    sun_day = mon_day + timedelta(days=6)
    
    lich = dao.lay_lich_tuan(mon_day, sun_day)
    assert len(lich) == 7
    day_map = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}
    for i in range(7):
        assert day_map[i] in lich
        assert lich[day_map[i]][setup_lich["ca_lam"].id] == [setup_lich["bs"].id]

def test_lay_lich_tuan_khong_ton_tai(test_session):
    result = dao.lay_lich_tuan(date.today(), date.today() + timedelta(days=7))
    assert result == {}

# ==========================================
# TEST: tao_lich_lam_viec
# ==========================================
def test_tao_lich_lam_viec_trung_lich(test_session):
    start = date.today()
    end = start + timedelta(days=5)
    lich_cu = LichLamViec(ngayBatDau=start, ngayKetThuc=end)
    test_session.add(lich_cu)
    test_session.commit()
    success, _ = dao.tao_lich_lam_viec(start, end)
    assert success is False

    success, _ = dao.tao_lich_lam_viec(start - timedelta(days=1), start + timedelta(days=2))
    assert success is False
    
    success, _ = dao.tao_lich_lam_viec(start + timedelta(days=2), start + timedelta(days=7))
    assert success is False

def test_tao_lich_lam_viec_thanh_cong(test_session):
    start = date.today()
    end = start + timedelta(days=5)
    success, lich_moi = dao.tao_lich_lam_viec(start, end)
    test_session.commit()

    assert success is True
    assert lich_moi is not None
    assert lich_moi.ngayBatDau == start
    assert lich_moi.ngayKetThuc == end

# ==========================================
# TEST: tao_ngay_lam_viec
# ==========================================
def test_tao_ngay_lam_viec_thanh_cong(test_session):
    today = date.today()
    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=today)
    test_session.add(lich)
    test_session.flush()

    success, ngay_moi = dao.tao_ngay_lam_viec(today, lich.id)
    test_session.commit()

    assert success is True
    assert ngay_moi is not None
    assert ngay_moi.ngay == today
    assert ngay_moi.id_LichLamViec == lich.id

def test_tao_ngay_lam_viec_out_of_range(test_session):
    today = date.today()
    lich = LichLamViec(ngayBatDau=today, ngayKetThuc=today + timedelta(days=2))
    test_session.add(lich)
    test_session.flush()
    success, _ = dao.tao_ngay_lam_viec(today - timedelta(days=1), lich.id)
    assert success is False
    
    success, _ = dao.tao_ngay_lam_viec(today + timedelta(days=3), lich.id)
    assert success is False

def test_tao_ngay_lam_viec_lich_khong_ton_tai(test_session):
    success, _ = dao.tao_ngay_lam_viec(date.today(), 999)
    assert success is False

# ==========================================
# TEST: tao_phan_ca
# ==========================================
@pytest.fixture
def setup_phan_ca(test_session):
    u = User(username='bs_test2', hoTen='BS Test 2', email='bs2@test.com', gioiTinh=True, role=UserRole.BACSI, password='123')
    test_session.add(u)
    test_session.flush()
    bs = BacSi(user_id=u.id, chuyenKhoa='Nhi Khoa')
    test_session.add(bs)

    ca = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    test_session.add(ca)

    lich = LichLamViec(ngayBatDau=date.today(), ngayKetThuc=date.today())
    test_session.add(lich)
    test_session.flush()

    nlv = NgayLamViec(ngay=date.today(), id_LichLamViec=lich.id)
    test_session.add(nlv)
    test_session.commit()

    return {
        'bs_id': bs.id,
        'ca_id': ca.id,
        'ngay': nlv.ngay
    }

def test_tao_phan_ca_bac_si_khong_ton_tai(test_session, setup_phan_ca):
    success, _ = dao.tao_phan_ca(999, setup_phan_ca['ca_id'], setup_phan_ca['ngay'])
    assert success is False

def test_tao_phan_ca_ca_lam_khong_ton_tai(test_session, setup_phan_ca):
    success, _ = dao.tao_phan_ca(setup_phan_ca['bs_id'], 999, setup_phan_ca['ngay'])
    assert success is False

def test_tao_phan_ca_ngay_lam_viec_khong_ton_tai(test_session, setup_phan_ca):
    success, _ = dao.tao_phan_ca(setup_phan_ca['bs_id'], setup_phan_ca['ca_id'], setup_phan_ca['ngay'] - timedelta(days=1))
    assert success is False

def test_tao_phan_ca_da_ton_tai(test_session, setup_phan_ca):
    pc = PhanCa(id_BacSi=setup_phan_ca['bs_id'], thuocNgay=setup_phan_ca['ngay'], id_CaLam=setup_phan_ca['ca_id'])
    test_session.add(pc)
    test_session.commit()

    success, _ = dao.tao_phan_ca(setup_phan_ca['bs_id'], setup_phan_ca['ca_id'], setup_phan_ca['ngay'])
    assert success is False

def test_tao_phan_ca_thanh_cong_khong_trung_ngay_nghi_phep(test_session, setup_phan_ca):
    success, pc_moi = dao.tao_phan_ca(setup_phan_ca['bs_id'], setup_phan_ca['ca_id'], setup_phan_ca['ngay'])
    assert success is True
    assert pc_moi is not None
    assert pc_moi.id_BacSi == setup_phan_ca['bs_id']
    assert pc_moi.id_CaLam == setup_phan_ca['ca_id']
    assert pc_moi.thuocNgay == setup_phan_ca['ngay']
    assert pc_moi.trangThai == TrangThaiBacSi.HoatDong

def test_tao_phan_ca_thanh_cong_trung_ngay_nghi_phep(test_session, setup_phan_ca):
    ngay_nghi = NgayNghiBacSi(
        bacsi_id=setup_phan_ca['bs_id'],
        ngayBatDau=setup_phan_ca['ngay'],
        ngayKetThuc=setup_phan_ca['ngay'],
        trangThai=TrangThaiDuyet.DaDuyet
    )
    test_session.add(ngay_nghi)
    test_session.commit()

    success, pc_moi = dao.tao_phan_ca(setup_phan_ca['bs_id'], setup_phan_ca['ca_id'], setup_phan_ca['ngay'])
    assert success is True
    assert pc_moi is not None
    assert pc_moi.id_BacSi == setup_phan_ca['bs_id']
    assert pc_moi.id_CaLam == setup_phan_ca['ca_id']
    assert pc_moi.thuocNgay == setup_phan_ca['ngay']
    assert pc_moi.trangThai == TrangThaiBacSi.NghiPhep

# ==========================================
# TEST: tao_lich
# ==========================================

def test_tao_lich_tao_lich_lam_viec_that_bai(mocker):
    mocker.patch('app.dao.tao_lich_lam_viec', return_value=(False, "Lỗi tạo lịch làm việc"))
    mock_tao_ngay = mocker.patch('app.dao.tao_ngay_lam_viec')
    
    success, msg = dao.tao_lich({}, date(2026, 5, 10), date(2026, 5, 12))
    assert success is False
    assert msg == "Lỗi tạo lịch làm việc"
    mock_tao_ngay.assert_not_called()

def test_tao_lich_tao_ngay_lam_viec_that_bai(mocker):
    lich_moi_mock = MagicMock()
    lich_moi_mock.id = 1
    mocker.patch('app.dao.tao_lich_lam_viec', return_value=(True, lich_moi_mock))
    mocker.patch('app.dao.tao_ngay_lam_viec', return_value=(False, "Lỗi tạo ngày làm việc"))
    mock_tao_phan_ca = mocker.patch('app.dao.tao_phan_ca')

    lich_tuan = {'CN': {'ca1': [1, 2]}}
    
    success, msg = dao.tao_lich(lich_tuan, date.today(), date.today() + timedelta(days=7))
    assert success is False
    assert msg == "Lỗi tạo ngày làm việc"
    mock_tao_phan_ca.assert_not_called()

def test_tao_lich_tao_phan_ca_that_bai(mocker):
    lich_moi_mock = MagicMock()
    lich_moi_mock.id = 1
    mocker.patch('app.dao.tao_lich_lam_viec', return_value=(True, lich_moi_mock))
    
    ngay_moi_mock = MagicMock()
    ngay_moi_mock.ngay = date.today()
    mocker.patch('app.dao.tao_ngay_lam_viec', return_value=(True, ngay_moi_mock))
    
    mocker.patch('app.dao.tao_phan_ca', return_value=(False, "Lỗi tạo phân ca"))
    mock_commit = mocker.patch('app.dao.commit')

    lich_tuan = {'CN': {'ca1': [1]}}
    
    success, msg = dao.tao_lich(lich_tuan, date.today(), date.today() + timedelta(days=7))
    assert success is False
    assert msg == "Lỗi tạo phân ca"
    mock_commit.assert_not_called()

def test_tao_lich_thanh_cong(mocker):
    lich_moi_mock = MagicMock()
    lich_moi_mock.id = 1
    mocker.patch('app.dao.tao_lich_lam_viec', return_value=(True, lich_moi_mock))
    
    ngay_moi_mock = MagicMock()
    ngay_moi_mock.ngay = date(2026, 5, 10) # Chủ nhật
    mock_tao_ngay = mocker.patch('app.dao.tao_ngay_lam_viec', return_value=(True, ngay_moi_mock))
    
    mock_tao_phan_ca = mocker.patch('app.dao.tao_phan_ca', return_value=(True, MagicMock()))
    mock_commit = mocker.patch('app.dao.commit')

    lich_tuan = {'CN': {'ca1': [1, 2], 'ca2': [3]}}
    
    success, msg = dao.tao_lich(lich_tuan, date(2026, 5, 10), date(2026, 5, 11))
    
    assert success is True
    assert msg == "Tạo lịch thành công!"
    mock_commit.assert_called_once()
    mock_tao_ngay.assert_called_once_with(date(2026, 5, 10), 1)
    
    assert mock_tao_phan_ca.call_count == 3

    expected_calls = [
        call(1, 'ca1', date(2026, 5, 10)),
        call(2, 'ca1', date(2026, 5, 10)),
        call(3, 'ca2', date(2026, 5, 10))
    ]
    mock_tao_phan_ca.assert_has_calls(expected_calls, any_order=True)

# ==========================================
# TEST: LuuLichLamViecSchema (marshmallow)
# ==========================================
import json

@pytest.fixture
def admin_login(test_app, test_client, mocker):
    class FakeAdmin:
        is_authenticated = True
        id = 1
        role = UserRole.ADMIN

    mocker.patch('flask_login.utils._get_user', return_value=FakeAdmin())
    return test_client


def _valid_payload(**overrides):
    today = date.today()
    start = today + timedelta(days=1)
    end = start + timedelta(days=7)
    payload = {
        'lichTuan': {'T2': {1: [1]}},
        'ngayBatDau': start.strftime('%Y-%m-%d'),
        'ngayKetThuc': end.strftime('%Y-%m-%d'),
    }
    payload.update(overrides)
    return payload


# ---------- lichTuan ----------
@pytest.mark.parametrize('lichTuan, err_msg', [
    (None, 'Dữ liệu không hợp lệ!'),
    ('not_a_dict', 'Dữ liệu không hợp lệ!'),
    ({'INVALID': {1: [1]}}, 'Dữ liệu không hợp lệ!'),
    ({'T2': 'not_a_dict'}, 'Dữ liệu không hợp lệ!'),
    ({'T2': {'abc': [1]}}, 'Dữ liệu không hợp lệ!'),
    ({'T2': {1: 'not_a_list'}}, 'Dữ liệu không hợp lệ!'),
    ({'T2': {1: ['abc']}}, 'Dữ liệu không hợp lệ!'),
])
def test_luu_lich_lichTuan_invalid(admin_login, lichTuan, err_msg, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich')
    payload = _valid_payload()
    if lichTuan is None:
        del payload['lichTuan']
    else:
        payload['lichTuan'] = lichTuan

    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == err_msg
    mock_tao_lich.assert_not_called()


yesterday = date.today() - timedelta(days=1)

@pytest.mark.parametrize('ngayBatDau, err_msg', [
    (None, 'Vui lòng cung cấp ngày bắt đầu.'),
    ('invalid-date', 'Ngày bắt đầu không hợp lệ!'),
    (yesterday.strftime('%Y-%m-%d'), 'Không thể tạo lịch làm việc trong quá khứ.'),
])
def test_luu_lich_ngayBatDau_invalid(admin_login, ngayBatDau, err_msg, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich')
    payload = _valid_payload()
    if ngayBatDau is None:
        del payload['ngayBatDau']
    else:
        payload['ngayBatDau'] = ngayBatDau

    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == err_msg
    mock_tao_lich.assert_not_called()


@pytest.mark.parametrize('ngayKetThuc, err_msg', [
    (None, 'Vui lòng cung cấp ngày kết thúc.'),
    ('invalid-date', 'Ngày kết thúc không hợp lệ!'),
])
def test_luu_lich_ngayKetThuc_invalid(admin_login, ngayKetThuc, err_msg, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich')
    payload = _valid_payload()
    if ngayKetThuc is None:
        del payload['ngayKetThuc']
    else:
        payload['ngayKetThuc'] = ngayKetThuc

    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == err_msg
    mock_tao_lich.assert_not_called()


def test_luu_lich_ngayKetThuc_truoc_ngayBatDau(admin_login, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich')
    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=2)
    payload = _valid_payload(
        ngayBatDau=start.strftime('%Y-%m-%d'),
        ngayKetThuc=end.strftime('%Y-%m-%d'),
    )
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == 'Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.'
    mock_tao_lich.assert_not_called()


def test_luu_lich_khoang_cach_duoi_7_ngay(admin_login, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich')
    start = date.today() + timedelta(days=1)
    end = start + timedelta(days=5)
    payload = _valid_payload(
        ngayBatDau=start.strftime('%Y-%m-%d'),
        ngayKetThuc=end.strftime('%Y-%m-%d'),
    )
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == 'Tạo lịch làm việc phải ít nhất 7 ngày.'
    mock_tao_lich.assert_not_called()


def test_luu_lich_valid_payload(admin_login, mocker):
    mock_tao_lich = mocker.patch('app.dao.tao_lich', return_value=(True, 'Tạo lịch thành công!'))
    payload = _valid_payload()

    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['message'] == 'Tạo lịch thành công!'
    mock_tao_lich.assert_called_once()

# ==========================================
# INTEGRATION TEST: API lưu lịch làm việc
# ==========================================

@pytest.fixture
def setup_bacsi_calam(test_session):
    u1 = User(username='bs_intg1', hoTen='BS Intg 1', email='bs_intg1@test.com',
              gioiTinh=True, role=UserRole.BACSI)
    u1.set_password('123456')
    test_session.add(u1)
    test_session.flush()
    bs1 = BacSi(user_id=u1.id, chuyenKhoa='Nhi Khoa')
    test_session.add(bs1)

    u2 = User(username='bs_intg2', hoTen='BS Intg 2', email='bs_intg2@test.com',
              gioiTinh=False, role=UserRole.BACSI)
    u2.set_password('123456')
    test_session.add(u2)
    test_session.flush()
    bs2 = BacSi(user_id=u2.id, chuyenKhoa='Tim Mạch')
    test_session.add(bs2)

    ca1 = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    ca2 = CaLam(tenCa='Ca Chiều', gioBatDau=time(13, 0), gioKetThuc=time(17, 0))
    test_session.add_all([ca1, ca2])
    test_session.commit()

    return {'bs1': bs1, 'bs2': bs2, 'ca1': ca1, 'ca2': ca2}


def test_intg_luu_lich_chua_dang_nhap(test_app, test_session):
    client = test_app.test_client()
    payload = _valid_payload()
    res = client.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 401


def test_intg_luu_lich_khong_phai_admin(test_client, mocker):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())

    payload = _valid_payload()
    res = test_client.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 403


def test_intg_luu_lich_validation_fail(admin_login):
    payload = _valid_payload()
    del payload['lichTuan']

    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['message'] == 'Dữ liệu không hợp lệ!'


def test_intg_luu_lich_trung_lich(admin_login, test_session, setup_bacsi_calam):
    start = date.today() + timedelta(days=1)
    end = start + timedelta(days=7)

    lich_cu = LichLamViec(ngayBatDau=start, ngayKetThuc=end)
    test_session.add(lich_cu)
    test_session.commit()

    payload = {
        'lichTuan': {'T2': {setup_bacsi_calam['ca1'].id: [setup_bacsi_calam['bs1'].id]}},
        'ngayBatDau': start.strftime('%Y-%m-%d'),
        'ngayKetThuc': end.strftime('%Y-%m-%d'),
    }
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'Đã tồn tại lịch' in data['message']


def test_intg_luu_lich_thanh_cong(admin_login, test_session, setup_bacsi_calam):
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    end_date = next_monday + timedelta(days=13)

    ca1_id = setup_bacsi_calam['ca1'].id
    ca2_id = setup_bacsi_calam['ca2'].id
    bs1_id = setup_bacsi_calam['bs1'].id
    bs2_id = setup_bacsi_calam['bs2'].id

    payload = {
        'lichTuan': {
            'T2': {ca1_id: [bs1_id, bs2_id]},
            'T4': {ca2_id: [bs1_id]},
        },
        'ngayBatDau': next_monday.strftime('%Y-%m-%d'),
        'ngayKetThuc': end_date.strftime('%Y-%m-%d'),
    }
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['message'] == 'Tạo lịch thành công!'

    lich = LichLamViec.query.filter_by(ngayBatDau=next_monday, ngayKetThuc=end_date).first()
    assert lich is not None

    t2_1 = next_monday
    t2_2 = next_monday + timedelta(days=7)

    for t2 in [t2_1, t2_2]:
        nlv = NgayLamViec.query.filter_by(ngay=t2).first()
        assert nlv is not None
        assert nlv.id_LichLamViec == lich.id
        pc1 = PhanCa.query.filter_by(id_BacSi=bs1_id, thuocNgay=t2, id_CaLam=ca1_id).first()
        pc2 = PhanCa.query.filter_by(id_BacSi=bs2_id, thuocNgay=t2, id_CaLam=ca1_id).first()
        assert pc1 is not None
        assert pc1.trangThai == TrangThaiBacSi.HoatDong
        assert pc2 is not None

    t4_1 = next_monday + timedelta(days=2)
    t4_2 = next_monday + timedelta(days=9)

    for t4 in [t4_1, t4_2]:
        nlv = NgayLamViec.query.filter_by(ngay=t4).first()
        assert nlv is not None
        pc = PhanCa.query.filter_by(id_BacSi=bs1_id, thuocNgay=t4, id_CaLam=ca2_id).first()
        assert pc is not None

    total_pc = PhanCa.query.count()
    assert total_pc == 6


def test_intg_luu_lich_ca_lam_khong_ton_tai(admin_login, test_session, setup_bacsi_calam):
    start = date.today() + timedelta(days=1)
    end = start + timedelta(days=7)
    bs1_id = setup_bacsi_calam['bs1'].id

    payload = {
        'lichTuan': {'T2': {9999: [bs1_id]}},
        'ngayBatDau': start.strftime('%Y-%m-%d'),
        'ngayKetThuc': end.strftime('%Y-%m-%d'),
    }
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'không tồn tại' in data['message'].lower()


def test_intg_luu_lich_bacsi_khong_ton_tai(admin_login, test_session, setup_bacsi_calam):
    start = date.today() + timedelta(days=1)
    end = start + timedelta(days=7)

    ca1_id = setup_bacsi_calam['ca1'].id

    payload = {
        'lichTuan': {'T2': {ca1_id: [9999]}},
        'ngayBatDau': start.strftime('%Y-%m-%d'),
        'ngayKetThuc': end.strftime('%Y-%m-%d'),
    }
    res = admin_login.post(
        '/api/admin/luu-lich-lam-viec',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert 'không tồn tại' in data['message'].lower()
