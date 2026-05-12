from datetime import datetime, time, date, timedelta
from http.client import parse_headers

from sqlalchemy import func, and_, or_, false

from app import app, db
from app.models import (User, BenhNhan, BacSi, PhieuDatLich,
                        LichLamViec, TrangThaiLichHen, UserRole, CaLam,
                        NgayLamViec, PhanCa, KhungGio, TrangThaiBacSi,
                        NgayNghiBacSi, TrangThaiDuyet)

import re
import json

def commit():
    db.session.commit()

def rollback():
    db.session.rollback()

def them_benhnhan(username, hoten, email, gioitinh, password, ngaysinh=None, diachi=None):
    try:
        if User.query.filter(User.username.__eq__(username)).first():
            return False, "Username đã tồn tại!"
        
        if User.query.filter(User.email.__eq__(email)).first():
            return False, "Email đã có tài khoản!"

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
        return True, "Thêm thành công!"

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

def lay_bac_si_co_lich_lam_viec(ngay):
    """
    Lấy danh sách các bác sĩ có lịch làm việc (PhanCa) trong một ngày cụ thể
    và trạng thái là HoatDong.
    """
    bac_si_co_lich = db.session.query(BacSi).join(PhanCa, BacSi.id == PhanCa.id_BacSi)\
        .filter(PhanCa.thuocNgay == ngay, PhanCa.trangThai == TrangThaiBacSi.HoatDong)\
        .all()
    return bac_si_co_lich

def lay_bac_si_nghi_phep(ngay):
    """
    Lấy danh sách các bác sĩ có ngày nghỉ phép đã được duyệt bao gồm ngày được truyền vào.
    """
    bac_si_nghi_phep = db.session.query(BacSi).join(NgayNghiBacSi, BacSi.id == NgayNghiBacSi.bacsi_id)\
        .filter(
            NgayNghiBacSi.ngayBatDau <= ngay,
            NgayNghiBacSi.ngayKetThuc >= ngay,
            NgayNghiBacSi.trangThai == TrangThaiDuyet.DaDuyet
        ).all()
    return bac_si_nghi_phep

def tao_nghi_phep_bac_si(bacsi_id, ngay_bat_dau, ngay_ket_thuc, ly_do=None):
    ds_nghi_phep = db.session.query(NgayNghiBacSi).filter(
        NgayNghiBacSi.bacsi_id == bacsi_id,
        NgayNghiBacSi.ngayBatDau <= ngay_ket_thuc,
        NgayNghiBacSi.ngayKetThuc >= ngay_bat_dau,
        NgayNghiBacSi.trangThai != TrangThaiDuyet.TuChoi
    ).first()

    if ds_nghi_phep:
        return False, "Bác sĩ đã có lịch nghỉ phép hoặc đang chờ duyệt trong khoảng thời gian này."

    try:
        nghi_phep = NgayNghiBacSi(
            bacsi_id=bacsi_id,
            ngayBatDau=ngay_bat_dau,
            ngayKetThuc=ngay_ket_thuc,
            lyDo=ly_do,
            trangThai=TrangThaiDuyet.DaDuyet 
        )
        db.session.add(nghi_phep)

        phan_cas = db.session.query(PhanCa).filter(
            PhanCa.id_BacSi == bacsi_id,
            PhanCa.thuocNgay >= ngay_bat_dau,
            PhanCa.thuocNgay <= ngay_ket_thuc
        ).all()

        for pc in phan_cas:
            pc.trangThai = TrangThaiBacSi.NghiPhep

        db.session.commit()
        return True, "Tạo nghỉ phép thành công."
    except Exception as e:
        db.session.rollback()
        raise e

def get_list_shift():
    ds_calam = CaLam.query.all()
    return [ca.to_dict() for ca in ds_calam]

def kiem_tra_lich_truc_bac_si(bac_si_id, ngay_kham):
    lich_truc = PhanCa.query.filter_by(id_BacSi=bac_si_id, thuocNgay=ngay_kham).all()

    if not lich_truc:
        return False, "Bác sĩ không có lịch trực trong ngày này.", None

    if any(ca.trangThai == TrangThaiBacSi.NghiPhep for ca in lich_truc):
        return False, "Bác sĩ đang nghỉ phép, vui lòng chọn ngày khác.", None

    return True, "", lich_truc

