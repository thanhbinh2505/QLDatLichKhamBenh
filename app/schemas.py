from marshmallow import Schema, fields, validate, ValidationError, validates, validates_schema
from datetime import date


class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=[
        validate.Length(min=5, max=20, error="Username phải từ 5 đến 20 kí tự!"), 
        validate.Regexp(r'^\S+$', error="Username không được chứa khoảng trắng!")
        ], error_messages={
        "required": "Username không được để trống!"
    })
    
    password = fields.Str(required=True, validate=[
        validate.Length(min=8, error="Mật khẩu phải ít nhất 8 kí tự!"),
        validate.Length(max=255, error="Mật khẩu không được vượt quá 255 kí tự!"),
        validate.Regexp(r'^\S+$', error="Mật khẩu không được chứa khoảng trắng!"),
        validate.Regexp(r'.*[0-9].*', error="Mật khẩu phải chứa ít nhất một số!"),
        validate.Regexp(r'.*[a-z].*', error="Mật khẩu phải chứa ít nhất một chữ thường!"),
        validate.Regexp(r'.*[A-Z].*', error="Mật khẩu phải chứa ít nhất một chữ hoa!"),
        validate.Regexp(r'.*[!@#$%^&*(),.?":{}|<>].*', error="Mật khẩu phải chứa ít nhất một kí tự đặc biệt!")
    ], error_messages={
        "required": "Password không được để trống!"
    })
    
    hoten = fields.Str(required=True, validate=[
        validate.Length(max=50, error="Họ tên không được vượt quá 50 ký tự!"),
        validate.Regexp(r'^\s*\S', error="Họ tên không được để trống!")
    ], error_messages={
        "required": "Họ tên không được để trống!"
    })
    
    email = fields.Email(required=True, validate=[
        validate.Length(max=100, error="Email không được vượt quá 100 ký tự!"), 
        ], error_messages={
        "required": "Email không được để trống!",
        "invalid": "Email không hợp lệ!"
    })
    
    gioitinh = fields.Str(required=True, validate=validate.OneOf(
        ["male", "female"], error="Giới tính không hợp lệ!"
    ), error_messages={"required": "Giới tính không được để trống!"})
    
    ngaysinh = fields.Date(required=False, allow_none=True, error_messages={
        "invalid": "Ngày sinh không hợp lệ!"
    })
    
    diachi = fields.Str(required=False, allow_none=True, validate=validate.Length(max=255, error="Địa chỉ không được vượt quá 255 ký tự!"))

    @validates('ngaysinh')
    def validate_ngaysinh(self, value, **kwargs):
        if value:
            today = date.today()
            if value >= today:
                raise ValidationError("Ngày sinh không được là hôm nay hoặc tương lai!")
            min_date = today.replace(year=today.year - 150)
            if value < min_date:
                raise ValidationError("Ngày sinh quá xa trong quá khứ!")

class StartEndDateSchema(Schema):
    ngayBatDau = fields.Date(required=True, error_messages={
        "required": "Vui lòng cung cấp ngày bắt đầu.",
        "invalid": "Ngày bắt đầu không hợp lệ!"
        })

    ngayKetThuc = fields.Date(required=True, error_messages={
        "required": "Vui lòng cung cấp ngày kết thúc.",
        "invalid": "Ngày kết thúc không hợp lệ!"
        })

    @validates('ngayBatDau')
    def validate_ngayBatDau(self, value, **kwargs):
        if value.weekday() != 0:
            raise ValidationError("Ngày bắt đầu phải là Thứ 2.")

    @validates('ngayKetThuc')
    def validate_ngayKetThuc(self, value, **kwargs):
        if value.weekday() != 6:
            raise ValidationError("Ngày kết thúc phải là Chủ nhật.")

    @validates_schema
    def validate_khoang_thoi_gian(self, data, **kwargs):
        if 'ngayBatDau' in data and 'ngayKetThuc' in data:
            if data['ngayKetThuc'] < data['ngayBatDau']:
                raise ValidationError("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.")
            if (data['ngayKetThuc'] - data['ngayBatDau']).days != 6:
                raise ValidationError("Khoảng thời gian phải đúng 1 tuần (7 ngày).")

class LuuLichLamViecSchema(Schema):
    lichTuan = fields.Dict(
        keys=fields.Str(validate=validate.OneOf(
            ["T2", "T3", "T4", "T5", "T6", "T7", "CN"], 
            error="Ngày trong tuần không hợp lệ (phải từ T2 đến CN)."
        )),
        values=fields.Dict(
            keys=fields.Int(error_messages={"invalid": "Dữ liệu không hợp lệ!"}),
            values=fields.List(fields.Int(error_messages={"invalid": "Dữ liệu không hợp lệ!"}), error_messages={"invalid": "Dữ liệu không hợp lệ!"}),
            error_messages={
                "invalid": "Dữ liệu không hợp lệ!"
            }
        ),
        required=True,
        error_messages={
            "required": "Vui lòng cung cấp dữ liệu lịch tuần.",
            "invalid": "Dữ liệu không hợp lệ!"
            }
    )

    ngayBatDau = fields.Date(required=True, error_messages={
        "required": "Vui lòng cung cấp ngày bắt đầu.",
        "invalid": "Ngày bắt đầu không hợp lệ!"
    })

    ngayKetThuc = fields.Date(required=True, error_messages={
        "required": "Vui lòng cung cấp ngày kết thúc.",
        "invalid": "Ngày kết thúc không hợp lệ!"
    })

    @validates('ngayBatDau')
    def validate_ngayBatDau(self, value, **kwargs):
        if value < date.today():
            raise ValidationError("Không thể tạo lịch làm việc trong quá khứ.")

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'ngayBatDau' in data and 'ngayKetThuc' in data:
            if data['ngayKetThuc'] < data['ngayBatDau']:
                raise ValidationError("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.")
            if (data['ngayKetThuc'] - data['ngayBatDau']).days < 7:
                raise ValidationError("Tạo lịch làm việc phải ít nhất 7 ngày.")

class TaoNghiPhepSchema(Schema):
    bacsi_id = fields.Int(required=True, error_messages={"required": "Vui lòng cung cấp ID bác sĩ."})
    
    ngayBatDau = fields.Date(required=True, error_messages={
        "required": "Vui lòng nhập ngày bắt đầu.",
        "invalid": "Ngày bắt đầu không đúng định dạng (YYYY-MM-DD)."
    })
    
    ngayKetThuc = fields.Date(required=True, error_messages={
        "required": "Vui lòng nhập ngày kết thúc.",
        "invalid": "Ngày kết thúc không đúng định dạng (YYYY-MM-DD)."
    })
    
    lyDo = fields.Str(required=False, validate=validate.Length(max=255), error_messages={
        "length": "Lý do không được vượt quá 255 ký tự."
    })

    @validates('ngayBatDau')
    def validate_ngayBatDau(self, value, **kwargs):
        if value < date.today():
            raise ValidationError("Không thể tạo ngày nghỉ phép trong quá khứ.")
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'ngayBatDau' in data and 'ngayKetThuc' in data:
            if data['ngayKetThuc'] < data['ngayBatDau']:
                raise ValidationError("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.")