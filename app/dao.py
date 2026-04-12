from datetime import datetime, time, date, timedelta

from sqlalchemy import func, and_, or_

from app import app, db
from app.models import User, BenhNhan, BacSi, PhieuDatLich, LichLamViec, TrangThaiLichHen, UserRole, CaLam, NgayLamViec, PhanCa

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
