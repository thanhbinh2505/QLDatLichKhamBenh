import time
from selenium.webdriver.common.by import By
from test.selenium_test.pages.HomePage import HomePage
from test.selenium_test.pages.LoginPage import LoginPage
from test.unit_test.test_base import driver

BASE_URL = "http://127.0.0.1:5000/"


def test_luong_dang_nhap_va_dat_lich(driver):
    print("\n--- TC01: E2E - ĐĂNG NHẬP VÀ ĐẶT LỊCH ---")
    home_page = HomePage(driver)
    login_page = LoginPage(driver)

    driver.get(BASE_URL)
    time.sleep(1)

    home_page.click_login()
    time.sleep(1)

    print("-> Đang đăng nhập với tài khoản bệnh nhân...")
    login_page.login("benhnhan1@gmail.com", "123456")
    time.sleep(2)  # Đợi xử lý đăng nhập

    driver.get(BASE_URL)
    time.sleep(1)

    print("-> Đang click Đặt lịch ngay...")
    home_page.click_main_booking()
    time.sleep(1)

    current_url = driver.current_url
    assert "dat-lich" in current_url, "Lỗi: Không thể vào trang đặt lịch sau khi đã đăng nhập!"
    print("=> THÀNH CÔNG: Đã vào được trang Đặt lịch sau khi xác thực.")


def test_cac_tinh_nang_ui_trang_chu(driver):
    print("\n--- TC02: TEST GIAO DIỆN VÀ ĐIỀU HƯỚNG TRANG CHỦ ---")

    driver.get(BASE_URL)
    time.sleep(1)

    print("-> Test thanh điều hướng (Nav)...")
    nav_links = {
        "Về chúng tôi": "we",
        "Chuyên khoa": "services",
        "Đội ngũ bác sĩ": "doctors"
    }

    for ten_link, id_phan_tu in nav_links.items():
        link_element = driver.find_element(By.XPATH, f"//nav//a[@href='#{id_phan_tu}']")
        link_element.click()
        time.sleep(1)
        assert f"#{id_phan_tu}" in driver.current_url, f"Lỗi: Không cuộn được đến phần {ten_link}"

    print("=> Thanh điều hướng hoạt động tốt.")

    print("-> Test nút đặt lịch trôi nổi (Floating Button)...")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    floating_btn = driver.find_element(By.XPATH, "//div[@id='floating-booking-btn']/a")

    is_displayed = floating_btn.is_displayed()
    assert is_displayed, "Lỗi: Cuộn xuống cuối trang nhưng không thấy nút Đặt lịch trôi nổi!"

    floating_btn.click()
    time.sleep(1)
    assert "dat-lich" in driver.current_url, "Lỗi: Nút đặt lịch trôi nổi không chuyển hướng đúng!"

    print("=> Nút đặt lịch trôi nổi hoạt động tốt.")
    print("--- HOÀN THÀNH TEST TRANG CHỦ ---")