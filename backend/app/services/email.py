import smtplib
from email.message import EmailMessage
import logging
import re
from app.models.empresa import Empresa
from app.core.security import decrypt_data
from app.services.pdf import markdown_to_html

logger = logging.getLogger(__name__)

def send_email_sync(empresa: Empresa, to_email: str, subject: str, html_content: str):
    if not empresa.smtp_host or not empresa.smtp_port or not empresa.smtp_user or not empresa.smtp_password:
        raise ValueError("Configuração SMTP da empresa incompleta.")

    # A senha está criptografada no banco
    real_password = decrypt_data(empresa.smtp_password)
    if not real_password:
        raise ValueError("Falha ao descriptografar a senha SMTP da empresa.")

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
        server.login(empresa.smtp_user, real_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise e

def replace_variables(text: str, variables: dict) -> str:
    if not text:
        return ""
    for tag, value in variables.items():
        text = text.replace(f"{{{{{tag}}}}}", str(value) if value is not None else "")
    return text

def build_email_variables(empresa, doc, is_orcamento=False) -> dict:
    # doc is either Proposta or Orcamento
    cliente = doc.cliente
    variables = {
        "cliente_razao_social": cliente.razao_social,
        "cliente_nome_fantasia": cliente.nome_fantasia,
        "cliente_contato_nome": cliente.contato_nome or cliente.razao_social,
        "cliente_email": cliente.email,
        "cliente_telefone": cliente.telefone,
        "cliente_cnpj": cliente.cnpj,
        "cliente_cidade": cliente.cidade,
        
        "empresa_razao_social": empresa.razao_social,
        "empresa_nome_fantasia": empresa.nome_fantasia,
        "empresa_email": empresa.email,
        "empresa_telefone": empresa.telefone,
        "empresa_cnpj": empresa.cnpj,
        "empresa_cidade": empresa.cidade,

        "proposta_titulo": doc.titulo,
        "proposta_numero": doc.numero,
        "proposta_valor_total": f"R$ {doc.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "proposta_data_emissao": doc.data_emissao.strftime("%d/%m/%Y"),
        "proposta_data_validade": doc.data_validade.strftime("%d/%m/%Y") if doc.data_validade else "—",
        
        "vendedor_nome": doc.usuario.nome if getattr(doc, "usuario", None) else "",
        "vendedor_email": doc.usuario.email if getattr(doc, "usuario", None) else "",
        "vendedor_telefone": doc.usuario.telefone if getattr(doc, "usuario", None) else "",
        "vendedor_cargo": doc.usuario.cargo if getattr(doc, "usuario", None) else "",
        
        "data_atual": doc.data_emissao.strftime("%d/%m/%Y"),
        "data_extenso": doc.data_emissao.strftime("%d de %B de %Y")
    }
    return variables

def get_email_content(empresa: Empresa, doc, link: str, is_orcamento=False) -> tuple[str, str]:
    variables = build_email_variables(empresa, doc, is_orcamento)
    
    tipo_doc = "Orçamento" if is_orcamento else "Proposta"
    default_subject = f"{tipo_doc} Comercial #{doc.numero} - {empresa.razao_social}"
    
    default_body = f"""
Olá, {{{{cliente_contato_nome}}}}!

A empresa **{{{{empresa_razao_social}}}}** enviou uma {tipo_doc.lower()} comercial para você.

**Título:** {{{{proposta_titulo}}}}
**Valor Total:** {{{{proposta_valor_total}}}}

[Visualizar {tipo_doc} Completa]({link})

Se tiver qualquer dúvida, basta responder a este e-mail.
"""
    
    assunto_raw = empresa.email_assunto_padrao or default_subject
    corpo_raw = empresa.email_corpo_padrao or default_body
    
    # Processa Markdown e converte botões
    corpo_raw = corpo_raw.replace(f"[Visualizar {tipo_doc} Completa]({link})", f'<div style="margin: 30px 0; text-align: center;"><a href="{link}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Visualizar {tipo_doc} Completa</a></div>')
    
    assunto = replace_variables(assunto_raw, variables)
    corpo = replace_variables(corpo_raw, variables)
    
    html_content = markdown_to_html(corpo)
    
    final_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        {html_content}
        <hr style="border: 0; border-top: 1px solid #eaeaea; margin: 20px 0;" />
        <p style="font-size: 12px; color: #888; text-align: center;">Enviado via Painel Proposta</p>
    </div>
    """
    
    return assunto, final_html
