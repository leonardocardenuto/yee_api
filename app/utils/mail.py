import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import smtp_server, sender_email, sender_password, port, logger

def send_mail(type,receiver_email,code = None):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Redefinição de senha"

    match type:
        case 'welcome':
            html = f"""
                <html>
                <body>
                    <p>Hello,</p>
                    <p>Thanks for signing up with us to use Ye - gestao de saude.</p>
                    <p>If you ever have questions, run into problems, consider an upgrade or anything at all, don’t hesitate to reach out to us via email [ADDRESS] or you can connect with us directly using the contact information below.</p>
                    <p>Looking forward to hearing from you soon!</p>
                    <p>Regards,</p>
                    <p>Equipe Ye</p>
                </body>
                </html>
                """
        case _:
            html = f"""
            <html>
            <body>
                <p>Hi,</p>
                <p>We just need to verify your email address before you can access Ye app.</p>
                <p>Verify your email address <strong>{code}</strong></p>
                <p>Thanks! – The Ye team</p>
            </body>
            </html>
            """

    part1 = MIMEText(html, "html")
    message.attach(part1)

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()
        server.starttls(context=context)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        logger.info("Email sent!")
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return True
    finally:
        server.quit()