def get_khung_gio_bac_si(bac_si_id, ngay_kham_str):

    ngay_kham = datetime.strptime(ngay_kham_str, '%Y-%m-%d').date()
    lich_truc = PhanCa.query.filter_by(id_BacSi=bac_si_id, thuocNgay=ngay_kham).all()
    hop_le, msg, lich_truc = kiem_tra_lich_truc_bac_si(bac_si_id, ngay_kham)
    if not hop_le:
        return {"status": "nghi_phep", "message": msg}

    ca_lam_ids = [ca.id_CaLam for ca in lich_truc]
    danh_sach_ca_lam = CaLam.query.filter(CaLam.id.in_(ca_lam_ids)).all()

    danh_sach_slot = []
    for ca in danh_sach_ca_lam:
        buoi = "sang" if "Ca Sáng" in ca.tenCa else "chieu"
        for kg in ca.danh_sach_khung_gio:
            danh_sach_slot.append({
                "gio": f"{kg.startTime.strftime('%H:%M')} - {kg.endTime.strftime('%H:%M')}",
                "buoi": buoi
            })
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
        gio_bat_dau_str = slot["gio"].split(" - ")[0]
        thoi_gian_slot = datetime.combine(ngay_kham, datetime.strptime(gio_bat_dau_str, '%H:%M').time())
        if thoi_gian_slot <datetime.now():
            slot["trang_thai"] = "dat_qua"
        else:
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
        ngay_hien_tai = date.today()
        if ngay_kham > ngay_hien_tai + timedelta(days=30):
            return False, "Bạn chỉ có thể đặt lịch trước tối đa 30 ngày.", None
        if ngay_kham < ngay_hien_tai:
            return False, "Không thể đặt lịch cho ngày trong quá khứ.", None
        gio_kham = datetime.combine(ngay_kham, start_time)
        if gio_kham <= datetime.now():
            return False, "Khung giờ đã qua, không thể đặt khung giờ này.", None

        hop_le, msg, lich_truc = kiem_tra_lich_truc_bac_si(bacsi_id, ngay_kham)
        if not hop_le:
            return False, msg, None
        benhnhan = BenhNhan.query.filter_by(user_id=current_user_id).first()
        if not benhnhan:
            return False, "Không tìm thấy hồ sơ bệnh nhân.", None
        if benhnhan.thoiGianMoKhoa:
            if datetime.now()<benhnhan.thoiGianMoKhoa:
                thoi_gian_str = benhnhan.thoiGianMoKhoa.strftime('%H:%M ngày %d/%m/%Y')
                return False, f"Tài khoản đang bị hạn chế đặt lịch đến {thoi_gian_str} do hủy lịch quá 3 lần/tuần.", None


        so_ca_da_dat = PhieuDatLich.query.filter(
            PhieuDatLich.benhnhan_id == benhnhan.id,
            PhieuDatLich.ngayKham == ngay_kham,
            PhieuDatLich.status != TrangThaiLichHen.Cancelled
        ).count()

        if so_ca_da_dat >= 2:
            return False, f"Chỉ đặt tối đa 2ca/ngày.Bạn đã đạt giới hạn: {ngay_kham.strftime('%d/%m/%Y')}.", None

        khung_gio = KhungGio.query.filter_by(startTime=start_time, endTime=end_time).first()
        if not khung_gio:
            return False, "Khung giờ khám không tồn tại hoặc nằm ngoài giờ làm việc.", None

        ca_lam_ids_cua_bac_si = [ca.id_CaLam for ca in lich_truc]
        if khung_gio.calam_id not in ca_lam_ids_cua_bac_si:
            return False, "Bác sĩ không làm việc vào ca chứa khung giờ này.", None

        trung_lich_kham = PhieuDatLich.query.filter(
            PhieuDatLich.khunggio_id == khung_gio.id,
            PhieuDatLich.ngayKham == ngay_kham,
            PhieuDatLich.status != TrangThaiLichHen.Cancelled,
            or_(
                PhieuDatLich.benhnhan_id == benhnhan.id,
                PhieuDatLich.bacsi_id == bacsi_id
                          )
        ).first()
        if trung_lich_kham:
            if trung_lich_kham.benhnhan_id == benhnhan.id:
                return False, f"Bạn đã có lịch khám khung giờ {gio_kham_str} ngay {ngay_kham.strftime('%d/%m/%Y')}.Vui lòng chọn khung giờ khác!", None
            if trung_lich_kham.bacsi_id == bacsi_id:
                return False, "Khung giờ này đã có người đặt. Vui lòng chọn giờ khác!", None
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

