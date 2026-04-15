from datetime import datetime, time, date, timedelta

from sqlalchemy import func, and_, or_

from app import app, db
from app.models import (User, BenhNhan, BacSi, PhieuDatLich,
                        LichLamViec, TrangThaiLichHen, UserRole, CaLam,
                        NgayLamViec, PhanCa, KhungGio, TrangThaiBacSi)

import re
import json

def commit():
    db.session.commit()

def rollback():
    db.session.rollback()

def them_benhnhan(username, hoten, email, gioitinh, password, ngaysinh=None, diachi=None):
    try:
        if len(username) < 5:
            raise ValueError("Username phải ít nhất 5 kí tự!")
        if User.query.filter(User.username.__eq__(username)).first():
            raise ValueError("Username đã tồn tại!")
        if not hoten or not hoten.strip():
            raise ValueError("Họ tên không được để trống!")
        if User.query.filter(User.email.__eq__(email)).first():
            raise ValueError("Email đã có tài khoản!")
        if not email or not email.strip():
            raise ValueError("Email không được để trống!")
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email.strip()):
            raise ValueError("Email không đúng định dạng!")
        if len(password) < 8:
            raise ValueError("Mật khẩu phải ít nhất 8 kí tự!")
        if " " in password:
            raise ValueError("Mật khẩu không được chứa khoảng trắng!")
        if not re.search(r'[0-9]', password):
            raise ValueError("Mật khẩu phải chứa số!")
        if not re.search(r'[a-z]', password):
            raise ValueError("Mật khẩu phải chứa chữ thường!")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Mật khẩu phải chứa chữ hoa!")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Mật khẩu phải chứa ít nhất một kí tự đặc biệt!")

        user = User(username=username,
                    hoTen=hoten,
                    email=email,
                    gioiTinh=gioitinh,
                    role=UserRole.BENHNHAN
                    )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        benhnhan = BenhNhan(
            user_id=user.id,
            ngaySinh=ngaysinh,
            diaChi=diachi
        )
        db.session.add(benhnhan)
        db.session.commit()
        return benhnhan

    except Exception as e:
        db.session.rollback()
        raise e

def get_user_by_email_username(identifier):
    u = User.query.filter(or_(User.email == identifier, User.username == identifier)).first()
    return u

def get_user_by_id(id):
    return User.query.get(id)

def get_list_doctor():
    return BacSi.query.join(User, BacSi.user_id == User.id).all()

def get_list_shift():
    #tra ve từ diển

    ds_calam = CaLam.query.all()
    return [ca.to_dict() for ca in ds_calam]

KHUNG_GIO_SANG = [
    "08:00 - 08:30", "08:30 - 09:00", "09:00 - 09:30", "09:30 - 10:00",
    "10:00 - 10:30", "10:30 - 11:00", "11:00 - 11:30", "11:30 - 12:00"
]

KHUNG_GIO_CHIEU = [
    "13:00 - 13:30", "13:30 - 14:00", "14:00 - 14:30", "14:30 - 15:00",
    "15:00 - 15:30", "15:30 - 16:00", "16:00 - 16:30", "16:30 - 17:00"
]

def get_khung_gio_bac_si(bac_si_id, ngay_kham_str):

    ngay_kham = datetime.strptime(ngay_kham_str, '%Y-%m-%d').date()
    lich_truc = PhanCa.query.filter_by(id_BacSi=bac_si_id, thuocNgay=ngay_kham).all()

    if not lich_truc:
        return {"status": "nghi_phep", "message": "Bác sĩ không có lịch trực trong ngày này."}

    if any(ca.trangThai == TrangThaiBacSi.NghiPhep for ca in lich_truc):
        return {"status": "nghi_phep", "message": "Bác sĩ đang nghỉ phép, vui lòng chọn ngày khác."}

    ca_lam_ids = [ca.id_CaLam for ca in lich_truc]
    danh_sach_ca_lam = CaLam.query.filter(CaLam.id.in_(ca_lam_ids)).all()

    danh_sach_slot = []
    for ca in danh_sach_ca_lam:
        if "Ca Sáng" in ca.tenCa:
            danh_sach_slot.extend([{"gio": gio, "buoi": "sang"} for gio in KHUNG_GIO_SANG])
        elif "Ca Chiều" in ca.tenCa:
            danh_sach_slot.extend([{"gio": gio, "buoi": "chieu"} for gio in KHUNG_GIO_CHIEU])

    phieu_da_dat = PhieuDatLich.query.filter_by(
        bacsi_id=bac_si_id,
        ngayKham=ngay_kham,
        status=TrangThaiLichHen.Scheduled
    ).all()

    cac_gio_da_dat = {
        f"{phieu.khung_gio.startTime.strftime('%H:%M')} - {phieu.khung_gio.endTime.strftime('%H:%M')}"
        for phieu in phieu_da_dat
    }
    for slot in danh_sach_slot:
        slot["trang_thai"] = "da_dat" if slot["gio"] in cac_gio_da_dat else "con_trong"
    return {
        "status": "hoat_dong",
        "slots": danh_sach_slot
    }
