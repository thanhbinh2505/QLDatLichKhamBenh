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
    danh_sach_khung_gio = relationship('KhungGio', backref='ca_lam', lazy=True)

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

class PhieuDatLich(BaseModel):
    __tablename__ = 'phieudatlich'

    benhnhan_id = Column(Integer, ForeignKey('benhnhan.id'), nullable=False)
    khunggio_id = Column(Integer, ForeignKey('khunggio.id'), nullable=False)
    bacsi_id = Column(Integer, ForeignKey('bacsi.id'), nullable=False)

    ngayTaoPhieu = Column(DateTime,default=datetime.now, nullable=False)
    status = Column(Enum(TrangThaiLichHen), default=TrangThaiLichHen.Scheduled, nullable=False)
    cancelTime = Column(DateTime)
    ngayKham = Column(Date, nullable=False)

    user_huy_id = Column(Integer, ForeignKey('user.id'), nullable=True)

    benh_nhan = relationship('BenhNhan', backref='PhieuDatLich', lazy=True)
    khung_gio = relationship('KhungGio', backref='PhieuDatLich', lazy=True)

class KhungGio(BaseModel):
    __tablename__ = 'khunggio'

    startTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    calam_id = Column(Integer, ForeignKey('ca_lam.id'), nullable=False)

    def __str__(self):
        return f"{self.startTime.strftime('%H:%M')} - {self.endTime.strftime('%H:%M')}"

    def to_dict(self):
        return {
            "id": self.id,
            "startTime": self.startTime.strftime('%H:%M'),
            "endTime": self.endTime.strftime('%H:%M'),
            "label": f"{self.startTime.strftime('%H:%M')} - {self.endTime.strftime('%H:%M')}"
        }

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        from datetime import datetime, timedelta, date, time
        from werkzeug.security import generate_password_hash
        import random


        # Tùy thuộc vào project của bạn, hãy import db và các Models ở đây
        # from your_application import db
        # from your_models import User, Admin, BenhNhan, BacSi, CaLam, LichLamViec, NgayLamViec, PhanCa, UserRole, TrangThaiBacSi

        def create_mock_data():
            print("Bắt đầu tạo dữ liệu mẫu...")
            default_password = '123456'
            # 4. TẠO CA LÀM (Sáng, Chiều)
            print("Đang tạo Ca làm...")
            ca_sang = CaLam(tenCa='Ca Sáng', gioBatDau=time(8, 0), gioKetThuc=time(12, 00))
            ca_chieu = CaLam(tenCa='Ca Chiều', gioBatDau=time(13, 0), gioKetThuc=time(17, 0))
            db.session.add_all([ca_sang, ca_chieu])
            db.session.flush()
            ca_lam_list = [ca_sang, ca_chieu]
            danh_sach_gio = [
                ("08:00", "08:30"), ("08:30", "09:00"), ("09:00", "09:30"), ("09:30", "10:00"),
                ("10:00", "10:30"), ("10:30", "11:00"), ("11:00", "11:30"), ("11:30", "12:00"),
                ("13:00", "13:30"), ("13:30", "14:00"), ("14:00", "14:30"), ("14:30", "15:00"),
                ("15:00", "15:30"), ("15:30", "16:00"), ("16:00", "16:30"), ("16:30", "17:00")
            ]

            for start_str, end_str in danh_sach_gio:
                start_t = datetime.strptime(start_str, "%H:%M").time()
                end_t = datetime.strptime(end_str, "%H:%M").time()

                calam_id_hien_tai = ca_sang.id if start_t < time(12, 0) else ca_chieu.id

                kg = KhungGio(startTime=start_t, endTime=end_t, calam_id=calam_id_hien_tai)
                db.session.add(kg)

            db.session.flush()
            # 1. TẠO 2 ADMIN
            print("Đang tạo Admin...")
            for i in range(1, 3):
                user = User(
                    username=f'admin_{i}',
                    hoTen=f'Quản trị viên {i}',
                    email=f'admin{i}@hospital.com',
                    gioiTinh=True,
                    role=UserRole.ADMIN
                )

                user.set_password(default_password)
                db.session.add(user)
                db.session.flush()  # Flush để lấy user.id

                admin = Admin(user_id=user.id)
                db.session.add(admin)

            # 2. TẠO 10 BỆNH NHÂN
            print("Đang tạo Bệnh nhân...")
            for i in range(1, 11):
                user = User(
                    username=f'benhnhan_{i}',
                    hoTen=f' Bệnh Nhân {i}',
                    email=f'benhnhan{i}@gmail.com',
                    gioiTinh=random.choice([True, False]),
                    role=UserRole.BENHNHAN
                )
                user.set_password(default_password)

                db.session.add(user)
                db.session.flush()

                benh_nhan = BenhNhan(
                    user_id=user.id,
                    ngaySinh=date(1980 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28)),
                    diaChi=f'Số {i} Đường ABC, Quận {random.randint(1, 10)}, TP.HCM'
                )
                db.session.add(benh_nhan)

            # 3. TẠO 10 BÁC SĨ
            print("Đang tạo Bác sĩ...")
            chuyen_khoa_list = ['Nhi khoa', 'Tim mạch', 'Răng Hàm Mặt', 'Thần Kinh', 'Nhãn khoa', 'Đa khoa tổng quát']
            danh_sach_bac_si = []

            for i in range(1, 11):
                user = User(
                    username=f'bacsi_{i}',
                    hoTen=f'Bác Sĩ {i}',
                    email=f'bacsi{i}@hospital.com',
                    gioiTinh=random.choice([True, False]),
                    role=UserRole.BACSI
                )
                user.set_password(default_password)
                db.session.add(user)
                db.session.flush()

                bac_si = BacSi(
                    user_id=user.id,
                    chuyenKhoa=random.choice(chuyen_khoa_list)
                )
                db.session.add(bac_si)
                danh_sach_bac_si.append(bac_si)

            # 5. TẠO LỊCH LÀM VIỆC CHO 1 THÁNG TỚI
            print("Đang tạo Lịch làm việc và Phân ca...")
            today = date.today()
            next_month = today + timedelta(days=30)

            lich_lam_viec = LichLamViec(ngayBatDau=today, ngayKetThuc=next_month)
            db.session.add(lich_lam_viec)
            db.session.flush()

            # Tạo các ngày làm việc và phân ca cho từng ngày
            for i in range(40):  # 0 đến 30 ngày
                current_date = today + timedelta(days=i)

                # Tạo bản ghi Ngày Làm Việc
                ngay_lam_viec = NgayLamViec(ngay=current_date, id_LichLamViec=lich_lam_viec.id)
                db.session.add(ngay_lam_viec)
                db.session.flush()

                # Phân ca ngẫu nhiên cho các bác sĩ trong ngày hôm đó
                for bs in danh_sach_bac_si:
                    # Random xem bác sĩ này hôm nay làm mấy ca (0 = nghỉ, 1 = làm 1 ca, 2 = làm cả ngày)
                    so_ca_lam = random.randint(0, 2)

                    if so_ca_lam > 0:
                        # Random chọn ca (nếu làm 1 ca thì chọn ngẫu nhiên sáng/chiều, 2 ca thì chọn cả 2)
                        ca_duoc_chon = random.sample(ca_lam_list, so_ca_lam)

                        for ca in ca_duoc_chon:
                            phan_ca = PhanCa(
                                id_BacSi=bs.id,
                                thuocNgay=ngay_lam_viec.ngay,
                                id_CaLam=ca.id,
                                trangThai=TrangThaiBacSi.HoatDong
                            )
                            db.session.add(phan_ca)

            # LƯU VÀO DATABASE
            try:
                db.session.commit()
                print("Đã tạo dữ liệu thành công! 2 Admin, 10 Bệnh nhân, 10 Bác sĩ và 1 tháng lịch làm việc.")
            except Exception as e:
                db.session.rollback()
                print(f"Có lỗi xảy ra: {e}")

        # Chạy hàm (Đảm bảo chạy trong context của Flask)
        # with app.app_context():
        create_mock_data()
