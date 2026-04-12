from datetime import datetime, time, date

from app import db, app
from sqlalchemy import Integer, String, Boolean, ForeignKey, Enum, Column,DateTime, Date, Time
from enum import Enum as RoleEnum, unique
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship, backref



class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class UserRole(RoleEnum):
    ADMIN = 1
    BENHNHAN = 2
    BACSI = 3

class TrangThaiLichHen(RoleEnum):
    Scheduled = 1
    Completed = 2
    Cancelled = 3

class TrangThaiBacSi(RoleEnum):
    HoatDong = 1
    NghiPhep = 2

class User(UserMixin, BaseModel):
    __tablename__ = 'user'

    username = Column(String(20), unique=True, nullable=False)
    hoTen = Column(String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gioiTinh = db.Column(Boolean, nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), nullable=False)

    def __str__(self):
        return self.username
    def get_id(self):
        return self.id
    def get_username(self):
        return self.username
    def set_password(self, password: str):
        self.password = generate_password_hash(password)
    def check_password(self, password: str):
        return check_password_hash(self.password, password)


class BenhNhan(BaseModel):
    __tablename__ = 'benhnhan'

    user_id = Column(Integer, ForeignKey('user.id'),unique=True, nullable=False)

    ngaySinh = Column(Date, nullable=True)
    diaChi = Column(String(50), nullable=True)
    thoiGianMoKhoa = Column(DateTime, nullable=True)
    ghiChu = Column(String(255), nullable=True)

    user = relationship('User', backref='Benhnhan', uselist=False)


class BacSi(BaseModel):
    __tablename__ = 'bacsi'
    user_id = Column(Integer, ForeignKey('user.id'),unique=True)

    chuyenKhoa = Column(String(100), nullable=False)
    avatar = Column(String(100), default="https://i.pinimg.com/originals/c6/e5/65/c6e56503cfdd87da299f72dc416023d4.jpg")

    user = relationship('User', backref='bacsi_profile', uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "hoTen": self.user.hoTen,
            "chuyenKhoa": self.chuyenKhoa,
            "avatar": self.avatar
        }

class Admin(BaseModel):
    __tablename__ = 'admin'
    user_id = Column(Integer, ForeignKey('user.id'),unique=True)
    user = relationship('User', backref='admin_profile', uselist=False)


class CaLam(BaseModel):
    __tablename__ = 'ca_lam'
    tenCa = Column(String(50), nullable=False)
    gioBatDau = Column(Time, nullable=False)
    gioKetThuc = Column(Time, nullable=False)

    danh_sach_phan_ca = relationship('PhanCa', backref='ca_lam', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tenCa": self.tenCa,
            "gioBatDau": self.gioBatDau.strftime('%H:%M'),
            "gioKetThuc": self.gioKetThuc.strftime('%H:%M'),
        }


class LichLamViec(BaseModel):
    __tablename__ = 'lich_lam_viec'

    ngayBatDau = Column(Date, nullable=False)
    ngayKetThuc = Column(Date, nullable=False)

    danh_sach_ngay = relationship('NgayLamViec', backref='lich_lam_viec', lazy=True)


class NgayLamViec(db.Model):
    __tablename__ = 'ngay_lam_viec'

    ngay = Column(Date, primary_key=True)
    id_LichLamViec = Column(Integer, ForeignKey('lich_lam_viec.id'), nullable=False)

    danh_sach_phan_ca = relationship('PhanCa', lazy=True)


class PhanCa(db.Model):
    __tablename__ = 'phan_ca'

    id_BacSi = Column(Integer, ForeignKey('bacsi.id'), primary_key=True)
    thuocNgay = Column(Date, ForeignKey('ngay_lam_viec.ngay'), primary_key=True)
    id_CaLam = Column(Integer, ForeignKey('ca_lam.id'), primary_key=True)

    trangThai = Column(Enum(TrangThaiBacSi), default=TrangThaiBacSi.HoatDong)

    bac_si = relationship('BacSi')
    # ca_lam = relationship('CaLam')

