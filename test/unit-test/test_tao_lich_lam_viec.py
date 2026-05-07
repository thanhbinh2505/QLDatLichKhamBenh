import pytest
from datetime import date, timedelta, time, datetime
from app import dao
from app.models import LichLamViec, NgayLamViec, PhanCa, BacSi, CaLam, User, UserRole, TrangThaiBacSi, NgayNghiBacSi, TrangThaiDuyet
from test_base import test_session, test_app, test_client
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

#******************************************
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

    # 2026-05-10 là Chủ Nhật
    lich_tuan = {'CN': {'ca1': [1, 2]}}
    
    success, msg = dao.tao_lich(lich_tuan, date(2026, 5, 10), date(2026, 5, 10))
    assert success is False
    assert msg == "Lỗi tạo ngày làm việc"
    mock_tao_phan_ca.assert_not_called()

def test_tao_lich_tao_phan_ca_that_bai(mocker):
    lich_moi_mock = MagicMock()
    lich_moi_mock.id = 1
    mocker.patch('app.dao.tao_lich_lam_viec', return_value=(True, lich_moi_mock))
    
    ngay_moi_mock = MagicMock()
    ngay_moi_mock.ngay = date(2026, 5, 10)
    mocker.patch('app.dao.tao_ngay_lam_viec', return_value=(True, ngay_moi_mock))
    
    mocker.patch('app.dao.tao_phan_ca', return_value=(False, "Lỗi tạo phân ca"))
    mock_commit = mocker.patch('app.dao.commit')

    lich_tuan = {'CN': {'ca1': [1]}}
    
    success, msg = dao.tao_lich(lich_tuan, date(2026, 5, 10), date(2026, 5, 10))
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

    # 2026-05-10 là Chủ nhật, 2026-05-11 là Thứ 2
    # Chỉ config 'CN', nên ngày thứ 2 vòng lặp inner sẽ bị skip
    lich_tuan = {'CN': {'ca1': [1, 2], 'ca2': [3]}}
    
    success, msg = dao.tao_lich(lich_tuan, date(2026, 5, 10), date(2026, 5, 11))
    
    assert success is True
    assert msg == "Tạo lịch thành công!"
    mock_commit.assert_called_once()
    mock_tao_ngay.assert_called_once_with(date(2026, 5, 10), 1)
    
    # Được gọi 3 lần cho ca1(2 bác sĩ) + ca2(1 bác sĩ) = 3
    assert mock_tao_phan_ca.call_count == 3

    expected_calls = [
        call(1, 'ca1', date(2026, 5, 10)),
        call(2, 'ca1', date(2026, 5, 10)),
        call(3, 'ca2', date(2026, 5, 10))
    ]
    mock_tao_phan_ca.assert_has_calls(expected_calls, any_order=True)

