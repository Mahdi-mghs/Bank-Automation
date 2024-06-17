# Automation Iranian Bank
here's a script code to automate your bank, you can guide your driver to the payway and confirm your transaction by give your card information
> All process happening in selenium, so it's necessary to use your driver in script
## Library needed
```
opencv-python
pillow
pybase64
pytesseract
```
also selenium for your driver

## How to use
just give your card info and driver
```
Banking(cardNumber, cvv2, monthExpier, yearExpier, driver)
```

## It's not completed yet ⚠️
This code uses the opencv library and image processing to extract the numbers from the photo and place them in the Captcha field.

Here is accuracy of these gates:
- SAMAN Gate 70%
- BehPardakht Gate 50%
- Pasargard Gate 75%

And it is not defined for the Tejarat port, you have to enter it manually
I will be happy to help me in the advancement of this automation 🤗