def count_huy_lich(benhnhan_id):
    today = datetime.now().date()
    start_week = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    end_week = datetime.combine(start_week + timedelta(days=6), datetime.max.time())
    return PhieuDatLich.query.filter(
        PhieuDatLich.benhnhan_id == benhnhan_id,
        PhieuDatLich.status == TrangThaiLichHen.Cancelled,
        PhieuDatLich.cancelTime >=start_week,
        PhieuDatLich.cancelTime <=end_week
    ).count()

def huy_lich_kham(phieu_id, current_user):
    phieu = PhieuDatLich.query.get(phieu_id)
    if not phieu:
        return False, "Không tìm thấy phiếu đặt lịch."
    if current_user.role != UserRole.ADMIN and phieu.benh_nhan.user_id != current_user.id:
        return False, "Bạn không có quyền hủy lịch khám này."
    if phieu.status == TrangThaiLichHen.Completed:
        return False, "Lịch khám đã hoàn thành, không thể hủy."
    if phieu.status == TrangThaiLichHen.Cancelled:
        return False, "Lịch khám đã được hủy trước đó."

    ngay_gio_kham = datetime.combine(phieu.ngayKham, phieu.khung_gio.startTime)
    time_con_lai = ngay_gio_kham - datetime.now()

    if time_con_lai<=timedelta(seconds=0):
        return False,"Đang trong giờ khám. Không thể hủy lịch khám."
    if time_con_lai<=timedelta(hours=1):
        return False, "Không thể hủy lịch vì còn dưới 1 giờ trước giờ khám."

    try:
        phieu.status = TrangThaiLichHen.Cancelled
        phieu.user_huy_id = current_user.id
        phieu.cancelTime = datetime.now()
        so_lan_huy = count_huy_lich(phieu.benhnhan_id)
        msg = "Hủy lịch khám thành công."
        if current_user.id==phieu.benh_nhan.user_id and so_lan_huy > 3:
            phieu.benh_nhan.thoiGianMoKhoa = datetime.now() + timedelta(hours=24)
            msg += " Lưu ý: Bạn đã hủy quá 3 lần trong tuần này, tài khoản bị hạn chế đặt lịch trong 24h tới."
        commit()
        return True, msg
    except Exception:
        rollback()
        import traceback
        traceback.print_exc()
        return False, "Có lỗi hệ thống xảy ra trong quá trình hủy lịch."

def get_lich_da_dat(user_id):
    benh_nhan = BenhNhan.query.filter_by(user_id=user_id).first()
    if not benh_nhan:
        return []
    ds_phieu = db.session.query(PhieuDatLich, BacSi, User, KhungGio) \
        .join(BacSi, PhieuDatLich.bacsi_id == BacSi.id) \
        .join(User, BacSi.user_id == User.id) \
        .join(KhungGio, PhieuDatLich.khunggio_id == KhungGio.id) \
        .filter(PhieuDatLich.benhnhan_id == benh_nhan.id) \
        .order_by(PhieuDatLich.ngayKham.asc()) \
        .all()

    results = []
    for phieu, bacsi, user_bs, khung_gio in ds_phieu:
        ngay_kham = phieu.ngayKham
        if isinstance(ngay_kham, str):
            ngay_kham = datetime.strptime(ngay_kham, '%Y-%m-%d').date()

        ngay_gio = datetime.combine(ngay_kham, khung_gio.startTime).isoformat()

        results.append({
            "id": phieu.id,
            "ten_BS": user_bs.hoTen,
            "ngay_kham_str": ngay_kham.strftime('%d/%m/%Y'),
            "gio_kham_str": f"{khung_gio.startTime.strftime('%H:%M')} - {khung_gio.endTime.strftime('%H:%M')}",
            "status": phieu.status.name,
            "ngay_gio_kham": ngay_gio,
        })
    return results

