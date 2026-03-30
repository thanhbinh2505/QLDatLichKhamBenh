
from app import db, app
from sqlalchemy import Integer, String, Boolean, ForeignKey, Enum, DateTime
from enum import Enum as RoleEnum, unique
from flask_login import UserMixin
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship, backref

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(Integer, primary_key=True, autoincrement=True)

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

    username = db.Column(String(20), unique=True, nullable=False)
    hoTen = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gioiTinh = db.Column(Boolean, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(Enum(UserRole), nullable=False)

    def __str__(self):
        return self.username
    def get_id(self):
        return self.id
    def get_username(self):
        return self.username
    def set_password(self, password: str):
        self.password = generate_password_hash(password)

class BenhNhan(BaseModel):
    __tablename__ = 'benhnhan'


    ngaySinh = db.Column(db.Date, nullable=True)
    diaChi = db.Column(db.String(50), nullable=True)
    soLanHuyTrongTuan= db.Column(Integer, default=0)
    thoiGianMoKhoa = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    phieu_dat_lich = relationship('PhieuDatLich', backref='BenhNhan', lazy=True)


class BacSi(BaseModel):
    __tablename__ = 'bacsi'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    chuyenKhoa = db.Column(db.String(100), nullable=False)
    trangThai = db.Column(db.Boolean, default=True)

    khung_gio = relationship('KhungGio', backref='BacSi', lazy=True)

class Admin(BaseModel):
    __tablename__ = 'admin'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class KhungGio(BaseModel):
    __tablename__ = 'khunggio'

    date = db.Column(db.Date, nullable=False)
    startTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    isBooked = db.Column(db.Boolean, default=False)

    bacsi_id = db.Column(db.Integer, db.ForeignKey('bacsi.id'), nullable=False)

    phieu_dat_lich = db.relationship('PhieuDatLich', backref='khunggio', uselist=False, lazy=True)

class PhieuDatLich(BaseModel):
    __tablename__ = 'phieudatlich'

    ngayTaoPhieu = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(Status), default=Status.Scheduled)

    benhNhan_id = db.Column(Integer, ForeignKey('benhnhan.id'), nullable=False)
    khungGio_id = db.Column(db.Integer, db.ForeignKey('khunggio.id'), nullable=False)
    def get_status(self):
        return self.status



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

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