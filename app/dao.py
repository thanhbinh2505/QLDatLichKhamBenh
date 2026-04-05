
from app import app, db
from app.models import User, BenhNhan, BacSi

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