from datetime import datetime, time, date, timedelta

from sqlalchemy import func, and_

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

def auth_user(username, password):
    u = User.query.filter(User.username.__eq__(username)).first()
    if u and u.check_password(password):
        return u
    return None

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

# def get_so_ca_lam(time_range = 'all', kw = None):
#     query = db.session.query(
#        LichLamViec,
#         BacSi,
#         User,
#         func.count(PhieuDatLich.id).label('count')
#     ).join(BacSi,LichLamViec.bacsi_id == BacSi.id) \
#     .join(User, BacSi.user_id == User.id) \
#     .outerjoin(KhungGio, LichLamViec.id == KhungGio.lich_id) \
#     .outerjoin(PhieuDatLich, KhungGio.id == PhieuDatLich.khunggio_id)
#     if kw:
#         query = query.filter(User.hoTen.ilike(f'%{kw}%'))
#     today = date.today()
#     if time_range == 'today':
#         query = query.filter(LichLamViec.ngayLamViec == today)
#     elif time_range == 'week':
#         startWeek = today - timedelta(days=today.weekday())
#         endWeek = startWeek + timedelta(days=6)
#         query = query.filter(LichLamViec.ngayLamViec >= startWeek,
#                              LichLamViec.ngayLamViec<=endWeek)
#
#     return query.group_by(LichLamViec.id, BacSi.id, User.id).order_by(LichLamViec.ngayLamViec.desc()).all()
#
# def add_schedule(bacsi_id, ds_gio, ngay_lam_viec):
#     try:
#         schedule = datetime.strptime(ngay_lam_viec, '%Y-%m-%d').date()
#
#         lich = LichLamViec.query.filter_by(bacsi_id = bacsi_id,
#                                         ngayLamViec = ngay_lam_viec
#                                         ).first()
#
#         if not lich:
#             lich = LichLamViec(bacsi_id=bacsi_id,
#                                             ngayLamViec=ngay_lam_viec)
#             db.session.add(lich)
#             db.session.flush()
#         so_ca_lam = KhungGio.query.filter_by(lich_id = lich.id).count() if lich.id else 0
#
#         if so_ca_lam + len(ds_gio) > 20:
#             return False, f"Vượt quá giới hạn! Ngày này bác sĩ đã có {so_ca_lam} ca, bạn chỉ được thêm tối đa {20 - so_ca_lam} ca nữa."
#
#         khung_gio_da_co = []
#
#         if lich.id:
#             khung_gio_cu = KhungGio.query.filter_by(lich_id = lich.id).all()
#             khung_gio_da_co = [kg.startTime.strftime('%H:%M') for kg in khung_gio_cu]
#
#         for g in ds_gio:
#             if g in khung_gio_da_co:
#                 db.session.rollback()
#                 return False, "Khung giờ này không còn trống. Vui lòng chọn khung giờ khác!!!"
#             # Tính toán giờ kết thúc (+30 phút)
#             gio, phut = map(int, g.split(':'))
#             start_time = time(gio, phut)
#
#             phut_end = phut + 30
#             gio_end = gio
#             if phut_end >= 60:
#                 phut_end -= 60
#                 gio_end += 1
#             end_time = time(gio_end, phut_end)
#
#             # Tạo khung giờ mới
#             khung_gio_moi = KhungGio(
#                 lich_id=lich.id,
#                 startTime=start_time,
#                 endTime=end_time
#             )
#             db.session.add(khung_gio_moi)
#         db.session.commit()
#         return True, "Cập nhật lịch làm việc thành công!"
#     except Exception as e:
#         db.session.rollback()
#         return False, str(e)
#

# Thêm Status vào phần import ở đầu file dao.py