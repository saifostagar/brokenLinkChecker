import os

EMAIL_USER = os.getenv('SCRIPT_EMAIL')
EMAIL_PASS = os.getenv('SCRIPT_PASS') # create your apppassword from here https://myaccount.google.com/apppasswords for gmail
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT= os.getenv('SMTP_PORT')
EMAIL_TO = 'saifostagar@gmail.com'
print(EMAIL_USER)