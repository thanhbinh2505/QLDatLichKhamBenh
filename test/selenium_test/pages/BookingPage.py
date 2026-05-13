from selenium.webdriver.common.by import By
from .BasePage import BasePage


class BookingPage(BasePage):
    BOOK_DOC_1_BTN = (By.XPATH, "//button[contains(@onclick, \"openBookingModal('1'\")]")

    FIRST_AVAILABLE_TIME_SLOT = (By.XPATH,
                                 "(//button[contains(@class, 'time-slot') and not(contains(@class, 'booked'))])[1]")

    SUBMIT_BTN = (By.ID, "btnSubmitBooking")

    RESULT_TITLE = (By.XPATH, "//div[@id='resultModal']//h3")

    CLOSE_RESULT_BTN = (By.XPATH, "//button[contains(text(), 'Đóng')]")

    def click_book_doctor_1(self):
        self.click(*self.BOOK_DOC_1_BTN)

    def select_first_time_slot(self):
        self.click(*self.FIRST_AVAILABLE_TIME_SLOT)

    def click_submit_booking(self):
        self.click(*self.SUBMIT_BTN)

    def get_result_message(self):
        element = self.find(*self.RESULT_TITLE)
        return element.text

    def click_close_result(self):
        self.click(*self.CLOSE_RESULT_BTN)