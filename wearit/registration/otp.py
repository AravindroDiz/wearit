from twilio.rest import Client
import pyotp
from django.contrib import messages
from datetime import datetime,timedelta

def sent_otp(request):
    # Generate a new OTP
    totp = pyotp.TOTP(pyotp.random_base32(), interval=60)
    otp = totp.now()
    request.session['otp_secret_key'] = totp.secret
    valid_date = datetime.now() + timedelta(minutes=1)
    request.session['otp_valid_date'] = str(valid_date)

    # Replace these values with your Twilio account SID and auth token
    account_sid = 'AC83eb13a8bd0db21bfc099c28e5154b4d'
    auth_token = '979a9663c18bef6a10a303ef9780a6a2'

    client = Client(account_sid, auth_token)

    # Replace with your Twilio phone number
    from_number = '+13343842454'
    
    # Replace with the user's phone number you want to send the OTP to
    to_number = '+919745760132'

    try:
        message = client.messages.create(
            body=f"Your OTP is: {otp}",
            from_=from_number,
            to=to_number
        )

        print('OTP sent successfully')
        return True
    except Exception as e:
        print(f'Error sending OTP: {str(e)}')
        messages.error(request, 'Error sending OTP')
        return False
