from flask import render_template, request, url_for, jsonify
from sqlalchemy.testing.exclusions import succeeds_if
from werkzeug.utils import redirect
from datetime import datetime
from flask_login import login_user, logout_user, login_required, current_user
from app import app, dao, login
from app.models import UserRole

@app.route('/')
def index():
    doctors = dao.get_list_doctor()
    return render_template('index.html', doctors=doctors)

@app.route('/admin')
@login_required
def admin_login():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')
    danh_sach_lich = dao.get_so_ca_lam()
    ds_bac_si = dao.get_list_doctor()

    return render_template('admin.html', danh_sach_lich=danh_sach_lich, ds_bac_si=ds_bac_si)

@app.route('/api/admin/tao-lich', methods=['POST'])
@login_required
def admin_tao_lich():
    if current_user.role != UserRole.ADMIN :
        return jsonify({'error': False, 'msg': 'Bạn không có quyền thao tác!'})
    data = request.json
    bacsi_id= data.get('bacsi_id')
    ngay_lam_viec = data.get('ngay_lam_viec')
    danh_sach_gio = data.get('danh_sach_gio')

    if  not bacsi_id or not ngay_lam_viec or not danh_sach_gio:
        return jsonify({'success': False, 'msg': 'Điền đầy đủ thông tin'})
    success, msg = dao.add_schedule(bacsi_id,danh_sach_gio, ngay_lam_viec, )
    return jsonify({'success': success, 'msg': msg})

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

@app.route('/logout')
@login_required
def logout_process():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=["get", "post"])
def register():
    err_msg = ""
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        hoten = request.form.get("hoten")
        gioitinh_form = request.form.get("gioitinh")

        gioitinh = True if gioitinh_form == 'male' else False
        email = request.form.get("email")

        ngaysinh_form = request.form.get("ngaysinh")
        ngaysinh = None

        if ngaysinh_form:
            try:
                ngaysinh = datetime.strptime(ngaysinh_form, "%Y-%m-%d").date()
            except ValueError:
                err_msg = "Định dạng ngày sinh không hợp lệ!"
                return render_template('register.html', err_msg=err_msg)

        diachi = request.form.get("diachi")

        if dao.them_benhnhan(username, hoten, email, gioitinh, password,
                             UserRole.BENHNHAN, ngaysinh=ngaysinh, diachi=diachi):
            return redirect(url_for('login_process'))
        else:
            err_msg = "something went wrong"
    return render_template('register.html', err_msg=err_msg)

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=5000)
