from test_base import test_session, test_app, test_client
from app.models import User, BenhNhan, UserRole
from app.dao import them_benhnhan
from datetime import datetime
import pytest

def test_success(test_session):
    ngaysinh = datetime.strptime("2005-03-10", "%Y-%m-%d").date()

    them_benhnhan(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh=True,
        ngaysinh=ngaysinh,
        diachi="Gia Lai"
    )

    u = User.query.filter(User.username.__eq__('user1')).first()
    benhnhan = BenhNhan.query.filter(BenhNhan.user_id == u.id).first()

    assert u is not None
    assert u.hoTen == 'Do Van Quan'
    assert u.email == '123@gmail.com'
    assert u.role == UserRole.BENHNHAN
    assert u.gioiTinh is True
    assert u.check_password(password='Abcd123@')
    assert benhnhan.ngaySinh == ngaysinh
    assert benhnhan.diaChi == 'Gia Lai'
    assert benhnhan.thoiGianMoKhoa == None

@pytest.mark.parametrize('password', [
    "Aa1@567",
    "",
    "Password@!",
    "PASSWORD@123",
    "password@123",
    "Password123",
    "        ",
    "12345678",
    "abcdefgh",
    "ABCDEFGH",
    "!@#$%^&*",
])
def test_invalid_password(password, test_session):
    with pytest.raises(ValueError):
        them_benhnhan(
            username='user123',
            password=password,
            email='123@gmail.com',
            hoten='Do Van Quan',
            gioitinh=True
        )

@pytest.mark.parametrize("username", [
    'a'*4, 'a'*2
])
def test_invalid_username(test_session, username):
    with pytest.raises(ValueError):
        them_benhnhan(
            username=username,
            password='Password123@',
            email='123@gmail.com',
            hoten='Do Van Quan',
            gioitinh=True
        )

def test_username_exsited(test_session):
    them_benhnhan(
        username='user1',
        password='Password123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh = True
    )

    with pytest.raises(ValueError):
        them_benhnhan(
            username='user1',
            password='Password1234@',
            email='email_khac@gmail.com',
            hoten='Do Van A',
            gioitinh = False
        )

def test_email_registered(test_session):
    them_benhnhan(
        username='user1',
        password='Password123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh = True
    )

    with pytest.raises(ValueError):
        them_benhnhan(
            username='user2',
            password='Password1234@',
            email='123@gmail.com',
            hoten='Do Van A',
            gioitinh = False
        )

@pytest.mark.parametrize("email", [
    "nguyenvanagmail.com",
    "user@.com",
    "@gmail.com",
    "user@gmail",
    "user @gmail.com",
])
def test_invalid_email(test_session, email):
    with pytest.raises(ValueError):
        them_benhnhan(
            username='user1',
            password='Password123@',
            email=email,
            hoten='Do Van Quan',
            gioitinh=True
        )

# if __name__ == '__main__':