def luu_phieu_dat_lich(bacsi_id, ngay_kham_str, gio_kham_str, current_user_id):
    try:
        try:
            ngay_kham = datetime.strptime(ngay_kham_str, '%Y-%m-%d').date()
            gio_bat_dau_str, gio_ket_thuc_str = gio_kham_str.split(" - ")
            start_time = datetime.strptime(gio_bat_dau_str, '%H:%M').time()
            end_time = datetime.strptime(gio_ket_thuc_str, '%H:%M').time()
        except ValueError:
            return False, "Định dạng ngày/giờ không hợp lệ.", None


        benhnhan = BenhNhan.query.filter_by(user_id=current_user_id).first()
        if not benhnhan:
            return False, "Không tìm thấy hồ sơ bệnh nhân.", None

        ngay_hien_tai = date.today()
        if ngay_kham > ngay_hien_tai + timedelta(days=30):
            return False, "Bạn chỉ có thể đặt lịch trước tối đa 30 ngày.", None
        if ngay_kham < ngay_hien_tai:
            return False, "Không thể đặt lịch cho ngày trong quá khứ.", None
        so_ca_da_dat = PhieuDatLich.query.filter(
            PhieuDatLich.benhnhan_id == benhnhan.id,
            PhieuDatLich.ngayKham == ngay_kham,
            PhieuDatLich.status != TrangThaiLichHen.Cancelled
        ).count()

        if so_ca_da_dat >= 2:
            return False, f"Chỉ đặt tối đa 2ca/ngày.Bạn đã đạt giới hạn: {ngay_kham.strftime('%d/%m/%Y')}.", None

        khung_gio = KhungGio.query.filter_by(startTime=start_time, endTime=end_time).first()
        if not khung_gio:
            khung_gio = KhungGio(startTime=start_time, endTime=end_time)
            db.session.add(khung_gio)
            db.session.flush()
        khung_gio_da_dat = PhieuDatLich.query.filter(
            PhieuDatLich.benhnhan_id==benhnhan.id,
            PhieuDatLich.khunggio_id == khung_gio.id,
            PhieuDatLich.ngayKham == ngay_kham,
            PhieuDatLich.status != TrangThaiLichHen.Cancelled
        ).first()
        if khung_gio_da_dat:
            return False, f"Bạn đã có lịch khám khung giờ {gio_kham_str} ngay {ngay_kham.strftime('%d/%m/%Y')}.Vui lòng chọn khung giờ khác!", None
        phieu_moi = PhieuDatLich(
            benhnhan_id=benhnhan.id,
            khunggio_id=khung_gio.id,
            bacsi_id=bacsi_id,
            ngayKham=ngay_kham,
            status=TrangThaiLichHen.Scheduled
        )
        db.session.add(phieu_moi)
        commit()

        bacsi = BacSi.query.get(bacsi_id)
        ten_bs = bacsi.user.hoTen if (bacsi and bacsi.user) else "Bác sĩ"

        thong_tin_dat_lich = {
            "doctor_name": f"BS. {ten_bs}",
            "date": ngay_kham.strftime('%d/%m/%Y'),
            "time": gio_kham_str
        }

        return True, "Bạn đã đặt lịch khám thành công.", thong_tin_dat_lich

    except Exception as e:
        db.session.rollback()
        return False, "Hệ thống đang gặp sự cố khi lưu lịch hẹn. Vui lòng thử lại!", None

