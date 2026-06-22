# Iranian Bank Payment Automation

A Selenium script that drives Iranian payment gateways: it fills in your card
details and automatically solves the image captcha using OpenCV preprocessing
plus Tesseract OCR. You bring the WebDriver and navigate to the payment page;
the script takes over from the card form onward.

> The whole flow runs through Selenium, so you must pass your own driver into the script.

## Supported gateways

| Code  | Gateway     | Captcha             |
|-------|-------------|---------------------|
| `sep` | SAMAN       | Auto (OCR)          |
| `bpm` | BehPardakht | Auto (OCR)          |
| `bp`  | Pasargad    | Auto (OCR)          |
| `tep` | Tejarat     | Manual entry        |

## Requirements

Python packages:

```
opencv-python
pillow
pytesseract
selenium
```

You also need the **Tesseract OCR** engine installed. This project targets
**Windows** — the path is configured at the top of `banks.py`:

```python
TESSERACT_CMD = r"C:\Program Files\tocr\tesseract.exe"
```

Adjust that constant if your Tesseract install lives elsewhere.

## Usage

Create the object with your card info and an active driver, then route to the
gateway you've navigated to:

```python
from banks import Banking

bank = Banking(card_number, cvv2, month, year, driver)
bank.bank_checking("sep")   # one of: sep, bpm, tep, bp
```

The script fills the card form, solves (or prompts for) the captcha, then asks
you for the OTP / second password shown on your phone before confirming the
payment.

## Notes ⚠️

This is still a work in progress. Captcha solving uses image processing, so it
is not 100% reliable — on a failed read the script automatically refreshes and
retries (up to a capped number of attempts).

Approximate per-gateway OCR accuracy:

- SAMAN — ~70%
- BehPardakht — ~50%
- Pasargad — ~75%

Tejarat captcha is **not** auto-solved; you enter it manually when prompted.

Contributions to improve OCR accuracy and reliability are very welcome 🤗
