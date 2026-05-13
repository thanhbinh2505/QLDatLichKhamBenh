from selenium.webdriver.common.by import By
from .BasePage import BasePage

class HomePage(BasePage):
    LOGIN_BTN = (By.XPATH, "//a[contains(@href, '/login')]")
    MAIN_BOOKING_BTN = (By.ID, "main-booking-btn")
    DOCTOR_CARDS = (By.CSS_SELECTOR, "#doctor-container > div")
    SCROLL_RIGHT_DOCTOR_BTN = (By.XPATH, "//button[contains(@onclick, 'right')]")

    def click_login(self):
        self.click(*self.LOGIN_BTN)

    def click_main_booking(self):
        self.click(*self.MAIN_BOOKING_BTN)

    def click_next_doctor(self):
        self.click(*self.SCROLL_RIGHT_DOCTOR_BTN)

    def count_doctor_cards(self):
        elements = self.finds(*self.DOCTOR_CARDS)
        return len(elements)