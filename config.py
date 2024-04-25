import os

EMAIL_USER = os.getenv('SCRIPT_EMAIL')
EMAIL_PASS = os.getenv('SCRIPT_PASS') # create your apppassword from here https://myaccount.google.com/apppasswords for gmail
EMAIL_TO = 'md.saif@shorthillstech.com'
print('Email will be sent to '+EMAIL_TO)