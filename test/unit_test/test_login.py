from test.unit_test.test_base import test_session, test_app
from app.models import User
from app.dao import them_benhnhan, get_user_by_email_username
import pytest

@pytest.fixture
def setup_user(test_session):
    # Tạo sẵn một tài khoản hợp lệ để test đăng nhập
    them_benhnhan(
        username='thanhbinh',
        password='Abc1234@',
        email='thanhbinhlb2505@gmail.com',
        hoten='Nguyễn Thanh Bình',
        gioitinh=True
    )
    # Trả về các thông tin cần thiết để sử dụng trong test case
    return {
        'username': 'thanhbinh',
        'email': 'thanhbinhlb2505@gmail.com',
        'password': 'Abc1234@'
    }

def test_login_success_by_username(test_session, setup_user):
    user = get_user_by_email_username(setup_user['username'])
    assert user is not None
    assert user.username == setup_user['username']
    assert user.check_password(setup_user['password']) is True

def test_login_success_by_email(test_session, setup_user):
    user = get_user_by_email_username(setup_user['email'])
    assert user is not None
    assert user.email == setup_user['email']
    assert user.check_password(setup_user['password']) is True

@pytest.mark.parametrize("identifier", [
    "nguyen",        # Username không tồn tại
    "notexist@gmail.com",   # Email không tồn tại
    "thanhbi",              # Gõ thiếu username
    "",                     # Để trống
])
def test_login_fail(test_session, setup_user, identifier):
    user = get_user_by_email_username(identifier)

    assert user is None

@pytest.mark.parametrize("password", [
    "Matkhausai123@",      # Mật khẩu hoàn toàn sai
    "aBc1234@",      # Sai chữ hoa/thường (Phân biệt hoa thường),    # Có khoảng trắng thừa
    "",                       # Để trống mật khẩu
])

def test_login_fail_password_by_username(test_session, setup_user, password):
    user = get_user_by_email_username(setup_user['username'])
    assert user is not None
    assert user.check_password(password) is False
