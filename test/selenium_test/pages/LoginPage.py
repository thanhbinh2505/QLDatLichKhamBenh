from selenium.webdriver.common.by import By
from .BasePage import BasePage


class LoginPage(BasePage):
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BTN = (By.XPATH, "//button[@type='submit']")
    TOGGLE_PWD_BTN = (By.ID, "togglePassword")

    def login(self, email, password):
        self.typing(*self.EMAIL_INPUT, email)
        self.typing(*self.PASSWORD_INPUT, password)

        self.click(*self.SUBMIT_BTN)

    def click_toggle_password(self):
        self.click(*self.TOGGLE_PWD_BTN)

    def get_password_input_type(self):
        e = self.find(*self.PASSWORD_INPUT)
        return e.get_attribute("type")