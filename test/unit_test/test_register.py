from test_base import test_session, test_app, test_client
from app.models import User, BenhNhan, UserRole
from app.dao import them_benhnhan
from datetime import datetime, date, timedelta
import pytest
from contextlib import contextmanager
from flask import template_rendered

# ==========================================
# TEST: them_benh_nhan
# ==========================================
def test_them_benh_nhan_thanh_cong(test_session):
    ngaysinh = datetime.strptime("2005-03-10", "%Y-%m-%d").date()

    success, _ = them_benhnhan(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh=True,
        ngaysinh=ngaysinh,
        diachi="Gia Lai"
    )

    assert success is True

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

def test_them_benh_nhan_username_da_ton_tai(test_session):
    ngaysinh = datetime.strptime("2005-03-10", "%Y-%m-%d").date()

    u1 = User(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoTen='Do Van Quan',
        gioiTinh=True,
        role=UserRole.BENHNHAN
    )
    test_session.add(u1)
    test_session.flush()
    b1 = BenhNhan(
        user_id=u1.id,
        ngaySinh=ngaysinh,
        diaChi="Gia Lai"
    )
    test_session.add(b1)
    test_session.commit()

    success, message = them_benhnhan(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh=True,
        ngaysinh=datetime.strptime("2005-03-10", "%Y-%m-%d").date(),
        diachi="Gia Lai"
    )
    assert success is False
    assert message == 'Username đã tồn tại!'

def test_them_benh_nhan_email_da_ton_tai(test_session):
    ngaysinh = datetime.strptime("2005-03-10", "%Y-%m-%d").date()

    u1 = User(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoTen='Do Van Quan',
        gioiTinh=True,
        role=UserRole.BENHNHAN
    )
    test_session.add(u1)
    test_session.flush()
    b1 = BenhNhan(
        user_id=u1.id,
        ngaySinh=ngaysinh,
        diaChi="Gia Lai"
    )
    test_session.add(b1)
    test_session.commit()

    success, message = them_benhnhan(
        username='user2',
        password='Abcd123@',
        email='123@gmail.com',
        hoten='Do Van Quan',
        gioitinh=True,
        ngaysinh=datetime.strptime("2005-03-10", "%Y-%m-%d").date(),
        diachi="Gia Lai"
    )
    assert success is False
    assert message == 'Email đã có tài khoản!'
    
# ==========================================
# TEST: marshmallow
# ==========================================
@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

