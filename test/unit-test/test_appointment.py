from sqlalchemy.testing.exclusions import succeeds_if
from test_base import test_session, test_app, test_client
from app.dao import luu_phieu_dat_lich, get_khung_gio_bac_si, get_lich_da_dat, count_huy_lich, huy_lich_kham, cap_nhat_trang_thai_lich_kham
from datetime import time, date, datetime, timedelta
from app.models import User, UserRole, BenhNhan, BacSi, NgayLamViec, CaLam, PhanCa, LichLamViec, TrangThaiBacSi, PhieuDatLich, TrangThaiLichHen, KhungGio
import pytest

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
    test_session.flush()

    kg1 = KhungGio(startTime=time(8, 0), endTime=time(8, 30), calam_id=ca.id)
    kg2 = KhungGio(startTime=time(8, 30), endTime=time(9, 0), calam_id=ca.id)
    kg3 = KhungGio(startTime=time(9, 0), endTime=time(9, 30), calam_id=ca.id)
    test_session.add_all([kg1, kg2, kg3])

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

@pytest.fixture
def setup_db_for_cancel(test_session):
    u_1 = User(username='bn1', hoTen='Bệnh Nhân 1', email='bn1@gmail.com', gioiTinh=True, role=UserRole.BENHNHAN, password='Abcd123@')
    u_2= User(username='bn2', hoTen='Bệnh Nhân 2', email='bn2@gmail.com', gioiTinh=True, role=UserRole.BENHNHAN, password='Abcd123@')
    u_admin =User(username='admin', hoTen='Quản Trị Viên 1', email='admin1@gmail.com', gioiTinh=True, role=UserRole.ADMIN, password='Abcd123@')
    test_session.add_all([u_1, u_2, u_admin])
    test_session.flush()

    # 2. Tạo Bệnh Nhân & Bác Sĩ
    patient = BenhNhan(user_id=u_1.id)
    test_session.add(patient)

    u_doctor = User(username='bs1', hoTen='Bác Sĩ 1', email='bs1@gmail.com', gioiTinh=True, role=UserRole.BACSI, password='Abcd123@')
    test_session.add(u_doctor)
    test_session.flush()
    doctor = BacSi(user_id=u_doctor.id, chuyenKhoa='Nhi Khoa')
    test_session.add(doctor)

    # 3. Tạo Khung giờ mẫu
    ca = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 0))
    test_session.add(ca)
    test_session.flush()

    kg = KhungGio(startTime=time(8, 0), endTime=time(8, 30), calam_id=ca.id)
    test_session.add(kg)
    test_session.commit()

    return {
        'u_patient': u_1,
        'u_other': u_2,
        'u_admin': u_admin,
        'patient_id': patient.id,
        'doctor_id': doctor.id,
        'khunggio_id': kg.id
    }

def phieu_dat_lich_test(test_session, data, status, ngay_kham_str, cancelTime = None):
    phieu = PhieuDatLich(
        benhnhan_id = data['patient_id'],
        bacsi_id = data['doctor_id'],
        khunggio_id = data['khunggio_id'],
        ngayKham = ngay_kham_str,
        status = status,
        cancelTime = cancelTime
    )
    test_session.add(phieu)
    test_session.commit()
    return phieu

# KIỂM THỬ API

def test_dat_lich_thanh_cong(test_client, mocker, setup_db_for_booking):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())

    payload = {
        "bacsi_id": setup_db_for_booking['doctor_id'],
        "ngay_kham": setup_db_for_booking['ngay_kham'],
        "gio_kham": "08:00 - 08:30"
    }
    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()
    assert res.status_code == 200
    assert data['success'] is True
    assert data['loai_thong_bao'] == 'success'
    assert "Bạn đã đặt lịch khám thành công." in data['message']

    phieu_moi = PhieuDatLich.query.filter_by(
        benhnhan_id=setup_db_for_booking['patient_id'],
        bacsi_id=setup_db_for_booking['doctor_id']
    ).first()

    assert phieu_moi is not None
    assert phieu_moi.status == TrangThaiLichHen.Scheduled