class PhieuDatLich(BaseModel):
    __tablename__ = 'phieudatlich'

    benhnhan_id = Column(Integer, ForeignKey('benhnhan.id'), nullable=False)
    khunggio_id = Column(db.Integer, db.ForeignKey('khunggio.id'),unique=True, nullable=False)

    ngayTaoPhieu = Column(DateTime,default=datetime.now, nullable=False)
    status = Column(Enum(TrangThaiLichHen), default=TrangThaiLichHen.Scheduled, nullable=False)
    cancelTime = Column(DateTime)

    user_huy_id = Column(Integer, ForeignKey('user.id'), nullable=True)

    benh_nhan = relationship('BenhNhan', backref='PhieuDatLich', lazy=True)
    khung_gio = relationship('KhungGio', backref='PhieuDatLich', lazy=True)

class KhungGio(BaseModel):
    __tablename__ = 'khunggio'

    # lich_id = Column(Integer, ForeignKey('lichlamviec.id'), nullable=False)

    startTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)

    # lich_lam_viec = relationship('LichLamViec', backref='KhungGio', lazy=True)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        ca_sang = CaLam(
            tenCa="Ca Sáng",
            gioBatDau=time(8, 0),
            gioKetThuc=time(12, 0)
        )

        # 2. Tạo ca chiều: 13:00 - 17:00
        ca_chieu = CaLam(
            tenCa="Ca Chiều",
            gioBatDau=time(13, 0),
            gioKetThuc=time(17, 0)
        )

        lich_mau = LichLamViec(
            ngayBatDau=date(2026, 4, 13),
            ngayKetThuc=date(2026, 4, 19)
        )

        db.session.add(ca_sang)
        db.session.add(ca_chieu)
        db.session.add(lich_mau)

        u_admin = User(
            username= "admin",
            hoTen="Nguyễn Thanh Bình",
            email="thanhbinhlb2505@gmail.com",
            gioiTinh=True,
            role=UserRole.ADMIN
        )
        u_admin.set_password('123456')
        db.session.add(u_admin)
        db.session.commit()

        doctors_data = [
            {
                "username": "bs_minhanh",
                "hoTen": "Nguyễn Minh Anh",
                "email": "minhanh.nguyen@gmail.com",
                "chuyenKhoa": "Nhi khoa"
            },
            {
                "username": "bs_hoangquan",
                "hoTen": "Lê Hoàng Quân",
                "email": "quan.lehoang@gmail.com",
                "chuyenKhoa": "Tim mạch"
            },
            {
                "username": "bs_phuongthao",
                "hoTen": "Trần Phương Thảo",
                "email": "thaotp.nha@gmail.com",
                "chuyenKhoa": "Răng Hàm Mặt"
            }
        ]

        for data in doctors_data:
            # Kiểm tra xem user đã tồn tại chưa để tránh lỗi trùng lặp (unique)
            exists = User.query.filter_by(username=data["username"]).first()
            if not exists:
                # Bước A: Tạo tài khoản User để đăng nhập
                new_user = User(
                    username=data["username"],
                    hoTen=data["hoTen"],
                    email=data["email"],
                    gioiTinh=True,  # Mặc định Nam/Nữ tùy bạn
                    role=UserRole.BACSI
                )
                new_user.set_password("123456")  # Mật khẩu mặc định

                db.session.add(new_user)
                db.session.flush()  # Lấy ID của user vừa tạo để gán cho bác sĩ

                # Bước B: Tạo thông tin chuyên khoa trong bảng BacSi
                new_doctor = BacSi(
                    user_id=new_user.id,
                    chuyenKhoa=data["chuyenKhoa"],
                )
                db.session.add(new_doctor)

        # Lưu tất cả vào Database
        db.session.commit()
        # 1. Lấy thông tin bệnh nhân và khung giờ để test
