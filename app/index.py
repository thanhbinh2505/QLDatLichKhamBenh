from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template, request, url_for, jsonify, redirect
from datetime import datetime, timedelta, date
from flask_login import login_user, logout_user, current_user
from marshmallow import ValidationError

from app import app, dao, login
from app.models import UserRole, BenhNhan
from app.decorator import role_required, anonymous_required
import app.schemas as schemas

def register_routes(app):
    @app.route('/')
    def index():
        doctors = dao.get_list_doctor()
        return render_template('index.html', doctors=doctors)

    @app.route('/login', methods=['GET', 'POST'])
    @anonymous_required
    def login_process():
        error_msg = ""
        username_val = ""

        if request.method == 'POST':
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
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
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

    @app.route('/register', methods=["GET", "POST"])
    @anonymous_required
    def register():
        err_msg = ""
        data = {}
        if request.method == 'POST':
            data = request.form.to_dict()
            
            if data.get('ngaysinh') == '':
                data['ngaysinh'] = None
            
            register_schema = schemas.RegisterSchema()
            try:
                data = register_schema.load(data)
            except ValidationError as err:
                first_error_field = list(err.messages.keys())[0]
                err_msg = err.messages[first_error_field][0]
                
                return render_template('register.html', err_msg=err_msg)
                
            username = data.get("username")
            password = data.get("password")
            hoten = data.get("hoten")
            gioitinh = True if data.get("gioitinh") == 'male' else False
            email = data.get("email")
            ngaysinh = data.get("ngaysinh", None)
            diachi = data.get("diachi", None)

            try:
                success, message = dao.them_benhnhan(username, hoten, email, gioitinh, password,
                                        ngaysinh=ngaysinh, diachi=diachi)
                if success:
                    return redirect(url_for('login_process'))
                else:
                    err_msg = message
            except Exception as e:
                err_msg = "Có lỗi xảy ra. Vui lòng thử lại sau!"

        return render_template('register.html', err_msg=err_msg)

    @app.route('/api/doctors')
    def api_get_doctors():
        ds_bacsi_objects = dao.get_list_doctor()
        return jsonify([bs.to_dict() for bs in ds_bacsi_objects])

    @app.route('/dat-lich', methods=['GET'])
    @role_required([UserRole.BENHNHAN, UserRole.ADMIN])
    def dat_lich():
        return render_template('dat_lich.html')

    @app.route('/api/gio-kham-bac-si', methods=['GET'])
    @role_required([UserRole.BENHNHAN, UserRole.ADMIN])
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
    @role_required(UserRole.BENHNHAN)
    def api_dat_lich():
        try:
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

    @app.route('/hoso')
    @role_required(UserRole.BENHNHAN)
    def ho_so():
        benh_nhan = BenhNhan.query.filter_by(user_id=current_user.id).first()
        return render_template('ho_so.html', benh_nhan=benh_nhan)

    @app.route('/api/huy-lich/<int:phieu_id>', methods=['POST'])
    @role_required([UserRole.BENHNHAN, UserRole.ADMIN])
    def huy_lich_api(phieu_id):
        success, message = dao.huy_lich_kham(phieu_id, current_user)

        if success:
            return jsonify({
                "success": True,
                "message": message
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": message
            }), 400

    @app.route('/api/ho-so/lich-kham')
    @role_required(UserRole.BENHNHAN)
    def get_lich_kham_ho_so():
        try:
            ds_lich_kham = dao.get_lich_da_dat(user_id=current_user.id)
            return jsonify(ds_lich_kham), 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify([]), 500

    @app.route('/admin')
    @role_required(UserRole.ADMIN)
    def admin():
        ds_ca = dao.get_list_shift()

        ngay_hom_nay = date.today()
        thu_cua_hom_nay = ngay_hom_nay.weekday()
        thu_2_cua_tuan_hien_tai = ngay_hom_nay - timedelta(days= thu_cua_hom_nay )
        cn_cua_tuan_hien_tai = thu_2_cua_tuan_hien_tai + timedelta(days= 6)

        return render_template('admin_lich_lam_viec.html',
                               active_tab="lich_lam_viec",
                               ds_calam = ds_ca,
                               thu_2=thu_2_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               chu_nhat=cn_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               )

    @app.route('/admin/lich-lam-viec')
    @role_required(UserRole.ADMIN)
    def admin_lich_lam_viec():
        ds_ca = dao.get_list_shift()

        ngay_hom_nay = date.today()
        thu_cua_hom_nay = ngay_hom_nay.weekday()
        thu_2_cua_tuan_hien_tai = ngay_hom_nay - timedelta(days= thu_cua_hom_nay )
        cn_cua_tuan_hien_tai = thu_2_cua_tuan_hien_tai + timedelta(days= 6)

        return render_template('admin_lich_lam_viec.html',
                               active_tab="lich_lam_viec",
                               ds_calam = ds_ca,
                               thu_2=thu_2_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               chu_nhat=cn_cua_tuan_hien_tai.strftime('%Y-%m-%d'),
                               )

    @app.route('/api/admin/lay-lich-tuan', methods=['GET'])
    @role_required(UserRole.ADMIN)
    def api_lay_lich_tuan():
        try:
            data = schemas.StartEndDateSchema().load(request.args)
        except ValidationError as err:
            return jsonify({"message": "Dữ liệu không hợp lệ", "errors": err.messages}), 400
        
        ngay_bat_dau = data.get('ngayBatDau')
        ngay_ket_thuc = data.get('ngayKetThuc')

        try:
            lich_tuan = dao.lay_lich_tuan(ngay_bat_dau, ngay_ket_thuc)

            return jsonify({
                "message": "Lấy lịch thành công",
                "data": lich_tuan
            }), 200

        except Exception as e:
            return jsonify({"message": "Đã xảy ra lỗi hệ thống."}), 500

    @app.route('/admin/tao-lich', methods=['GET'])
    @role_required(UserRole.ADMIN)
    def admin_page_tao_lich():
        ds_calam = dao.get_list_shift()

        ngay_bat_dau_goi_y = dao.get_ngay_chua_sap_lich_gan_nhat()
        ngay_ket_thuc_goi_y = ngay_bat_dau_goi_y + timedelta(days=6)

        return render_template('admin_tao_lich.html',
                               ds_calam=ds_calam,
                               ngay_bat_dau_goi_y=ngay_bat_dau_goi_y.strftime('%Y-%m-%d'),
                               ngay_ket_thuc_goi_y=ngay_ket_thuc_goi_y.strftime('%Y-%m-%d')
                               )

    @app.route('/admin/benh-nhan', methods=['GET'])
    @role_required(UserRole.ADMIN)
    def admin_benh_nhan():
        ds_benh_nhan = dao.get_all_benh_nhan()
        return render_template('admin_benh_nhan.html', ds_benh_nhan = ds_benh_nhan)

    @app.route('/api/admin/benh-nhan/<int:id>/lich-kham', methods=['GET'])
    @role_required(UserRole.ADMIN)
    def api_get_lich_kham_benh_nhan(id):
        try:
            benh_nhan = dao.get_benh_nhan_by_id(id)
            if not benh_nhan:
                return jsonify({"success": False, "message": "Không tìm thấy bệnh nhân"}), 404
            ds_lich_kham = dao.get_lich_da_dat(user_id=benh_nhan.user_id)
            return jsonify({"success": True, "data": ds_lich_kham}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/api/admin/luu-lich-lam-viec', methods=['POST'])
    @role_required(UserRole.ADMIN)
    def api_tao_lich_moi():
        try:
            data = schemas.LuuLichLamViecSchema().load(request.json)
        except ValidationError as err:
            first_error_field = list(err.messages.keys())[0]
            err_msg = err.messages[first_error_field][0]
            return jsonify({
                "message": err_msg
            }), 400

        ngay_bat_dau = data['ngayBatDau']
        ngay_ket_thuc = data['ngayKetThuc']
        lich_tuan = data['lichTuan']

        try:
            success, msg = dao.tao_lich(lich_tuan, ngay_bat_dau, ngay_ket_thuc)
            if success:
                return jsonify({
                    "message": msg
                }), 200
            else:
                return jsonify({
                    "message": msg
                }), 400

        except Exception as e:
            return jsonify({"message": "Đã xảy ra lỗi. Thử lại sau!."}), 500

    @app.route('/api/admin/tao-nghi-phep', methods=['POST'])
    @role_required(UserRole.ADMIN)
    def api_tao_nghi_phep():
        nghi_phep_schema = schemas.TaoNghiPhepSchema()
        try:
            data = nghi_phep_schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                "message": "Dữ liệu không hợp lệ", 
                "errors": err.messages
            }), 400

        bacsi_id = data['bacsi_id']
        ngay_bat_dau = data['ngayBatDau']
        ngay_ket_thuc = data['ngayKetThuc']
        ly_do = data.get('lyDo', '')

        try:
            success, msg = dao.tao_nghi_phep_bac_si(bacsi_id, ngay_bat_dau, ngay_ket_thuc, ly_do)
            if success:
                return jsonify({"message": msg}), 200
            else:
                return jsonify({"message": msg}), 400
        except Exception as e:
            print("Lỗi tạo nghỉ phép:", e)
            return jsonify({"message": "Lỗi hệ thống khi tạo nghỉ phép."}), 500

    @app.route('/admin/bac-si', methods=['GET'])
    @role_required(UserRole.ADMIN)
    def quan_ly_bac_si():
        today = date.today()
        danh_sach_bac_si = dao.get_list_doctor()
        
        bac_si_co_lich = dao.lay_bac_si_co_lich_lam_viec(today)
        bac_si_nghi_phep = dao.lay_bac_si_nghi_phep(today)
        
        co_lich_ids = [bs.id for bs in bac_si_co_lich]
        nghi_phep_ids = [bs.id for bs in bac_si_nghi_phep]
        
        status_map = {}
        for bs in danh_sach_bac_si:
            if bs.id in nghi_phep_ids:
                status_map[bs.id] = 'nghi_phep'
            elif bs.id in co_lich_ids:
                status_map[bs.id] = 'dang_lam_viec'
            else:
                status_map[bs.id] = 'ngay_nghi'
                
        return render_template('admin_doctor.html', active_tab="bac_si", danh_sach_bac_si=danh_sach_bac_si, status_map=status_map)

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)

if __name__ == '__main__':
    register_routes(app)
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=dao.cap_nhat_trang_thai_lich_kham, trigger='interval', minutes=5)
    scheduler.start()
    try:
        with app.app_context():
            app.run(debug=True, port=5000, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