def get_benh_nhan_by_id(bn_id):
    return BenhNhan.query.get(bn_id)
def get_all_benh_nhan():
    benh_nhans = BenhNhan.query.all()
    ket_qua = []
    for bn in benh_nhans:
        # Tận dụng hàm count_huy_lich đã có trong dao.py để đếm số lần hủy tuần này
        so_lan_huy = count_huy_lich(bn.id)

        ket_qua.append({
            'id': bn.id,
            'ho_ten': bn.user.hoTen,
            'email': bn.user.email,
            'gioi_tinh': "Nam" if bn.user.gioiTinh else "Nữ",
            'ngay_sinh': bn.ngaySinh.strftime('%d/%m/%Y') if bn.ngaySinh else "Chưa cập nhật",
            'so_lan_huy_tuan': so_lan_huy
        })
    return ket_qua

def cap_nhat_trang_thai_lich_kham():
    with app.app_context():
        phieu_cho = db.session.query(PhieuDatLich, KhungGio)\
        .join(KhungGio, PhieuDatLich.khunggio_id == KhungGio.id)\
        .filter(PhieuDatLich.status == TrangThaiLichHen.Scheduled).all()
        flag = False
        for phieu, khung_gio in phieu_cho:
            end_time = datetime.combine(phieu.ngayKham,khung_gio.endTime)
            if datetime.now() > end_time:
                phieu.status = TrangThaiLichHen.Completed
                flag = True
        if flag:
            try:
                commit()
            except Exception as e:
                rollback()
                print(f"Lỗi cập nhật trạng thái lịch khám: {e}")

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
    ds_ngay_lam_viec = db.session.query(NgayLamViec).filter(
        NgayLamViec.ngay >= ngay_bat_dau,
        NgayLamViec.ngay <= ngay_ket_thuc
    ).order_by(NgayLamViec.ngay).all()

    return ds_ngay_lam_viec

def lay_danh_sach_phan_ca(ngay):
    return db.session.query(PhanCa).filter(
        PhanCa.thuocNgay == ngay,
        PhanCa.trangThai == TrangThaiBacSi.HoatDong
    ).all()

def lay_lich_tuan(ngay_bat_dau, ngay_ket_thuc):
    """
    lay_lich_tuan(date(2026, 5, 4), date(2026, 5, 10))
    
    Returns:
        dict:
            {
                "T2": {"1": [1, 2], "2": [1]},   # key = id CaLam (string)
                "T3": { ... },
                ...           # chỉ có các ngày có phân ca
            }
    """

    ds_ngay_lam_viec = lay_ngay_lam_viec(ngay_bat_dau, ngay_ket_thuc)

    day_map = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}
    lich_tuan = {}

    for ngay_lam_viec in ds_ngay_lam_viec:
        thu = day_map[ngay_lam_viec.ngay.weekday()]
        lich_tuan[thu] = {}

        ds_phan_ca = lay_danh_sach_phan_ca(ngay_lam_viec.ngay)

        for pc in ds_phan_ca:
            ca_id = pc.id_CaLam
            bs_id = pc.id_BacSi

            if ca_id not in lich_tuan[thu]:
                lich_tuan[thu][ca_id] = []

            lich_tuan[thu][ca_id].append(bs_id)
    return lich_tuan