def test_dat_lich_that_bai_chua_dang_nhap(test_client, mocker):
    class FakeUser:
        is_authenticated = False

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    payload = {
        "bacsi_id": 2,
        "ngay_kham": "2026-05-15",
        "gio_kham": "08:00 - 08:30"
    }
    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()
    assert res.status_code == 401
    assert data['success'] is False
    assert data['loai_thong_bao'] == 'auth_required'
    assert data['message'] == "Vui lòng đăng nhập để đặt lịch khám!"

def test_dat_lich_that_bai_sai_role(test_client, mocker):
    class FakeUser:
        is_authenticated = True
        id = 1
        role = UserRole.BACSI

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    payload = {"bacsi_id": 2, "ngay_kham": "2026-05-15", "gio_kham": "08:00 - 08:30"}

    res = test_client.post('/api/dat-lich', json=payload)
    data = res.get_json()

    assert res.status_code == 401
    assert data['success'] is False
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

def test_api_huy_lich_thanh_cong(test_client, test_session, setup_db_for_cancel, mocker):
    class FakeUser:
        is_authenticated = True
        id = setup_db_for_cancel['u_patient'].id
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    ngay_kham = date.today() + timedelta(days=1)
    phieu = phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Scheduled, ngay_kham)

    res = test_client.post(f'/api/huy-lich/{phieu.id}')
    data = res.get_json()

    assert res.status_code == 200
    assert data['success'] is True
    assert "Hủy lịch khám thành công." in data['message']
    assert phieu.cancelTime is not None
    assert phieu.status == TrangThaiLichHen.Cancelled

def test_api_huy_lich_that_bai(test_client, test_session, setup_db_for_cancel, mocker):
    class FakeUser:
        is_authenticated = True
        id = setup_db_for_cancel['u_patient'].id
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    res = test_client.post('/api/huy-lich/999')
    data = res.get_json()
    assert res.status_code == 400
    assert data['success'] is False
    assert data['message'] == "Không tìm thấy phiếu đặt lịch."

def test_huy_lich_chua_dang_nhap(test_client,mocker):
    class FakeUser:
        is_authenticated = False
    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())
    res = test_client.post('/api/huy-lich/1')
    assert res.status_code == 401

def test_api_ho_so_lich_kham(test_client, test_session, setup_db_for_booking, mocker):
    patient_id = setup_db_for_booking['patient_id']
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    class FakeUser:
        is_authenticated = True
        id = patient_id
        role = UserRole.BENHNHAN

    mocker.patch('flask_login.utils._get_user', return_value=FakeUser())

    luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient_id)
    res = test_client.get('/api/ho-so/lich-kham')
    data = res.get_json()

    assert res.status_code == 200
    assert len(data) == 1
    assert data[0]['status'] == "Scheduled"
    assert data[0]['ngay_kham_str'] == "15/05/2026"

def test_lay_gio_kham_thanh_cong(test_client, test_session,mocker,setup_db_for_booking):
    bacsi_id = setup_db_for_booking['doctor_id']
    ngay_kham = setup_db_for_booking['ngay_kham']

    res = test_client.get(f'/api/gio-kham-bac-si?bacsi_id={bacsi_id}&ngay={ngay_kham}')
    data = res.get_json()

    assert res.status_code == 200
    assert data['status'] == "hoat_dong"
    assert len(data['slots']) > 0

def test_lay_gio_kham_thieu_tham_so(test_client):
    res = test_client.get('/api/gio-kham-bac-si?bacsi_id=1')
    data = res.get_json()

    assert res.status_code == 400
    assert data['error'] == "Thiếu tham số"

# Kiểm thử đặt lịch khám

def test_sai_dinh_dang_ngay_gio(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']

    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str='2026-04-16',
        gio_kham_str='08AM - 09AM',
        current_user_id=patient_id,
    )

    assert success is False
    assert "Định dạng ngày/giờ không hợp lệ" in msg
    assert info is None

