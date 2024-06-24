from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementClickInterceptedException
)
import subprocess
import cv2
from PIL import Image
from io import BytesIO
import base64
from pytesseract import pytesseract


class Banking:
    def __init__(self, card_number, cvv2, month, year, driver):
        self.driver = driver
        self.cardNumber = card_number
        self.cvv2 = cvv2
        self.month = month
        self.year = year

    def captcha_resolver(self, location, otp_button, err_placce, input_captcha, refresh_button):

        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        path_to_tesseract = r'C:\Program Files\tocr\tesseract.exe' 
        path_to_image = r'SepCaptcha.png' 
        pytesseract.tesseract_cmd = path_to_tesseract
        counter = 0
        while True: 
            sleep(2.5) 
            screenshot = self.driver.get_screenshot_as_base64() 
            img = Image.open(BytesIO(base64.b64decode(screenshot))) 
            area = img.crop(location) 
            area.save(path_to_image,'png') 
            ## cv2 library 
            # Load the image
            image = cv2.imread(path_to_image)

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            # Apply denoising (optional)
            denoised = cv2.medianBlur(thresh, 3)

            # Save the preprocessed image
            cv2.imwrite('ready.png', denoised)

            # OCR with Tesseract
            text = str(pytesseract.image_to_string(denoised, config=config))
            ## 
            text = text.strip()
            # Check if the captcha is valid
            print(len(text), " and content = ", text, "and is ", text.isdigit()) 
            if len(text) == 5 and text.isdigit() : 
                enterCaptcha = self.driver.find_element(By.XPATH, input_captcha)
                enterCaptcha.send_keys(text) 
                print("Captcha entered1")
                sleep(4)
                if self.state == 'tep' or self.state == 'bp':
                    self.driver.find_element(By.XPATH, otp_button).click() 
                else:
                    self.driver.find_element(By.ID, otp_button).click() 
                print("Captcha entered")
                sleep(.8)
                try:
                    sss = self.driver.find_element(By.XPATH, err_placce)
                    if sss.text != "لطفا اطلاعات مورد نیاز را به درستی وارد کنید" and sss.text != "کد امنیتی به درستی وارد نشده است" and sss.text != "کپچا اشتباه است": 
                        break 
                except NoSuchElementException:
                    enterCaptcha.send_keys(Keys.CONTROL, 'A', Keys.BACKSPACE)
                    print("Cleaned")
                    enterCaptcha.clear()
        
            refresh = self.driver.find_element(By.XPATH, refresh_button)
            if self.state == 'bp' and counter >= 5:
                try:
                    sss = self.driver.find_element(By.XPATH, err_placce)
                    if sss.text == "درخواست بیش از حد مجاز است":
                        self.driver.find_element(By.ID, 'cancel').click()
                        sleep(3)
                        return False
                except NoSuchElementException:
                    pass
                
            counter += 1
            refresh.click()

    def sep(self, cardNumber, cvv2, month, year):

        #In Way
        CardNumber = self.driver.find_element(By.ID,'CardNumber_PanString')
        CardNumber.send_keys(cardNumber)
        CVV2Number = self.driver.find_element(By.ID,'Cvv2')
        CVV2Number.send_keys(cvv2)
        Mounth = self.driver.find_element(By.ID,'Month')
        Mounth.send_keys(month)
        Year = self.driver.find_element(By.ID,'Year')
        Year.send_keys(year)
        sleep(2)
        captcha = self.driver.find_element(By.ID,'CaptchaImage') 
        loc = captcha.location 
        size = captcha.size 
        left = loc['x'] 
        top = loc['y'] 
        width = size['width'] 
        height = size['height'] 
        box = (int(left-6), int(top-5), int(left+width-4), int(top+height-4))
        captcha = self.captcha_resolver(box, 'Otp', '//*[@id="frmPayment"]/div[6]', '//*[@id="CaptchaInputText"]', '//*[@id="frmPayment"]/div[4]/div/div/div[1]/div/i')

        Pin2 = self.driver.find_element(By.ID,'Pin2')
        secPass = input("Watch your mobile, what did u see : ")
        Pin2.send_keys(secPass)
        Purchase = self.driver.find_element(By.ID, 'Purchase')
        sleep(.5)
        Purchase.click()

    def bpm(self, cardNumber, cvv2, month, year):
        #In Way
        CardNumber = self.driver.find_element(By.ID,'cardnumber')
        CardNumber.send_keys(cardNumber)
        CVV2Number = self.driver.find_element(By.ID,'inputcvv2')
        CVV2Number.send_keys(cvv2)
        Mounth = self.driver.find_element(By.ID,'inputmonth')
        Mounth.send_keys(month)
        Year = self.driver.find_element(By.ID,'inputyear')
        Year.send_keys(year)
        sleep(2)
        captcha = self.driver.find_element(By.ID,'captcha-img')
        loc = captcha.location 
        size = captcha.size 
        left = loc['x'] 
        top = loc['y'] 
        width = size['width'] 
        height = size['height']
        box = (int(left), int(top-6), int(left+width-44), int(top+height-4))
        self.captcha_resolver(box, 'otp-button', '//*[@id="body"]/div/section[1]/div/div[1]/div/div[3]/form/div[8]/div[2]/span', '//*[@id="inputcaptcha"]', '//*[@id="captcha-button"]')

        # time.sleep(5)
        Pin2 = self.driver.find_element(By.ID,'inputpin')
        secPass = input("Watch your mobile, what did u see : ")
        Pin2.clear()
        Pin2.send_keys(secPass)
        self.driver.execute_script("window.scrollTo(0, 540)")
    
        try:
            Purchase = self.driver.find_element(By.ID,'payButton')
            sleep(.5)
            Purchase.click()
        except ElementClickInterceptedException:
            sleep(.8)
            Purchase = self.driver.find_element(By.ID,'payButton')
            sleep(.5)
            Purchase.click()

    def tep(self, cardNumber, cvv2, month, year):
        #In Way
        sleep(5)
        CardNumber = self.driver.find_element(By.ID,'pan')
        CardNumber.clear()
        CardNumber.send_keys(cardNumber)
        CVV2Number = self.driver.find_element(By.ID,'cvv2')
        CVV2Number.send_keys(cvv2)
        Mounth = self.driver.find_element(By.ID,'txtExpM')
        Mounth.send_keys(month)
        Year = self.driver.find_element(By.ID,'txtExpY')
        Year.send_keys(year)
        sleep(2)
        try:
            subprocess.run(["PowerShell", "-Command", "Add-Type -AssemblyName PresentationFramework;[System.Windows.MessageBox]::Show('It's me again')"], shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running PowerShell command: {e}")
        captcha = input("Enter your captcha : ")
        captchaInput = self.driver.find_element(By.ID, "Captcha")
        captchaInput.send_keys(captcha)
    
        self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[4]/div/div/div[3]/div/form/div[4]/div[2]/div[2]/button").click()
        # end captcha
        # time.sleep(5)
        Pin2 = self.driver.find_element(By.ID,'pin2')
        secPass = input("Watch your mobile, what did u see : ")
        Pin2.send_keys(secPass)
        Purchase = self.driver.find_element(By.ID,'btnPayment')
        sleep(.5)
        Purchase.click()

    def bp(self, cardNumber, cvv2, month, year):
        #In Way
        CardNumber = self.driver.find_element(By.XPATH,'//*[@id="field-0"]')
        CardNumber.send_keys(cardNumber)
        CVV2Number = self.driver.find_element(By.ID,'field-1')
        CVV2Number.send_keys(cvv2)
        Mounth = self.driver.find_element(By.XPATH,'//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[4]/div/div/div/input[1]')
        Mounth.send_keys(month)
        Year = self.driver.find_element(By.XPATH,'//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[4]/div/div/div/input[2]')
        Year.send_keys(year)
        sleep(2)
        captcha = self.driver.find_element(By.CLASS_NAME,'captcha-image')
        loc = captcha.location
        size = captcha.size
        left = loc['x']
        top = loc['y']
        width = size['width']
        height = size['height']
        box = (int(left+2), int(top-2), int(left+width-4), int(top+height-10))
        result = self.captcha_resolver(box, '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[7]/div[2]/button', '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[1]/div/div/div', '//*[@id="field-3"]', '//*[@id="app"]/div/main/div[1]/div/div[1]/div/div/div[2]/div[1]/form/div/div[5]/div/div/div[1]/span/button')
        if result:
            return
        Pin2 = self.driver.find_element(By.ID,'pincode')
        secPass = input("Watch your mobile, what did u see : ")
        Pin2.send_keys(secPass)
        Purchase = self.driver.find_element(By.ID,'purchase')
        sleep(.5)
        Purchase.click()

    def bank_checking(self, state):

        if self.cardNumber == None or self.cardNumber == "":
            WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/ui-view/div[1]/div/div/h2")))
            return
        self.state = state
        if state == 'sep':
            self.sep(self.cardNumber, self.cvv2, self.month, self.year)
        elif state == 'bpm':
            self.bpm(self.cardNumber, self.cvv2, self.month, self.year)
        elif state == 'tep':
            self.tep(self.cardNumber, self.cvv2, self.month, self.year)
        elif state == 'bp':
            self.bp(self.cardNumber, self.cvv2, self.month, self.year)