def tao_lich_lam_viec(ngay_bat_dau, ngay_ket_thuc):
    lich_da_tao = db.session.query(LichLamViec).filter(
        LichLamViec.ngayBatDau <= ngay_ket_thuc,
        LichLamViec.ngayKetThuc >= ngay_bat_dau
    ).first()

    if lich_da_tao:
        return False, f"Đã tồn tại lịch từ {lich_da_tao.ngayBatDau.strftime('%d/%m/%Y')} đến {lich_da_tao.ngayKetThuc.strftime('%d/%m/%Y')})."

    try:
        lich_moi = LichLamViec(ngayBatDau=ngay_bat_dau, ngayKetThuc=ngay_ket_thuc)
        db.session.add(lich_moi)

        db.session.flush()
        return True, lich_moi

    except Exception as e:
        db.session.rollback()
        raise e

def tao_ngay_lam_viec(ngay, id_lichlamviec):
    lich = db.session.get(LichLamViec, id_lichlamviec)
    if not lich:
        return False, "Lịch làm việc không tồn tại."
    if ngay < lich.ngayBatDau or ngay > lich.ngayKetThuc:
        return False, "Ngày làm việc phải nằm trong phạm vi của lịch làm việc."

    try:
        ngay_moi = NgayLamViec(
            ngay=ngay,
            id_LichLamViec=id_lichlamviec
        )

        db.session.add(ngay_moi)
        db.session.flush()

        return True, ngay_moi

    except Exception as e:
        db.session.rollback()
        raise e

def tao_phan_ca(id_bacsi, id_calam, thuoc_ngay):
    try:
        if not BacSi.query.get(id_bacsi):
            return False, "ID bác sĩ không tồn tại!"

        if not CaLam.query.get(id_calam):
            return False, "ID ca làm không tồn tại!"

        if not NgayLamViec.query.get(thuoc_ngay):
            return False, "Ngày làm việc không tồn tại!"

        pc_ton_tai = PhanCa.query.filter(
            PhanCa.id_BacSi == id_bacsi,
            PhanCa.id_CaLam == id_calam,
            PhanCa.thuocNgay == thuoc_ngay
        ).first()

        if pc_ton_tai:
            return False, "Bác sĩ này đã được phân ca này trong ngày rồi."

        nghi_phep = NgayNghiBacSi.query.filter(
            NgayNghiBacSi.bacsi_id == id_bacsi,
            NgayNghiBacSi.trangThai == TrangThaiDuyet.DaDuyet,
            NgayNghiBacSi.ngayBatDau <= thuoc_ngay,
            NgayNghiBacSi.ngayKetThuc >= thuoc_ngay
        ).first()

        trang_thai_pc = TrangThaiBacSi.NghiPhep if nghi_phep else TrangThaiBacSi.HoatDong

        moi = PhanCa(
            id_BacSi=id_bacsi,
            id_CaLam=id_calam,
            thuocNgay=thuoc_ngay,
            trangThai=trang_thai_pc
        )

        db.session.add(moi)
        db.session.flush()
        return True, moi

    except Exception as e:
        db.session.rollback()
        return False, "Có lỗi xảy ra trong quá trình lưu dữ liệu."

def tao_lich(lich_tuan, ngay_bat_dau, ngay_ket_thuc):
    success, output = tao_lich_lam_viec(ngay_bat_dau, ngay_ket_thuc)
    if not success:
        return False, output
    lich_moi = output

    day_map = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}

    current_date = ngay_bat_dau
    while current_date <= ngay_ket_thuc:
        thu_cua_ngay = day_map[current_date.weekday()]

        if thu_cua_ngay in lich_tuan:

            success, output = tao_ngay_lam_viec(current_date, lich_moi.id)
            if not success:
                return False, output
            ngay_moi = output

            danh_sach_ca = lich_tuan[thu_cua_ngay]

            for ca_id_str, bac_si_ids in danh_sach_ca.items():
                ca_id = ca_id_str

                for bs_id in bac_si_ids:
                    success, output = tao_phan_ca(bs_id, ca_id, ngay_moi.ngay)

                    if not success:
                        return False, output

        current_date += timedelta(days=1)

    commit()
    return True, "Tạo lịch thành công!"


if __name__ == '__main__':
    with app.app_context():
        lich = lay_lich_tuan(date(2026, 4, 28), date(2026, 5, 3))
        print(lich)
        print(len(lich))