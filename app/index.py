from flask import render_template, request, url_for, jsonify
from sqlalchemy.testing.exclusions import succeeds_if
from werkzeug.utils import redirect
from datetime import datetime, timedelta
from flask_login import login_user, logout_user, login_required, current_user
from app import app, dao, login
from app.models import UserRole, CaLam, LichLamViec, NgayLamViec, PhanCa


@app.route('/')
def index():
    doctors = dao.get_list_doctor()
    return render_template('index.html', doctors=doctors)

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html', active_tab="lich_lam_viec")

@app.route('/dat-lich')
def dat_lich():
    return render_template('dat_lich.html')

@app.route('/admin/tao-lich', methods=['GET'])
@login_required
def admin_page_tao_lich():
    ds_calam = dao.get_list_shift()

    ngay_bat_dau_goi_y = dao.get_ngay_chua_sap_lich_gan_nhat()
    ngay_ket_thuc_goi_y = ngay_bat_dau_goi_y + timedelta(days=6)

    return render_template('admin_tao_lich.html',
                           ds_calam=ds_calam,
                           ngay_bat_dau_goi_y=ngay_bat_dau_goi_y.strftime('%Y-%m-%d'),
                           ngay_ket_thuc_goi_y=ngay_ket_thuc_goi_y.strftime('%Y-%m-%d')
                           )


from flask import request, jsonify


@app.route('/api/admin/luu-lich-lam-viec', methods=['POST'])
def api_tao_lich_moi():
    data = request.json
    ngay_bat_dau = data.get('ngayBatDau')
    ngay_ket_thuc = data.get('ngayKetThuc')
    lich_tuan = data.get('lichTuan', {})

    if ngay_bat_dau is not None and ngay_ket_thuc is not None:
        try:
            ngay_bat_dau = datetime.strptime(ngay_bat_dau, "%Y-%m-%d").date()
            ngay_ket_thuc = datetime.strptime(ngay_ket_thuc, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({
                "message": "Định dạng ngày bắt đầu / kết thúc không hợp lệ!",
            }), 400
    else:
        return jsonify({"message": "Thiếu thông tin ngày tháng!"}), 400

    try:
        lich_moi = dao.tao_lich_lam_viec(ngay_bat_dau, ngay_ket_thuc)

        day_map = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}

        current_date = ngay_bat_dau
        while current_date <= ngay_ket_thuc:
            thu_cua_ngay = day_map[current_date.weekday()]

            # Kiểm tra xem "Thứ" này có được xếp ca nào trong payload gửi lên không
            if thu_cua_ngay in lich_tuan:

                # Tạo bản ghi NgayLamViec
                dao.tao_ngay_lam_viec(current_date, lich_moi.id)

                # Lấy danh sách các ca của ngày hôm đó. VD: {"1": [5, 8], "2": [12]}
                danh_sach_ca = lich_tuan[thu_cua_ngay]

                for ca_id_str, bac_si_ids in danh_sach_ca.items():
                    ca_id = int(ca_id_str)

                    for bs_id in bac_si_ids:
                        # Gọi hàm tạo phân ca
                        success, msg_or_obj = dao.tao_phan_ca(bs_id, ca_id, current_date)

                        # Nếu logic DAO báo lỗi (trùng lặp, sai ID...), ném lỗi ra ngoài ngay
                        if not success:
                            raise ValueError(f"Lỗi ngày {current_date.strftime('%d/%m/%Y')} (Ca {ca_id}): {msg_or_obj}")

            # Tiến lên 1 ngày
            current_date += timedelta(days=1)

        # 4. Lưu chính thức toàn bộ (Lịch, Ngày, Phân Ca) xuống Database
        dao.commit()

        return jsonify({
            "message": "Tạo lịch thành công!",
            "id_lich_moi": lich_moi.id
        }), 200

    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400

    except Exception as e:
        print("Lỗi server:", e)
        return jsonify({"message": "Đã xảy ra lỗi. Thử lại sau!."}), 500

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

@app.route('/logout', methods=['GET', 'POST'])
def logout_process():
    logout_user()
    return redirect('/')

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


@app.route('/api/doctors')
def api_get_doctors():
    ds_bacsi_objects = dao.get_list_doctor()

    return jsonify([bs.to_dict() for bs in ds_bacsi_objects])


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=5000)
