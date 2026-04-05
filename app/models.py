import datetime

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

class Status(RoleEnum):
    Scheduled = 1
    Completed = 2
    Cancelled = 3


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
    soLanHuyTrongTuan= Column(Integer,default = 0)
    thoiGianMoKhoa = Column(DateTime, nullable=True)

    user = relationship('User', backref='Benhnhan', uselist=False)


class BacSi(BaseModel):
    __tablename__ = 'bacsi'
    user_id = Column(Integer, ForeignKey('user.id'),unique=True)

    chuyenKhoa = Column(String(100), nullable=False)
    trangThai = Column(Boolean, default=True)

    user = relationship('User', backref='bacsi_profile', uselist=False)

class Admin(BaseModel):
    __tablename__ = 'admin'
    user_id = Column(Integer, ForeignKey('user.id'),unique=True)
    user = relationship('User', backref='admin_profile', uselist=False)

class LichLamViec(BaseModel):
    __tablename__ = 'lichlamviec'

    bacsi_id = Column(Integer, ForeignKey('bacsi.id'), nullable=False)
    ngayLamViec = Column(Date, nullable=False)

    bac_si = relationship('BacSi', backref='LichLamViec', lazy=True)

class PhieuDatLich(BaseModel):
    __tablename__ = 'phieudatlich'

    benhnhan_id = Column(Integer, ForeignKey('benhnhan.id'), nullable=False)
    khunggio_id = Column(db.Integer, db.ForeignKey('khunggio.id'),unique=True, nullable=False)

    ngayTaoPhieu = Column(DateTime,default=datetime.datetime.now, nullable=False)
    status = Column(Enum(Status), default=Status.Scheduled,nullable=False)

    benh_nhan = relationship('BenhNhan', backref='PhieuDatLich', lazy=True)
    khung_gio = relationship('KhungGio', backref='PhieuDatLich', lazy=True)

class KhungGio(BaseModel):
    __tablename__ = 'khunggio'

    lich_id = Column(Integer, ForeignKey('lichlamviec.id'), nullable=False)

    startTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)

    lich_lam_viec = relationship('LichLamViec', backref='KhungGio', lazy=True)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # u_admin = User(
        #     username= "admin",
        #     hoTen="Nguyễn Thanh Bình",
        #     email="thanhbinhlb2505@gmail.com",
        #     gioiTinh=True,
        #     role=UserRole.ADMIN
        # )
        # u_admin.set_password('123456')
        # db.session.add(u_admin)
        # db.session.commit()

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
                    trangThai=True
                )
                db.session.add(new_doctor)

        # Lưu tất cả vào Database
        db.session.commit()