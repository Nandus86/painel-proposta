import smtplib
from email.message import EmailMessage
import logging
from app.models.empresa import Empresa

logger = logging.getLogger(__name__)

def send_email_sync(empresa: Empresa, to_email: str, subject: str, html_content: str):
    if not empresa.smtp_host or not empresa.smtp_port or not empresa.smtp_user or not empresa.smtp_password:
        raise ValueError("Configuração SMTP da empresa incompleta.")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = empresa.smtp_user
    msg['To'] = to_email
    msg.set_content("Para visualizar este e-mail, utilize um cliente com suporte a HTML.")
    msg.add_alternative(html_content, subtype='html')

    try:
        server = smtplib.SMTP(empresa.smtp_host, empresa.smtp_port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(empresa.smtp_user, empresa.smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise e
