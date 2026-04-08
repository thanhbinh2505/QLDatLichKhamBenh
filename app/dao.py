from datetime import datetime, time, date, timedelta

from sqlalchemy import func, outerjoin

from app import app, db
from app.models import User, BenhNhan, BacSi, KhungGio, PhieuDatLich, LichLamViec, Status

import json

import hashlib

def tao_user(username, hoten, email, gioitinh, password, role):
    user = User(username=username,
                hoTen=hoten,
                email=email,
                gioiTinh=gioitinh,
                role=role
                )
    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    return user

def them_benhnhan(username, hoten, email, gioitinh, password, role, ngaysinh=None, diachi=None):
    try:
        user = tao_user(username, hoten, email, gioitinh, password, role)

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
        return None

def auth_user(username, password):
    u = User.query.filter(User.username.__eq__(username)).first()
    if u and u.check_password(password):
        return u
    return None

def get_user_by_id(id):
    return User.query.get(id)

def get_list_doctor():
    return BacSi.query.join(User, BacSi.user_id == User.id).all()

def get_so_ca_lam(time_range = 'all', kw = None):
    query = db.session.query(
       LichLamViec,
        BacSi,
        User,
        func.count(PhieuDatLich.id).label('count')
    ).join(BacSi,LichLamViec.bacsi_id == BacSi.id) \
    .join(User, BacSi.user_id == User.id) \
    .outerjoin(KhungGio, LichLamViec.id == KhungGio.lich_id) \
    .outerjoin(PhieuDatLich, KhungGio.id == PhieuDatLich.khunggio_id)
    if kw:
        query = query.filter(User.hoTen.ilike(f'%{kw}%'))
    today = date.today()
    if time_range == 'today':
        query = query.filter(LichLamViec.ngayLamViec == today)
    elif time_range == 'week':
        startWeek = today - timedelta(days=today.weekday())
        endWeek = startWeek + timedelta(days=6)
        query = query.filter(LichLamViec.ngayLamViec >= startWeek,
                             LichLamViec.ngayLamViec<=endWeek)

    return query.group_by(LichLamViec.id, BacSi.id, User.id).order_by(LichLamViec.ngayLamViec.desc()).all()

def add_schedule(bacsi_id, ds_gio, ngay_lam_viec):
    try:
        schedule = datetime.strptime(ngay_lam_viec, '%Y-%m-%d').date()

        lich = LichLamViec.query.filter_by(bacsi_id = bacsi_id,
                                        ngayLamViec = ngay_lam_viec
                                        ).first()

        if not lich:
            lich = LichLamViec(bacsi_id=bacsi_id,
                                            ngayLamViec=ngay_lam_viec)
            db.session.add(lich)
            db.session.flush()
        so_ca_lam = KhungGio.query.filter_by(lich_id = lich.id).count() if lich.id else 0

        if so_ca_lam + len(ds_gio) > 20:
            return False, f"Vượt quá giới hạn! Ngày này bác sĩ đã có {so_ca_lam} ca, bạn chỉ được thêm tối đa {20 - so_ca_lam} ca nữa."

        khung_gio_da_co = []

        if lich.id:
            khung_gio_cu = KhungGio.query.filter_by(lich_id = lich.id).all()
            khung_gio_da_co = [kg.startTime.strftime('%H:%M') for kg in khung_gio_cu]

        for g in ds_gio:
            if g in khung_gio_da_co:
                db.session.rollback()
                return False, "Khung giờ này không còn trống. Vui lòng chọn khung giờ khác!!!"
            # Tính toán giờ kết thúc (+30 phút)
            gio, phut = map(int, g.split(':'))
            start_time = time(gio, phut)

            phut_end = phut + 30
            gio_end = gio
            if phut_end >= 60:
                phut_end -= 60
                gio_end += 1
            end_time = time(gio_end, phut_end)

            # Tạo khung giờ mới
            khung_gio_moi = KhungGio(
                lich_id=lich.id,
                startTime=start_time,
                endTime=end_time
            )
            db.session.add(khung_gio_moi)
        db.session.commit()
        return True, "Cập nhật lịch làm việc thành công!"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


# Thêm Status vào phần import ở đầu file dao.py
from app.models import Status


def get_chi_tiet_lich_by_id(lich_id):
    lich = LichLamViec.query.get(lich_id)
    if not lich:
        return None

    bacsi = BacSi.query.get(lich.bacsi_id)
    user = User.query.get(bacsi.user_id)

    # Lấy tất cả khung giờ của ngày này, sắp xếp theo thời gian
    khung_gios = KhungGio.query.filter_by(lich_id=lich_id).order_by(KhungGio.startTime).all()

    danh_sach_ca = []
    for kg in khung_gios:
        # KIỂM TRA: Khung giờ này đã có bệnh nhân nào đặt thành công chưa?
        # Theo models.py, khunggio_id là unique trong PhieuDatLich
        phieu = PhieuDatLich.query.filter_by(
            khunggio_id=kg.id,
            status=Status.Scheduled
        ).first()

        danh_sach_ca.append({
            'time': kg.startTime.strftime('%H:%M'),
            'is_booked': True if phieu else False  # Nếu có phiếu -> Đã đặt
        })

    return {
        'ten_bacsi': user.hoTen,
        'ngay_lam_viec': lich.ngayLamViec.strftime('%d/%m/%Y'),
        'raw_date': lich.ngayLamViec.strftime('%Y-%m-%d'),
        'bacsi_id': bacsi.id,
        'ca_lam_viec': danh_sach_ca
    }