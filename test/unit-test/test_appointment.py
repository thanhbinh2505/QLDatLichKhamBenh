
from app import dao
from test_base import test_session, test_app, test_client
from datetime import time, date, datetime, timedelta
from app.models import User, UserRole, BenhNhan, BacSi, NgayLamViec, CaLam, PhanCa, LichLamViec, TrangThaiBacSi, PhieuDatLich, TrangThaiLichHen
from app.dao import get_khung_gio_bac_si, luu_phieu_dat_lich
import pytest

# KIỂM THỬ API Đặt Lịch

def test_dat_lich_thanh_cong(test_client, mocker):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    mock_luu_phieu = mocker.patch('app.dao.luu_phieu_dat_lich', return_value=(
        True,
        "Bạn đã đặt lịch khám thành công.",
        {"doctor_name": "BS. Nguyễn Thanh Bình",
         "date": "19/04/2026",
         "time": "08:00 - 08:30"}
    ))
    payload = {
        "bacsi_id": 2,
        "ngay_kham": "2026-04-19",
        "gio_kham": "08:00 - 08:30"
    }
    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True
    assert data['loai_thong_bao'] == 'success'
    assert data['message'] == "Bạn đã đặt lịch khám thành công."
    assert data['booking_info']['doctor_name'] == "BS. Nguyễn Thanh Bình"

    mock_luu_phieu.assert_called_once_with(
        bacsi_id=2,
        ngay_kham_str="2026-04-19",
        gio_kham_str="08:00 - 08:30",
        current_user_id=1
    )

def test_dat_lich_that_bai_chua_dang_nhap(test_client, mocker):
    class FakeUser:
        is_authenticated = False

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    payload = {
        "bacsi_id": 2,
        "ngay_kham": "2026-04-15",
        "gio_kham": "08:00 - 08:30"
    }
    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()
    assert res.status_code == 401
    assert data['success'] is False
    assert data['loai_thong_bao'] == 'auth_required'
    assert data['message'] == "Vui lòng đăng nhập để đặt lịch khám!"

def test_dat_lich_that_bai_thieu_tham_so(test_client, mocker):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    payload = {
        "bacsi_id": 2,
        "ngay_kham": "2026-04-15"
    }
    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()
    assert res.status_code == 400
    assert data['success'] is False
    assert data['message'] == "Thiếu thông tin đặt lịch!"

# KIỂM THỬ API Lấy Khung Giờ Bác Sĩ

def test_lay_gio_kham_thanh_cong(test_client,mocker):
    mock_data = {
        "status": "hoat_dong",
        "slots": [{"gio": "08:00 - 08:30", "trang_thai": "con_trong", "buoi": "sang"}]
    }
    mocker.patch('app.dao.get_khung_gio_bac_si', return_value=mock_data)

    res = test_client.get('/api/gio-kham-bac-si?bacsi_id=1&ngay=2026-04-15')
    data = res.get_json()

    assert res.status_code == 200
    assert data['status'] == "hoat_dong"

def test_lay_gio_kham_thieu_tham_so(test_client):
    res = test_client.get('/api/gio-kham-bac-si?bacsi_id=1')
    data = res.get_json()

    assert res.status_code == 400
    assert data['error'] == "Thiếu tham số"

@pytest.fixture
def setup_db_for_booking(test_session):

    u_patient = User(username='bn1', hoTen='Bệnh Nhân 1', email='bn1@gmail.com', gioiTinh=True, role=UserRole.BENHNHAN, password='Abcd123@')
    test_session.add(u_patient)
    test_session.flush()
    patient = BenhNhan(user_id=u_patient.id)
    test_session.add(patient)

    # 2. Tạo Bác sĩ
    u_doc = User(username='bs1', hoTen='Bác Sĩ 1', email='bs1@gmail.com', gioiTinh=True, role=UserRole.BACSI, password='Abcd123@')
    test_session.add(u_doc)
    test_session.flush()
    doctor = BacSi(user_id=u_doc.id, chuyenKhoa='Nhi Khoa')
    test_session.add(doctor)

    # 3. Tạo Ca làm việc (Ca Sáng)
    ca = CaLam(tenCa='Ca Sáng', gioBatDau=time(8,0), gioKetThuc=time(12,0))
    test_session.add(ca)

    ngay_truc = date(2026, 5, 15)
    lich = LichLamViec(ngayBatDau=ngay_truc, ngayKetThuc=ngay_truc)
    test_session.add(lich)
    test_session.flush()

    ngay_lam_viec = NgayLamViec(ngay=ngay_truc, id_LichLamViec=lich.id)
    test_session.add(ngay_lam_viec)

    # Phân ca cho bác sĩ vào ca sáng ngày hôm đó
    phan_ca = PhanCa(id_BacSi=doctor.id, thuocNgay=ngay_truc, id_CaLam=ca.id, trangThai=TrangThaiBacSi.HoatDong)
    test_session.add(phan_ca)
    test_session.commit()

    return {
        'patient_id': u_patient.id,
        'doctor_id': doctor.id,
        'ngay_kham': '2026-05-15'
    }