@pytest.mark.parametrize('username, err_msg', [
    (None, 'Username không được để trống!'),
    ('', 'Username phải từ 5 đến 20 kí tự!'),
    ('abc', 'Username phải từ 5 đến 20 kí tự!'),
    ('ab'*20, 'Username phải từ 5 đến 20 kí tự!'),
    ('      ', 'Username không được chứa khoảng trắng!'),
    ('abc abc', 'Username không được chứa khoảng trắng!')
])
def test_register_username_invalid(test_app, test_client, username, err_msg, mocker):
    data = {
        'username': username,
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        # templates[0][0] là tên file template ('register.html')
        # templates[0][1] là dictionary chứa các biến truyền vào file đó
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        # KIỂM TRA TRỰC TIẾP BIẾN err_msg TẠI ĐÂY
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

@pytest.mark.parametrize('password, err_msg', [
    (None, 'Password không được để trống!'),
    ('Abc123@', 'Mật khẩu phải ít nhất 8 kí tự!'),
    ('Ab1@'*100, 'Mật khẩu không được vượt quá 255 kí tự!'),
    ('Abc123@ Abc123@', 'Mật khẩu không được chứa khoảng trắng!'),
    (' '*8, 'Mật khẩu không được chứa khoảng trắng!'),
    ('Abcdefgh@', 'Mật khẩu phải chứa ít nhất một số!'),
    ('ABC123@@', 'Mật khẩu phải chứa ít nhất một chữ thường!'),
    ('abc123@@', 'Mật khẩu phải chứa ít nhất một chữ hoa!'),
    ('Abc12345', 'Mật khẩu phải chứa ít nhất một kí tự đặc biệt!')
])
def test_register_password_invalid(test_app, test_client, password, err_msg, mocker):
    data = {
        'username': 'user1',
        'password': password,
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

@pytest.mark.parametrize('hoten, err_msg', [
    (None, 'Họ tên không được để trống!'),
    ('A'*51, 'Họ tên không được vượt quá 50 ký tự!'),
    ('   ', 'Họ tên không được để trống!'),
    ('', 'Họ tên không được để trống!')
])
def test_register_hoten_invalid(test_app, test_client, hoten, err_msg, mocker):
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': hoten,
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

@pytest.mark.parametrize('email, err_msg', [
    (None, 'Email không được để trống!'),
    ('A'*100 + '@gmail.com', 'Email không được vượt quá 100 ký tự!'),
    ('   ', 'Email không hợp lệ!'),
    ('', 'Email không hợp lệ!'),
    ('do van quan@gmail.com', 'Email không hợp lệ!')
])
def test_register_email_invalid(test_app, test_client, email, err_msg, mocker):
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': email,
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

@pytest.mark.parametrize('gioitinh, err_msg', [
    (None, 'Giới tính không được để trống!'),
    ('other', 'Giới tính không hợp lệ!')
])
def test_register_gioitinh_invalid(test_app, test_client, gioitinh, err_msg, mocker):
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': gioitinh,
        'ngaysinh': '2005-03-10',
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

tomorrow = date.today() + timedelta(days=1)
@pytest.mark.parametrize('ngaysinh, err_msg', [
   ('2005/03/10', 'Ngày sinh không hợp lệ!'),
   ('nfjhfuhf', 'Ngày sinh không hợp lệ!'),
    (tomorrow.strftime('%Y-%m-%d'), 'Ngày sinh không được là hôm nay hoặc tương lai!'),
    (date.today().replace(year=date.today().year - 151).strftime('%Y-%m-%d'), 'Ngày sinh quá xa trong quá khứ!')
])
def test_register_ngaysinh_invalid(test_app, test_client, ngaysinh, err_msg, mocker):
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': ngaysinh,
        'diachi': "Gia Lai"
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == err_msg

        mock_them_benh_nhan.assert_not_called()

def test_register_diachi_invalid(test_app, test_client, mocker):
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': 'a'*256
    }
    with captured_templates(test_app) as templates:
        mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan')
        res = test_client.post('/register', data=data)
        
        template_name, context = templates[0]
        
        assert res.status_code == 200
        assert template_name.name == 'register.html'
        assert context['err_msg'] == "Địa chỉ không được vượt quá 255 ký tự!"

        mock_them_benh_nhan.assert_not_called()

def test_register_success(test_app, test_client, mocker):
    birth_day = date.today() - timedelta(days=365 * 18)
    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': birth_day.strftime('%Y-%m-%d'),
        'diachi': "Gia Lai"
    }
    mock_them_benh_nhan = mocker.patch('app.dao.them_benhnhan', return_value=(True, "Thêm thành công"))
    res = test_client.post('/register', data=data)

    assert res.status_code == 302
    assert '/login' in res.location
    mock_them_benh_nhan.assert_called_with(
        'user1',                
        'Do Van Quan',          
        '123@gmail.com',        
        True,                   
        'Abcd123@',             
        ngaysinh=birth_day,     
        diachi="Gia Lai"        
    )

# ==========================================
# INTERGRATION TESTS
# ==========================================
def test_integration_register_success(test_client, test_session):
    ngaysinh = datetime.strptime("2005-03-10", "%Y-%m-%d").date()

    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Do Van Quan',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': ngaysinh.strftime('%Y-%m-%d'),
        'diachi': 'Gia Lai'
    }
    res = test_client.post('/register', data=data)
    
    assert res.status_code == 302
    assert '/login' in res.location
    
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

def test_integration_register_duplicate_username(test_client, test_session):
    u1 = User(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoTen='Do Van Quan',
        gioiTinh=True,
        role=UserRole.BENHNHAN
    )
    test_session.add(u1)
    test_session.commit()

    data = {
        'username': 'user1',
        'password': 'Abcd123@',
        'hoten': 'Nguoi Dung Moi',
        'email': 'moi@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': 'Gia Lai'
    }
    
    res = test_client.post('/register', data=data)
    
    assert res.status_code == 200 
    
    html_text = res.data.decode('utf-8')
    assert 'Username đã tồn tại!' in html_text

def test_integration_register_duplicate_email(test_client, test_session):
    u1 = User(
        username='user1',
        password='Abcd123@',
        email='123@gmail.com',
        hoTen='Do Van Quan',
        gioiTinh=True,
        role=UserRole.BENHNHAN
    )
    test_session.add(u1)
    test_session.commit()

    data = {
        'username': 'user2',
        'password': 'Abcd123@',
        'hoten': 'Nguoi Dung Moi',
        'email': '123@gmail.com',
        'gioitinh': 'male',
        'ngaysinh': '2005-03-10',
        'diachi': 'Gia Lai'
    }
    
    res = test_client.post('/register', data=data)
    
    assert res.status_code == 200 
    
    html_text = res.data.decode('utf-8')
    assert 'Email đã có tài khoản!' in html_text
