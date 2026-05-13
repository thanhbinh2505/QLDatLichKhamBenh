import threading
import requests
import json

# URL API đặt lịch
url = "http://127.0.0.1:5000/api/dat-lich"

payload = {
    "bacsi_id": 1,
    "ngay_kham": "2026-06-01",
    "gio_kham": "08:00 - 08:30"
}

# Dán Cookie thật lấy từ web vào
headers_A = {'Cookie': 'session=.eJwdzrsNAjEMANBdUl8Rf5OwzMmObUF7QIXYHYk3wfu0s6583tvtdb3zaOcj2q1N0JUok8F4T46-3HZVDVTbWJvY1nByTuIyQJCoNGUXWD5lgpVp1OorgUF7AXYePGD4lkQGUul7RLnV9iUUQSUYqBQaXdvRzvczr_-Gvj9-wy9N.agNmbw.VpKHEFk9SF9QSj4T8i1GZQdBuV4'}
headers_B = {'Cookie': 'session=.eJwdzsENwzAIAMBd_M7DYMB2lonAgNJv0ryq7l6pN8F9ypFX3GfZ39cTWzleXvYyQGYgDwKlNcjrNF2Z2VF0Ya5GOrs1o2iUCgjsGSpkDNMGD9BU8Zx1BhBITcBKnTp0WxxI0ITr6p6muWxyc2_J6CjNxauUrRzPHdd_Q98ffsUvTg.agNn5w.vz7f2XkgBG0YHP7f4iD-zGfA8IE'}

# Tạo một cái "giỏ" để lưu mã trạng thái (status code) của 2 luồng
ket_qua = {}


def dat_lich(ten_nguoi_dung, headers):
    print(f"\n[{ten_nguoi_dung}] Đang bắn request...")
    response = requests.post(url, json=payload, headers=headers)

    # 1. BIẾN ĐỔI JSON ĐỂ ĐỌC ĐƯỢC TIẾNG VIỆT
    data_dict = response.json()
    json_dep = json.dumps(data_dict, ensure_ascii=False, indent=2)

    print(f"[{ten_nguoi_dung}] Kết quả: {response.status_code}")
    print(json_dep)

    # Lưu kết quả vào giỏ chung để lát nữa Pytest kiểm tra
    ket_qua[ten_nguoi_dung] = response.status_code


def test_race_condition():
    luong_A = threading.Thread(target=dat_lich, args=("Bệnh Nhân A", headers_A))
    luong_B = threading.Thread(target=dat_lich, args=("Bệnh Nhân B", headers_B))

    # Bóp cò!
    luong_A.start()
    luong_B.start()

    # Đợi cả 2 luồng chạy xong mới đi tiếp
    luong_A.join()
    luong_B.join()

    # --- 2. ASSERT ĐỂ HỆ THỐNG HẾT "NGÂY THƠ" ---
    status_A = ket_qua.get("Bệnh Nhân A")
    status_B = ket_qua.get("Bệnh Nhân B")

    # Khẳng định (Assert) kịch bản đúng:
    # "Tuyệt đối KHÔNG THỂ có chuyện cả A và B cùng bằng 200"
    # Nếu hệ thống lủng (cả 2 = 200), lệnh assert này sẽ làm bài Test sụp đổ (Báo FAILED)
    assert not (status_A == 200 and status_B == 200), \
        "🚨 BUG CRITICAL: Bị lỗi Race Condition! Cả 2 người đều đặt chung 1 lịch thành công!"