def test_luu_phieu_dat_lich_thanh_cong(test_session, setup_db_for_booking):
    success, msg, info = luu_phieu_dat_lich(
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

    luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:00 - 08:30',
        patient_id,
    )
    luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '08:30 - 09:00',
        patient_id,
    )
    success, msg, info = luu_phieu_dat_lich(
        doctor_id,
        ngay_kham_str,
        '09:00 - 09:30',
        patient_id,
    )

    assert success is False
    assert "tối đa 2ca/ngày" in msg
    assert info is None
    assert PhieuDatLich.query.count() == 2

def test_trung_khung_gio_1_ngay_benh_nhan(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient_id)
    success, msg, info = luu_phieu_dat_lich(doctor_id,ngay_kham_str , '08:00 - 08:30', patient_id)
    assert success is False
    assert "đã có lịch khám khung giờ" in msg
    assert info is None

def test_dat_lich_trung_gio_bac_si(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient1_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient1_id)
    u2 = User(
        username='bn2', hoTen='Bệnh Nhân 2', email='bn2@gmail.com',
        gioiTinh=True, role=UserRole.BENHNHAN, password='123456'
    )
    test_session.add(u2)
    test_session.flush()
    bn2 = BenhNhan(user_id=u2.id)
    test_session.add(bn2)
    test_session.commit()

    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=u2.id
    )

    assert success is False
    assert "Khung giờ này đã có người đặt" in msg
    assert info is None

