from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
import os

configuration = Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")

def send_email(subject: str, html_content: str, to_email: str, to_name: str = "Recipient"):
    """
    Send email via Brevo API
    
    Args:
        subject: Email subject
        html_content: HTML formatted email content
        to_email: Recipient email address
        to_name: Recipient name (defaults to "Recipient")
    """
    api_client = None
    try:
        api_client = ApiClient(configuration)
        api_instance = transactional_emails_api.TransactionalEmailsApi(api_client)
        
        send_smtp_email = SendSmtpEmail(
            to=[{
                "email": to_email,
                "name": to_name  # Required field
            }],
            subject=subject,
            html_content=html_content,
            sender={
                "name": "Edith", 
                "email": "edith_naike27@students.uonbi.ac.ke"  # Must be verified
            }
        )
        
        response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent to {to_email}! Message ID: {response.message_id}")
        return {"status": "success", "message_id": response.message_id}
        
    except Exception as e:
        error_msg = f"Failed to send email to {to_email}: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}
        
    finally:
        if api_client:
            # Newer versions don't need close(), but we'll keep it clean
            try:
                if hasattr(api_client, 'close'):
                    api_client.close()
            except:
                pass
            
