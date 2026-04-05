from app import app, db
from app.models import User, BenhNhan, UserRole, BacSi
import re
import json

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