def test_khong_dat_lich_qua_30_ngay(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = '2026-8-15'
    success, msg, info = luu_phieu_dat_lich(
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
    success, msg, info = luu_phieu_dat_lich(
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

    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=patient_id,
    )
    assert success is False
    assert "Tài khoản đang bị hạn chế đặt lịch" in msg
    assert info is None

def test_khung_gio_da_qua_trong_ngay(test_session, setup_db_for_booking, mocker):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    mock_now = datetime(2026, 4, 30, 9, 0, 0)

    class MockDateTime(datetime):
        @classmethod
        def now(cls):
            return mock_now

    class MockDate(date):
        @classmethod
        def today(cls):
            return mock_now.date()

    # 2. Gắn Mock vào file app.dao để nó dùng thời gian giả thay vì giờ hệ thống
    mocker.patch('app.dao.datetime', MockDateTime)
    mocker.patch('app.dao.date', MockDate)
    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str='2026-04-30',
        gio_kham_str='08:00 - 08:30',
        current_user_id=patient_id,
    )

    assert success is False
    assert "Khung giờ đã qua" in msg

def test_dat_lich_khung_gio_khong_ton_tai(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham = setup_db_for_booking['ngay_kham']

    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham,
        gio_kham_str='18:00 - 18:30',
        current_user_id=patient_id,
    )

    assert success is False
    assert "Khung giờ khám không tồn tại hoặc nằm ngoài giờ làm việc." in msg

def test_khong_tim_thay_ho_so_benh_nhan(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    # Dùng một ID giả mạo (không tồn tại trong Database)
    user_id = 999

    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=user_id,
    )

    assert success is False
    assert "Không tìm thấy hồ sơ bệnh nhân" in msg
    assert info is None

def test_try_except_database(test_session, setup_db_for_booking, mocker):
    doctor_id = setup_db_for_booking['doctor_id']
    patient_id = setup_db_for_booking['patient_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    mocker.patch('app.dao.commit', side_effect=Exception("Database Timeout"))
    success, msg, info = luu_phieu_dat_lich(
        bacsi_id=doctor_id,
        ngay_kham_str=ngay_kham_str,
        gio_kham_str='08:00 - 08:30',
        current_user_id=patient_id,
    )
    assert success is False
    assert "Hệ thống đang gặp sự cố khi lưu lịch hẹn" in msg
#Kiểm thử lấy khung giờ

def test_get_khung_gio(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']
    patient_id = setup_db_for_booking['patient_id']

    luu_phieu_dat_lich(doctor_id, ngay_kham_str, '08:00 - 08:30', patient_id)

    res = get_khung_gio_bac_si(doctor_id, ngay_kham_str)
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

    res = get_khung_gio_bac_si(doctor_id, ngay_kham_str)

    assert res is not None
    assert res['status'] == 'nghi_phep'
    assert "không có lịch trực" in res['message']

def test_get_khung_gio_bac_si_nghi_phep(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']
    phan_ca = PhanCa.query.filter_by(id_BacSi=doctor_id).first()
    phan_ca.trangThai = TrangThaiBacSi.NghiPhep
    test_session.commit()

    res = get_khung_gio_bac_si(doctor_id, ngay_kham_str)
    assert res is not None
    assert res['status'] == 'nghi_phep'
    assert "đang nghỉ phép" in res['message']

def test_get_khung_gio__con_trong_full(test_session, setup_db_for_booking):
    doctor_id = setup_db_for_booking['doctor_id']
    ngay_kham_str = setup_db_for_booking['ngay_kham']

    res = get_khung_gio_bac_si(doctor_id, ngay_kham_str)

    assert res['status'] == 'hoat_dong'
    for slot in res['slots']:
        assert slot['trang_thai'] == 'con_trong'

# Kiểm thử lấy lịch khám đã đặt

def test_get_lich_kham(test_session, setup_db_for_cancel):
    u_patient = setup_db_for_cancel['u_patient']
    ngay_kham_str = date.today()+ timedelta(days=1)
    phieu_dat_lich_test(
        test_session,
        setup_db_for_cancel,
        TrangThaiLichHen.Scheduled,
        ngay_kham_str
    )
    phieu_dat_lich_test(
        test_session,
        setup_db_for_cancel,
        TrangThaiLichHen.Cancelled,
        ngay_kham_str
    )
    res = get_lich_da_dat(u_patient.id)
    assert res is not None
    assert isinstance(res, list)
    assert len(res) == 2
    assert res[0]['status'] == 'Scheduled'
    assert res[0]['gio_kham_str']=='08:00 - 08:30'

def test_get_lich_da_dat_rong(test_session, setup_db_for_cancel):
    u_other = setup_db_for_cancel['u_other']

    res = get_lich_da_dat(u_other.id)
    assert res == []
    assert len(res) == 0

def test_auto_cap_nhat_trang_thai_lich_kham(test_session, test_app, setup_db_for_cancel, mocker):
    ngay_kham = date.today()
    phieu = phieu_dat_lich_test(
        test_session,
        setup_db_for_cancel,
        TrangThaiLichHen.Scheduled,
        ngay_kham
    )
    mock_now = datetime.combine(ngay_kham, time(8, 35))
    class MockDateTime(datetime):
        @classmethod
        def now(cls): return mock_now
    mocker.patch('app.dao.datetime', MockDateTime)
    mocker.patch('app.dao.app.app_context')
    cap_nhat_trang_thai_lich_kham()
    test_session.refresh(phieu)
    assert phieu.status == TrangThaiLichHen.Completed

def test_auto_cap_nhat_bo_qua_phieu_chua_den_gio(test_session, test_app, setup_db_for_cancel, mocker):
    ngay_kham = date.today()
    phieu = phieu_dat_lich_test(
        test_session,
        setup_db_for_cancel,
        TrangThaiLichHen.Scheduled,
        ngay_kham
    )
    mock_now = datetime.combine(ngay_kham, time(8, 15))
    class MockDateTime(datetime):
        @classmethod
        def now(cls): return mock_now

    mocker.patch('app.dao.datetime', MockDateTime)
    mocker.patch('app.dao.app.app_context')
    cap_nhat_trang_thai_lich_kham()
    test_session.refresh(phieu)
    assert phieu.status == TrangThaiLichHen.Scheduled

# Kiểm thử hủy lịch khám

def test_lich_kham_khong_ton_tai(test_session, setup_db_for_cancel):
    u = setup_db_for_cancel['patient_id']
    success, msg = huy_lich_kham(999, u)

    assert success is False
    assert "Không tìm thấy phiếu đặt lịch." in msg

def test_lich_da_hoan_thanh(test_session, setup_db_for_cancel):
    phieu = phieu_dat_lich_test(
        test_session, setup_db_for_cancel, TrangThaiLichHen.Completed, date.today()
    )
    success, msg = huy_lich_kham(
        phieu.id,
        setup_db_for_cancel['u_patient']
    )
    assert success is False
    assert "Lịch khám đã hoàn thành, không thể hủy." in msg

def test_lich_da_huy_truoc(test_session, setup_db_for_cancel):
    phieu = phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Cancelled, date.today())
    success, msg = huy_lich_kham(phieu.id, setup_db_for_cancel['u_patient'])
    assert success is False
    assert "Lịch khám đã được hủy trước đó." in msg

def test_huy_lich_trong_gio_kham(test_session, setup_db_for_cancel, mocker):
    u_patient = setup_db_for_cancel['u_patient']
    mock_now = datetime.combine(date.today(), time(8, 15))
    class MockDateTime(datetime):
        @classmethod
        def now(cls):
            return mock_now
    mocker.patch('app.dao.datetime', MockDateTime)
    phieu = phieu_dat_lich_test(test_session, setup_db_for_cancel,  TrangThaiLichHen.Scheduled, mock_now.date())
    success, msg = huy_lich_kham(phieu.id, u_patient)
    assert success is False
    assert "Đang trong giờ khám. Không thể hủy lịch khám." in msg

def test_huy_lich_duoi_1_tieng(test_session, setup_db_for_cancel, mocker):
    u_patient = setup_db_for_cancel['u_patient']

    # Giả lập hiện tại là 07:30 (Chỉ còn 30 phút nữa là đến giờ khám 08:00)
    mock_now = datetime.combine(date.today(), time(7, 30))
    class MockDateTime(datetime):
        @classmethod
        def now(cls):
            return mock_now
    mocker.patch('app.dao.datetime', MockDateTime)
    phieu = phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Scheduled, mock_now.date())

    success, msg = huy_lich_kham(phieu.id, u_patient)
    assert success is False
    assert "dưới 1 giờ" in msg

def test_huy_lich_qua_3_lan(test_session, setup_db_for_cancel, mocker):
    u_patient = setup_db_for_cancel['u_patient']
    ngay_kham = date.today() + timedelta(days=1)
    phieu = phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Scheduled, ngay_kham)
    mocker.patch('app.dao.count_huy_lich', return_value=4)
    success, msg = huy_lich_kham(phieu.id, u_patient)

    assert success is True
    assert "tài khoản bị hạn chế đặt lịch trong 24h tới" in msg
    assert phieu.benh_nhan.thoiGianMoKhoa is not None

def test_count_huy_lich(test_session, setup_db_for_cancel):
    patient_id = setup_db_for_cancel['patient_id']
    phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Cancelled, datetime.now().date(), cancelTime=datetime.now())
    phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Cancelled, datetime.now().date(), cancelTime=datetime.now())

    thang_truoc = datetime.now() - timedelta(days=30)
    phieu_dat_lich_test(test_session, setup_db_for_cancel, TrangThaiLichHen.Cancelled, datetime.now().date(), cancelTime=thang_truoc)

    so_lan_huy = count_huy_lich(patient_id)
    assert so_lan_huy == 2

def test_khong_co_quyen_huy(test_session, setup_db_for_cancel):
    phieu = phieu_dat_lich_test(
        test_session,setup_db_for_cancel,TrangThaiLichHen.Scheduled, (date.today() + timedelta(days=1))
    )
    u_other = setup_db_for_cancel['u_other']
    success, msg = huy_lich_kham(phieu.id, u_other)

    assert success is False
    assert "Bạn không có quyền hủy lịch khám này." in msg

def test_admin_co_quyen_huy_lich(test_session, setup_db_for_cancel):
    phieu = phieu_dat_lich_test(
        test_session,
        setup_db_for_cancel,
        TrangThaiLichHen.Scheduled,
        date.today() + timedelta(days=1)
    )

    u_admin = setup_db_for_cancel['u_admin']
    success, msg = huy_lich_kham(phieu.id, u_admin)

    assert success is True
    assert "thành công" in msg
    assert phieu.status == TrangThaiLichHen.Cancelled
    assert phieu.user_huy_id == u_admin.id



