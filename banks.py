import logging
import os
import subprocess
import tempfile
from time import sleep

import cv2
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pytesseract import pytesseract

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bank-automation")

# Windows-only configuration (per project target platform).
TESSERACT_CMD = r"C:\Program Files\tocr\tesseract.exe"
OCR_CONFIG = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789"

# Error texts that mean the captcha/inputs were rejected and we should retry.
CAPTCHA_ERROR_TEXTS = {
    "لطفا اطلاعات مورد نیاز را به درستی وارد کنید",
    "کد امنیتی به درستی وارد نشده است",
    "کپچا اشتباه است",
}
RATE_LIMIT_TEXT = "درخواست بیش از حد مجاز است"

# Maximum captcha attempts before giving up, so we never spin forever.
MAX_CAPTCHA_ATTEMPTS = 15


class Banking:
    def __init__(self, card_number, cvv2, month, year, driver):
        self.driver = driver
        self.cardNumber = card_number
        self.cvv2 = cvv2
        self.month = month
        self.year = year
        self.state = None
        pytesseract.tesseract_cmd = TESSERACT_CMD

    # ------------------------------------------------------------------ helpers

    def _wait(self, timeout=20):
        return WebDriverWait(self.driver, timeout)

    def _find(self, by, value, timeout=20):
        """Wait for an element to be present and return it."""
        return self._wait(timeout).until(EC.presence_of_element_located((by, value)))

    def _fill(self, by, value, text):
        """Locate a field, clear it and type into it."""
        element = self._find(by, value)
        element.clear()
        element.send_keys(text)
        return element

    def _fill_card_form(self, fields):
        """Fill the four standard card fields.

        ``fields`` maps logical names to ``(By, locator)`` tuples for
        card number, cvv2, month and year.
        """
        self._fill(*fields["card"], self.cardNumber)
        self._fill(*fields["cvv2"], self.cvv2)
        self._fill(*fields["month"], self.month)
        self._fill(*fields["year"], self.year)

    def _read_captcha(self, element):
        """Screenshot a captcha element directly and OCR the digits.

        Capturing the element itself avoids the brittle absolute-coordinate
        cropping the old code relied on.
        """
        fd, raw_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            element.screenshot(raw_path)

            image = cv2.imread(raw_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            denoised = cv2.medianBlur(thresh, 3)

            text = str(pytesseract.image_to_string(denoised, config=OCR_CONFIG)).strip()
            logger.info("OCR result: len=%s content=%r digits=%s", len(text), text, text.isdigit())
            return text
        finally:
            if os.path.exists(raw_path):
                os.remove(raw_path)

    def _has_error(self, err_xpath):
        """Return the error element's text, or None if it isn't present."""
        try:
            return self.driver.find_element(By.XPATH, err_xpath).text
        except NoSuchElementException:
            return None

    # ----------------------------------------------------------- captcha solver

    def captcha_resolver(self, captcha_element, otp_button, err_xpath,
                         input_captcha, refresh_button):
        """Solve the captcha loop. Returns True on success, False on give-up."""
        for attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
            sleep(2.5)
            text = self._read_captcha(captcha_element)

            if len(text) == 5 and text.isdigit():
                enter_captcha = self.driver.find_element(By.XPATH, input_captcha)
                enter_captcha.clear()
                enter_captcha.send_keys(text)
                logger.info("Captcha typed")
                sleep(4)

                if self.state in ("tep", "bp"):
                    self.driver.find_element(By.XPATH, otp_button).click()
                else:
                    self.driver.find_element(By.ID, otp_button).click()
                logger.info("Captcha submitted")
                sleep(0.8)

                error_text = self._has_error(err_xpath)
                if error_text is None or error_text not in CAPTCHA_ERROR_TEXTS:
                    return True
                # Captcha rejected — clear the field and try again.
                enter_captcha.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
                enter_captcha.clear()
                logger.info("Captcha rejected, cleared field")

            if self.state == "bp" and attempt >= 5:
                if self._has_error(err_xpath) == RATE_LIMIT_TEXT:
                    self.driver.find_element(By.ID, "cancel").click()
                    sleep(3)
                    return False

            self.driver.find_element(By.XPATH, refresh_button).click()

        logger.warning("Gave up after %s captcha attempts", MAX_CAPTCHA_ATTEMPTS)
        return False

    # ------------------------------------------------------------------- gates

    def sep(self):
        self._fill_card_form({
            "card": (By.ID, "CardNumber_PanString"),
            "cvv2": (By.ID, "Cvv2"),
            "month": (By.ID, "Month"),
            "year": (By.ID, "Year"),
        })
        sleep(2)
        captcha = self._find(By.ID, "CaptchaImage")
        ok = self.captcha_resolver(
            captcha,
            "Otp",
            '//*[@id="frmPayment"]/div[6]',
            '//*[@id="CaptchaInputText"]',
            '//*[@id="frmPayment"]/div[4]/div/div/div[1]/div/i',
        )
        if not ok:
            return

        sec_pass = input("Watch your mobile, what did u see : ")
        self._fill(By.ID, "Pin2", sec_pass)
        sleep(0.5)
        self.driver.find_element(By.ID, "Purchase").click()

    def bpm(self):
        self._fill_card_form({
            "card": (By.ID, "cardnumber"),
            "cvv2": (By.ID, "inputcvv2"),
            "month": (By.ID, "inputmonth"),
            "year": (By.ID, "inputyear"),
        })
        sleep(2)
        captcha = self._find(By.ID, "captcha-img")
        ok = self.captcha_resolver(
            captcha,
            "otp-button",
            '//*[@id="body"]/div/section[1]/div/div[1]/div/div[3]/form/div[8]/div[2]/span',
            '//*[@id="inputcaptcha"]',
            '//*[@id="captcha-button"]',
        )
        if not ok:
            return

        sec_pass = input("Watch your mobile, what did u see : ")
        self._fill(By.ID, "inputpin", sec_pass)
        self.driver.execute_script("window.scrollTo(0, 540)")

        try:
            sleep(0.5)
            self.driver.find_element(By.ID, "payButton").click()
        except ElementClickInterceptedException:
            sleep(0.8)
            self.driver.find_element(By.ID, "payButton").click()

    def tep(self):
        sleep(5)
        self._fill_card_form({
            "card": (By.ID, "pan"),
            "cvv2": (By.ID, "cvv2"),
            "month": (By.ID, "txtExpM"),
            "year": (By.ID, "txtExpY"),
        })
        sleep(2)
        # Tejarat captcha is solved manually; pop a reminder dialog (Windows only).
        try:
            subprocess.run(
                [
                    "PowerShell",
                    "-Command",
                    "Add-Type -AssemblyName PresentationFramework;"
                    "[System.Windows.MessageBox]::Show('Its me again')",
                ],
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Error running PowerShell command: %s", e)

        captcha = input("Enter your captcha : ")
        self._fill(By.ID, "Captcha", captcha)
        self.driver.find_element(
            By.XPATH,
            "/html/body/div[1]/div/div/div[4]/div/div/div[3]/div/form/div[4]/div[2]/div[2]/button",
        ).click()

        sec_pass = input("Watch your mobile, what did u see : ")
        self._fill(By.ID, "pin2", sec_pass)
        sleep(0.5)
        self.driver.find_element(By.ID, "btnPayment").click()

    def bp(self):
        self._fill_card_form({
            "card": (By.XPATH, '//*[@id="field-0"]'),
            "cvv2": (By.ID, "field-1"),
            "month": (By.XPATH, '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[4]/div/div/div/input[1]'),
            "year": (By.XPATH, '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[4]/div/div/div/input[2]'),
        })
        sleep(2)
        captcha = self._find(By.CLASS_NAME, "captcha-image")
        ok = self.captcha_resolver(
            captcha,
            '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[7]/div[2]/button',
            '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[1]/div/div/div',
            '//*[@id="field-3"]',
            '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[5]/div/div/div[1]/span/button',
        )
        if not ok:
            return

        sec_pass = input("Watch your mobile, what did u see : ")
        self._fill(By.ID, "pincode", sec_pass)
        sleep(0.5)
        self.driver.find_element(By.ID, "purchase").click()

    # ----------------------------------------------------------------- routing

    def bank_checking(self, state):
        if self.cardNumber is None or self.cardNumber == "":
            self._wait(120).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[2]/div[2]/div/ui-view/div[1]/div/div/h2")
                )
            )
            return

        self.state = state
        gates = {"sep": self.sep, "bpm": self.bpm, "tep": self.tep, "bp": self.bp}
        gate = gates.get(state)
        if gate is None:
            raise ValueError(f"Unknown gateway state: {state!r}")
        gate()
