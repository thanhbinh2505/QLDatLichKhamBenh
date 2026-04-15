from flask import render_template, request, url_for, jsonify
from sqlalchemy.testing.exclusions import succeeds_if
from werkzeug.utils import redirect
from datetime import datetime, timedelta, date
from flask_login import login_user, logout_user, login_required, current_user
from app import app, dao, login
from app.models import UserRole, CaLam, LichLamViec, NgayLamViec, PhanCa, TrangThaiBacSi
def register_routes(app):
    @app.route('/')
    def index():
        doctors = dao.get_list_doctor()
        return render_template('index.html', doctors=doctors)

    @app.route('/login', methods=['GET', 'POST'])
    def login_process():
        error_msg = ""
        username_val = ""

        if request.method == ('POST'):
            username_or_email = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            user = dao.get_user_by_email_username(username_or_email)
            if not user:
                error_msg = "Username hoặc email không tồn tại!"
                username_val = ""
            elif not user.check_password(password):
                error_msg = "Mật khẩu không chính xác!"
                username_val = username_or_email
            else:
                login_user(user = user)
                if user.role == UserRole.ADMIN:
                    return redirect('/admin')
                elif user.role == UserRole.BACSI:
                    return redirect('/bacsi')
                elif user.role == UserRole.BENHNHAN:
                    return redirect('/')

        return render_template('login.html', error=error_msg, username_val=username_val)

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

    @app.route('/api/doctors')
    def api_get_doctors():
        ds_bacsi_objects = dao.get_list_doctor()

        return jsonify([bs.to_dict() for bs in ds_bacsi_objects])

    @app.route('/dat-lich', methods=['GET'])
    def dat_lich():
        return render_template('dat_lich.html')
    @app.route('/api/gio-kham-bac-si', methods=['GET'])
    def api_gio_kham_bac_si():
        bacsi_id = request.args.get('bacsi_id')
        ngay_str = request.args.get('ngay')

        if not bacsi_id or not ngay_str:
            return jsonify({"error": "Thiếu tham số"}), 400

        ket_qua = dao.get_khung_gio_bac_si(bacsi_id, ngay_str)

        if ket_qua.get("status") == "error":
            return jsonify(ket_qua), 400

        return jsonify(ket_qua)

    @app.route('/api/dat-lich', methods=['POST'])
    def api_dat_lich():
        try:
            if not current_user.is_authenticated or current_user.role != UserRole.BENHNHAN:
                return jsonify({
                    "success": False,
                    "loai_thong_bao": "auth_required",
                    "message": "Vui lòng đăng nhập để đặt lịch khám!"
                }), 401
            data = request.json
            bacsi_id = data.get('bacsi_id')
            ngay_kham = data.get('ngay_kham')
            gio_kham = data.get('gio_kham')

            if not bacsi_id or not ngay_kham or not gio_kham:
                 return jsonify({
                    "success": False,
                    "loai_thong_bao": "error",
                    "message": "Thiếu thông tin đặt lịch!"
                }), 400

            thanh_cong, thong_diep, info = dao.luu_phieu_dat_lich(
                bacsi_id=bacsi_id,
                ngay_kham_str=ngay_kham,
                gio_kham_str=gio_kham,
                current_user_id=current_user.id
            )
            return jsonify({
                "success": thanh_cong,
                "loai_thong_bao": 'success' if thanh_cong else 'error',
                "message": thong_diep,
                "booking_info": info
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "loai_thong_bao": "error",
                "message": f"Hệ thống bận hoặc có lỗi: {str(e)}"
            }), 500

    @app.route('/admin')
    @login_required
    def admin():

        ds_ca = dao.get_list_shift()

        ngay_hom_nay = date.today()
        thu_cua_hom_nay = ngay_hom_nay.weekday()
        thu_2_cua_tuan_hien_tai = ngay_hom_nay - timedelta(days= thu_cua_hom_nay )
        cn_cua_tuan_hien_tai = thu_2_cua_tuan_hien_tai + timedelta(days= 6)

        return render_template('admin.html',
                               active_tab="lich_lam_viec",
                               ds_calam = ds_ca,
                               thu_2=thu_2_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               chu_nhat=cn_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               )

    @app.route('/api/admin/lay-lich-tuan', methods=['GET'])
    def api_lay_lich_tuan():
        start_str = request.args.get('ngayBatDau')
        end_str = request.args.get('ngayKetThuc')

        if not start_str or not end_str:
            return jsonify({"message": "Thiếu tham số ngayBatDau hoặc ngayKetThuc"}), 400

        try:
            ngay_bat_dau = datetime.strptime(start_str, "%Y-%m-%d").date()
            ngay_ket_thuc = datetime.strptime(end_str, "%Y-%m-%d").date()

            if ngay_bat_dau.weekday() != 0:
                return jsonify({"message": f"Ngày bắt đầu ({start_str}) phải là Thứ 2."}), 400

            if ngay_ket_thuc.weekday() != 6:
                return jsonify({"message": f"Ngày kết thúc ({end_str}) phải là Chủ nhật."}), 400

            if (ngay_ket_thuc - ngay_bat_dau).days != 6:
                return jsonify({"message": "Khoảng thời gian phải đúng 1 tuần (7 ngày)."}), 400

            ds_ngay_lam_viec = dao.lay_ngay_lam_viec(ngay_bat_dau, ngay_ket_thuc)

            day_map = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}
            lich_tuan = {}

            for ngay_lam_viec in ds_ngay_lam_viec:
                thu = day_map[ngay_lam_viec.ngay.weekday()]
                lich_tuan[thu] = {}

                ds_phan_ca = dao.lay_danh_sach_phan_ca(ngay_lam_viec.ngay)

                for pc in ds_phan_ca:
                    ca_id_str = str(pc.id_CaLam)
                    bs_id = pc.id_BacSi

                    if ca_id_str not in lich_tuan[thu]:
                        lich_tuan[thu][ca_id_str] = []

                    lich_tuan[thu][ca_id_str].append(bs_id)

            return jsonify({
                "message": "Lấy lịch thành công",
                "data": lich_tuan
            }), 200

        except ValueError as ve:
            return jsonify({"message": str(ve)}), 400
        except Exception as e:
            print("Lỗi API lấy lịch tuần:", e)
            return jsonify({"message": "Đã xảy ra lỗi hệ thống."}), 500

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

                if thu_cua_ngay in lich_tuan:

                    dao.tao_ngay_lam_viec(current_date, lich_moi.id)

                    danh_sach_ca = lich_tuan[thu_cua_ngay]

                    for ca_id_str, bac_si_ids in danh_sach_ca.items():
                        ca_id = int(ca_id_str)

                        for bs_id in bac_si_ids:
                            success, msg_or_obj = dao.tao_phan_ca(bs_id, ca_id, current_date)

                            if not success:
                                raise ValueError(f"Lỗi ngày {current_date.strftime('%d/%m/%Y')} (Ca {ca_id}): {msg_or_obj}")

                current_date += timedelta(days=1)

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

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=5000)
