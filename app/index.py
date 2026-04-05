from flask import render_template, request, url_for
from werkzeug.utils import redirect
from datetime import datetime
from flask_login import login_user, logout_user, login_required
from app import app, dao, login
from app.models import UserRole

@app.route('/')
def index():
    doctors = dao.get_list_doctor()
    return render_template('index.html', doctors=doctors)

@app.route('/admin')
def admin_login():
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login_process():
    error_msg = ""
    if request.method == ('POST'):
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)
            if user.role == UserRole.ADMIN:
                return redirect('/admin')
            elif user.role == UserRole.BACSI:
                return redirect('/bacsi')
            elif user.role == UserRole.BENHNHAN:
                return redirect('/')
        else:
            error_msg = "Tài khoản hoặc mật khẩu không chính xác!"

    return render_template('login.html', error=error_msg)

@app.route('/register', methods=["get", "post"])
def register():
    err_msg = ""
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        hoten = request.form.get("hoten")
        gioitinh_form = request.form.get("gioitinh")

        if gioitinh_form not in ['male', 'female']:
            err_msg = "Vui lòng chọn giới tính!"
            return render_template('register.html', err_msg=err_msg)

        gioitinh = True if gioitinh_form == 'male' else False

        email = request.form.get("email")

        ngaysinh_form = request.form.get("ngaysinh")
        print(ngaysinh_form)
        ngaysinh = None
        if ngaysinh_form:
            try:
                ngaysinh = datetime.strptime(ngaysinh_form, "%Y-%m-%d").date()
                print(ngaysinh)
            except ValueError:
                err_msg = "Định dạng ngày sinh không hợp lệ!"
                return render_template('register.html', err_msg=err_msg)

        diachi = request.form.get("diachi")

        try:

            if dao.them_benhnhan(username, hoten, email, gioitinh, password,
                                    ngaysinh=ngaysinh, diachi=diachi):
                return redirect(url_for('login_process'))
        except ValueError as e:
            err_msg = str(e)
        except Exception as e:
            err_msg = "Có lỗi xảy ra. Vui lòng thử lại sau!"
    return render_template('register.html', err_msg=err_msg)

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=5000)
