import africastalking

# Initialize SDK
username = "sandbox"       # Your Africa's Talking username
api_key = "0f6cb88ba15c5882c7363bf91e357c8faf6df66dfd9dd4e20c240798ef95ca14"         # Your API key from the dashboard
africastalking.initialize(username, api_key)

sms = africastalking.SMS

# Send bulk SMS
recipients = ["+2547021718141", "+254713297541"]  # List of phone numbers
message = "This patient has high levels of glucose in the blood. Please take necessary action."
sender_id = "Masterclass"  # Optional and must be approved

response = sms.send(message, recipients, sender_id=sender_id)
print(response)

try:
        # Set the numbers you want to send to in international format
        recipients = ["+2547021718141", "+254713297541"]
        
        # Set your message
        message = "This patient has high levels of glucose in the blood. Please take necessary action."
        
        # Set your sender ID (alphanumeric for some countries)
        sender = "Masterclass"  # or shortcode if you have one
        
        # Send the SMS
        response = sms.send(message, recipients, sender)
        print(response)
except Exception as e:
        print(f"Error: {e}")