def test_sai_dinh_dang_ngay_gio(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']

    success, msg, info = dao.luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str='2026-04-16',
        gio_kham_str='08AM - 09AM',
        current_user_id=patient_id,
    )

    assert success is False
    assert "Định dạng ngày/giờ không hợp lệ" in msg
    assert info is None

def test_luu_phieu_dat_lich_thanh_cong(test_session, setup_db_for_booking):
    success, msg, info = dao.luu_phieu_dat_lich(
        bacsi_id=setup_db_for_booking['doctor_id'],
        ngay_kham_str=setup_db_for_booking['ngay_kham'],
        gio_kham_str='08:00 - 08:30',
        current_user_id=setup_db_for_booking['patient_id'],
    )
    phieu_moi = PhieuDatLich.query.first()
    assert success is True
    assert "thành công" in msg
    assert info['doctor_name'] == "BS. Bác Sĩ 1"
    assert PhieuDatLich.query.count() == 1
    assert phieu_moi.status == TrangThaiLichHen.Scheduled

def test_gioi_han_2_ca(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    dao.luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:00 - 08:30',
        patient_id,
    )
    dao.luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:30 - 09:00',
        patient_id,
    )
    success, msg, info = dao.luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '09:00 - 09:30',
        patient_id,
    )

    assert success is False
    assert "tối đa 2ca/ngày" in msg
    assert info is None
    assert PhieuDatLich.query.count() == 2

def test_trung_khung_gio_1_ngay(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    dao.luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient_id)
    success, msg, info = dao.luu_phieu_dat_lich('2',ngay_kham_str , '08:00 - 08:30', patient_id)
    assert success is False
    assert "đã có lịch khám khung giờ" in msg
    assert info is None

def test_khong_dat_lich_qua_30_ngay(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = '2026-8-15'
    success, msg, info = dao.luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:00 - 08:30',
        patient_id,
    )
    assert success is False
    assert msg == "Bạn chỉ có thể đặt lịch trước tối đa 30 ngày."
    assert info is None

def test_khong_dat_lich_qua_khu(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = '2026-1-1'
    success, msg, info = dao.luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:00 - 08:30',
        patient_id,
    )
    assert success is False
    assert msg == "Không thể đặt lịch cho ngày trong quá khứ."
    assert info is None

def test_bi_khoa_dat_lich_24h(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    benh_nhan = BenhNhan.query.filter_by(user_id= patient_id).first()
    thoi_gian_mo_khoa = datetime.now() + timedelta(hours=15)
    benh_nhan.thoiGianMoKhoa = thoi_gian_mo_khoa
    test_session.commit()

    success, msg, info = dao.luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=patient_id,
    )
    assert success is False
    assert "Tài khoản đang bị hạn chế đặt lịch" in msg
    assert info is None

def test_khung_gio_da_qua_trong_ngay(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']

    success, msg, info = dao.luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str='2026-4-18',
        gio_kham_str='08:00 - 08:30',
        current_user_id=patient_id,
    )

    assert success is False
    assert "Khung giờ đã qua" in msg

def test_khong_tim_thay_ho_so_benh_nhan(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    # Dùng một ID giả mạo (không tồn tại trong Database)
    user_id = 999

    success, msg, info = dao.luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=user_id,
    )

    assert success is False
    assert "Không tìm thấy hồ sơ bệnh nhân" in msg
    assert info is None

def test_get_khung_gio(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']
    patient_id = setup_db_for_booking['patient_id']

    dao.luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient_id)

    res = dao.get_khung_gio_bac_si(doctor_id, ngay_kham_str)
    assert res is not None
    assert res['status'] == 'hoat_dong'
    for s in res['slots']:
        if s['gio'] == '08:00 - 08:30':
            assert s['trang_thai'] == 'da_dat'
        if s['gio'] == '08:30 - 09:00':
            assert s['trang_thai'] == 'con_trong'

def test_get_khung_gio_ngay_khong_co_lich_truc(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = '2026-8-15'

    res = dao.get_khung_gio_bac_si(doctor_id, ngay_kham_str)

    assert res is not None
    assert res['status'] == 'nghi_phep'
    assert "không có lịch trực" in res['message']

def test_get_khung_gio_bac_si_nghi_phep(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']
    phan_ca = PhanCa.query.filter_by(id_BacSi=doctor_id).first()
    phan_ca.trangThai = TrangThaiBacSi.NghiPhep
    test_session.commit()

    res = dao.get_khung_gio_bac_si(doctor_id, ngay_kham_str)
    assert res is not None
    assert res['status'] == 'nghi_phep'
    assert "đang nghỉ phép" in res['message']

def test_get_khung_gio__con_trong_full(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    res = dao.get_khung_gio_bac_si(doctor_id, ngay_kham_str)

    assert res['status'] == 'hoat_dong'
    for slot in res['slots']:
        assert slot['trang_thai'] == 'con_trong'
