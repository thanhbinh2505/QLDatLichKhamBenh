import time
from selenium.webdriver.common.by import By
from test.selenium_test.pages.LoginPage import LoginPage
from test.selenium_test.pages.BookingPage import BookingPage

from test.unit_test.test_base import driver

BASE_URL = "http://127.0.0.1:5000"


def test_luong_dang_nhap_va_dat_lich(driver):
    print("\n--- BẮT ĐẦU E2E TEST: ĐĂNG NHẬP & ĐẶT LỊCH ---")

    login_page = LoginPage(driver)
    booking_page = BookingPage(driver)

    print("1. Đang truy cập trang Đăng nhập...")
    driver.get(f"{BASE_URL}/login")
    time.sleep(1)

    # Điền form và submit
    login_page.login("benhnhan1@gmail.com", "123456")
    time.sleep(2)

    assert "login" not in driver.current_url, "Lỗi: Không thể đăng nhập!"

    print("2. Chuyển hướng đến trang Đặt lịch...")
    driver.get(f"{BASE_URL}/dat-lich")
    time.sleep(2)  # Chờ danh sách bác sĩ tải xong

    print("3. Chọn Bác Sĩ 1 và mở bảng chọn giờ...")
    booking_page.click_book_doctor_1()
    time.sleep(1)

    print("4. Chọn khung giờ đầu tiên và Xác nhận...")
    booking_page.select_first_time_slot()
    time.sleep(0.5)
    booking_page.click_submit_booking()
    time.sleep(2)

    thong_bao = booking_page.get_result_message()
    print(f"-> Hệ thống báo: '{thong_bao}'")

    assert thong_bao in ["Thành công!", "Thao tác thất bại"], f"Lỗi: Giao diện trả về thông báo lạ '{thong_bao}'"

    print("5. Đóng bảng thông báo...")
    booking_page.click_close_result()
    time.sleep(1)  # Chờ hiệu ứng đóng

    assert "dat-lich" in driver.current_url, "Lỗi: Đóng popup xong bị chuyển hướng sai chỗ!"

    print("--- HOÀN TẤT KỊCH BẢN ĐẶT LỊCH ---")