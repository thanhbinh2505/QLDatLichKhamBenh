import traceback

from app import app, db
from app.models import User, BenhNhan
from functools import wraps
import json
import os
import hashlib

def tao_user(username, hoten, email, gioitinh, password, role):
    user = User(username=username,
                hoTen=hoten,
                email=email,
                gioiTinh=gioitinh,
                password=str(hashlib.md5(password.strip().encode("utf-8")).hexdigest()),
                role=role
                )
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
        print(e)
        db.session.rollback()
        return None