def get_ngay_chua_sap_lich_gan_nhat():
    """
    Tìm ngày gần nhất chưa được phân lịch làm việc.
    Trả về object datetime.date
    """

    max_ngay_ket_thuc = db.session.query(func.max(LichLamViec.ngayKetThuc)).scalar()

    today = date.today()

    if max_ngay_ket_thuc is None:
        return today

    ngay_tiep_theo = max_ngay_ket_thuc + timedelta(days=1)

    if ngay_tiep_theo < today:
        return today

    return ngay_tiep_theo

def lay_ngay_lam_viec(ngay_bat_dau, ngay_ket_thuc):
    if not isinstance(ngay_bat_dau, date) or not isinstance(ngay_ket_thuc, date):
        raise ValueError("ngay_bat_dau và ngay_ket_thuc phải là kiểu datetime.date")

    if ngay_ket_thuc < ngay_bat_dau:
        raise ValueError("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu")

    ds_ngay_lam_viec = db.session.query(NgayLamViec).filter(
        NgayLamViec.ngay >= ngay_bat_dau,
        NgayLamViec.ngay <= ngay_ket_thuc
    ).order_by(NgayLamViec.ngay).all()

    return ds_ngay_lam_viec

def lay_danh_sach_phan_ca(ngay):
    ngay_lam_viec = NgayLamViec.query.get(ngay)

    if not ngay_lam_viec:
        return []

    return ngay_lam_viec.danh_sach_phan_ca

def tao_lich_lam_viec(ngay_bat_dau, ngay_ket_thuc):

    if ngay_bat_dau is None or ngay_ket_thuc is None:
        raise ValueError("Ngày bắt đầu và ngày kết thúc không được để trống.")

    if ngay_ket_thuc < ngay_bat_dau:
        raise ValueError("Ngày kết thúc không thể diễn ra trước ngày bắt đầu.")

    lich_da_tao = db.session.query(LichLamViec).filter(
        LichLamViec.ngayBatDau <= ngay_ket_thuc,
        LichLamViec.ngayKetThuc >= ngay_bat_dau
    ).first()

    if lich_da_tao:
        raise ValueError(
            f"Trùng lịch!(Đã tồn tại lịch từ {lich_da_tao.ngayBatDau} đến {lich_da_tao.ngayKetThuc}).")

    try:
        lich_moi = LichLamViec(ngayBatDau=ngay_bat_dau, ngayKetThuc=ngay_ket_thuc)
        db.session.add(lich_moi)

        db.session.flush()
        return lich_moi

    except Exception as e:
        db.session.rollback()
        raise e


def tao_ngay_lam_viec(ngay, id_lichlamviec):

    try:
        ngay_moi = NgayLamViec(
            ngay=ngay,
            id_LichLamViec=id_lichlamviec
        )

        db.session.add(ngay_moi)

        db.session.flush()

        return ngay_moi

    except Exception as e:
        db.session.rollback()
        raise e

def tao_phan_ca(id_bacsi, id_calam, thuoc_ngay):
    try:
        if not BacSi.query.get(id_bacsi):
            return False, "ID bác sĩ không tồn tại!"

        if not CaLam.query.get(id_calam):
            return False, "ID ca làm không tồn tại!"

        pc_ton_tai = PhanCa.query.filter(
            PhanCa.id_BacSi == id_bacsi,
            PhanCa.id_CaLam == id_calam,
            PhanCa.thuocNgay == thuoc_ngay
        ).first()

        if pc_ton_tai:
            return False, "Bác sĩ này đã được phân ca này trong ngày rồi."

        moi = PhanCa(
            id_BacSi=id_bacsi,
            id_CaLam=id_calam,
            thuocNgay=thuoc_ngay
        )

        db.session.add(moi)
        db.session.flush()
        return True, moi

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi tại tao_phan_ca: {str(e)}")
        return False, "Có lỗi xảy ra trong quá trình lưu dữ liệu."
