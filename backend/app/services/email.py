import html
import logging
import smtplib
import socket
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app.config import settings
from app.core.security import decrypt_data
from app.models.empresa import Empresa
from app.schemas.empresa import documento_publico
from app.services.pdf import fmt_date, format_brl, markdown_to_html

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 20


def smtp_error_message(exc: Exception) -> str:
    """Mensagem amigável para falhas de SMTP (sem expor detalhes internos)."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "usuário ou senha SMTP recusados pelo servidor."
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return "o endereço de destino foi recusado pelo servidor."
    if isinstance(exc, smtplib.SMTPSenderRefused):
        return "o remetente foi recusado pelo servidor (verifique o usuário SMTP)."
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "tempo esgotado ao conectar ao servidor SMTP (verifique host e porta)."
    if isinstance(exc, (socket.gaierror, ConnectionRefusedError, OSError)) and not isinstance(exc, smtplib.SMTPException):
        return "não foi possível conectar ao servidor SMTP (verifique host e porta)."
    if isinstance(exc, ValueError):
        return str(exc)
    return "erro no servidor SMTP."


def _smtp_send(
    host: str,
    port: int,
    user: str,
    password: str,
    from_name: str,
    from_addr: str,
    to_email: str,
    subject: str,
    html_content: str,
    reply_to: str | None = None,
) -> None:
    """Núcleo de envio SMTP (porta 465 = SSL implícito, demais = STARTTLS quando suportado)."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_addr))
    msg["To"] = to_email
    msg["Message-ID"] = make_msgid()
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content("Para visualizar este e-mail, utilize um cliente com suporte a HTML.")
    msg.add_alternative(html_content, subtype="html")

    context = ssl.create_default_context()
    port = int(port)
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT, context=context) as server:
                if user:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT) as server:
                server.ehlo()
                if server.has_extn("starttls"):
                    server.starttls(context=context)
                    server.ehlo()
                if user:
                    server.login(user, password)
                server.send_message(msg)
    except Exception as e:
        logger.error("Falha ao enviar e-mail para %s via %s:%s: %s", to_email, host, port, e)
        raise


def send_email_sync(empresa: Empresa, to_email: str, subject: str, html_content: str, reply_to: str | None = None):
    """Envia um e-mail HTML usando o SMTP configurado pela empresa."""
    if not smtp_configurado(empresa):
        raise ValueError("Configuração SMTP da empresa incompleta.")

    real_password = decrypt_data(empresa.smtp_password)
    if not real_password:
        raise ValueError("Não foi possível ler a senha SMTP salva. Cadastre a senha novamente.")

    _smtp_send(
        host=empresa.smtp_host,
        port=empresa.smtp_port,
        user=empresa.smtp_user,
        password=real_password,
        from_name=empresa.nome_fantasia or empresa.razao_social or settings.APP_NAME,
        from_addr=empresa.smtp_user,
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        reply_to=reply_to or empresa.email,
    )
    return True


def system_smtp_configurado() -> bool:
    return bool(settings.SMTP_HOST and (settings.SMTP_FROM or settings.SMTP_USER))


def send_system_email(to_email: str, subject: str, html_content: str) -> None:
    """Envia um e-mail da plataforma (SMTP definido no .env)."""
    if not system_smtp_configurado():
        raise ValueError("SMTP do sistema não configurado.")
    _smtp_send(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        user=settings.SMTP_USER or "",
        password=settings.SMTP_PASSWORD or "",
        from_name=settings.APP_NAME,
        from_addr=settings.SMTP_FROM or settings.SMTP_USER,
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


def send_notification_email(empresa: Empresa, to_email: str, subject: str, html_content: str) -> bool:
    """Aviso interno (ex.: proposta aceita): usa o SMTP do sistema e, na falta dele, o da empresa.

    Nunca levanta exceção: falha de aviso não pode quebrar o fluxo principal.
    """
    try:
        if system_smtp_configurado():
            send_system_email(to_email, subject, html_content)
            return True
        if smtp_configurado(empresa):
            send_email_sync(empresa, to_email, subject, html_content)
            return True
    except Exception:
        logger.exception("Falha ao enviar aviso por e-mail para %s", to_email)
    return False


def render_system_email(titulo: str, paragrafos: list[str], botao_label: str | None = None,
                        botao_link: str | None = None, cor: str = "#4f46e5") -> str:
    """Template HTML padrão dos e-mails da plataforma. `paragrafos` são textos simples (serão escapados)."""
    corpo = "".join(
        f'<p style="margin: 0 0 14px 0; line-height: 1.6;">{html.escape(p)}</p>' for p in paragrafos
    )
    botao = _button(botao_link, botao_label, cor) if botao_label and botao_link else ""
    return f"""
    <div style="background: #f4f5f7; padding: 32px 12px; font-family: Arial, Helvetica, sans-serif;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e5e7eb;">
        <div style="height: 6px; background: {cor};"></div>
        <div style="padding: 28px 32px; color: #1f2937; font-size: 15px;">
          <h2 style="margin: 0 0 18px 0; font-size: 20px; color: #111827;">{html.escape(titulo)}</h2>
          {corpo}
          {botao}
        </div>
        <div style="padding: 14px 32px; background: #f9fafb; color: #9ca3af; font-size: 12px; text-align: center;">
          {html.escape(settings.APP_NAME)} — mensagem automática, não responda.
        </div>
      </div>
    </div>
    """


def replace_variables(text: str, variables: dict, escape: bool = False) -> str:
    if not text:
        return ""
    for tag, value in variables.items():
        val = "" if value is None else str(value)
        if escape:
            val = html.escape(val)
        text = text.replace(f"{{{{{tag}}}}}", val)
    return text


def smtp_configurado(empresa: Empresa) -> bool:
    return bool(empresa.smtp_host and empresa.smtp_port and empresa.smtp_user and empresa.smtp_password)


def build_email_variables(empresa, doc, is_orcamento=False) -> dict:
    """Variáveis disponíveis nos textos de e-mail/WhatsApp (inclui as tags do catálogo de modelos)."""
    cliente = doc.cliente
    usuario = getattr(doc, "usuario", None)
    empresa_nome = empresa.nome_fantasia or empresa.razao_social
    endereco_cliente = ", ".join(p for p in [cliente.endereco, cliente.cidade, cliente.estado] if p)
    endereco_empresa = ", ".join(p for p in [empresa.endereco, empresa.cidade, empresa.estado] if p)
    valor = format_brl(doc.valor_total)
    tz = empresa.fuso_horario

    def _fmt_data(dt):
        return fmt_date(dt, tz)

    variables = {
        # Nomes usados nos modelos padrão de e-mail
        "cliente_razao_social": cliente.razao_social,
        "cliente_nome_fantasia": cliente.nome_fantasia,
        "cliente_contato_nome": cliente.contato_nome or cliente.razao_social,
        "cliente_email": cliente.email,
        "cliente_telefone": cliente.telefone,
        "cliente_cnpj": cliente.cnpj or cliente.cpf,
        "cliente_cidade": cliente.cidade,
        "empresa_razao_social": empresa.razao_social,
        "empresa_nome_fantasia": empresa.nome_fantasia,
        "empresa_email": empresa.email,
        "empresa_telefone": empresa.telefone,
        "empresa_cnpj": documento_publico(empresa.cnpj),
        "empresa_cidade": empresa.cidade,
        "proposta_titulo": doc.titulo,
        "proposta_numero": doc.numero,
        "proposta_valor_total": valor,
        "proposta_data_emissao": _fmt_data(doc.data_emissao),
        "proposta_data_validade": _fmt_data(doc.data_validade),
        "vendedor_nome": usuario.nome if usuario else "",
        "vendedor_email": usuario.email if usuario else "",
        "vendedor_telefone": (usuario.telefone or "") if usuario else "",
        "vendedor_cargo": (usuario.cargo or "") if usuario else "",
        "data_atual": _fmt_data(doc.data_emissao),
        # Tags do catálogo exibido no editor (VariablePalette)
        "cliente": cliente.razao_social,
        "cliente_fantasia": cliente.nome_fantasia,
        "cliente_contato": cliente.contato_nome or cliente.razao_social,
        "cliente_endereco": endereco_cliente,
        "empresa": empresa_nome,
        "empresa_endereco": endereco_empresa,
        "empresa_responsavel": usuario.nome if usuario else "",
        "valor_total": valor,
        "condicoes_pagamento": doc.condicoes_pagamento,
        "data_emissao": _fmt_data(doc.data_emissao),
        "data_validade": _fmt_data(doc.data_validade),
        "validade_dias": doc.validade_dias,
    }
    return variables


def _button(link: str, label: str, color: str) -> str:
    return (
        '<div style="margin: 30px 0; text-align: center;">'
        f'<a href="{html.escape(link, quote=True)}" style="background-color: {color}; color: #ffffff; padding: 12px 24px; '
        'text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">'
        f"{html.escape(label)}</a></div>"
    )


def get_email_content(empresa: Empresa, doc, link: str, is_orcamento=False) -> tuple[str, str]:
    variables = build_email_variables(empresa, doc, is_orcamento)
    variables["link_proposta"] = link

    tipo_doc = "Orçamento" if is_orcamento else "Proposta"
    artigo = "um" if is_orcamento else "uma"
    label_botao = f"Visualizar {tipo_doc}"
    empresa_nome = empresa.nome_fantasia or empresa.razao_social
    default_subject = f"{tipo_doc} #{doc.numero} - {empresa_nome}"

    default_body = f"""Olá, {{{{cliente_contato_nome}}}}!

A empresa **{{{{empresa}}}}** enviou {artigo} {tipo_doc.lower()} comercial para você.

**Título:** {{{{proposta_titulo}}}}
**Valor total:** {{{{proposta_valor_total}}}}

{{{{botao_link}}}}

Se tiver qualquer dúvida, basta responder a este e-mail."""

    assunto = replace_variables(empresa.email_assunto_padrao or default_subject, variables).replace("\n", " ").strip()

    corpo_raw = empresa.email_corpo_padrao or default_body
    # O botão é inserido depois da conversão; se o modelo não tiver o botão nem o link, adiciona ao final
    if "{{botao_link}}" not in corpo_raw and "{{link_proposta}}" not in corpo_raw:
        corpo_raw += "\n\n{{botao_link}}"
    corpo_md = replace_variables(corpo_raw, variables)
    html_content = markdown_to_html(corpo_md)
    cor = empresa.cor_marca or "#4f46e5"
    botao = _button(link, label_botao, cor)
    html_content = html_content.replace("<p>{{botao_link}}</p>", botao).replace("{{botao_link}}", botao)

    final_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        {html_content}
        <hr style="border: 0; border-top: 1px solid #eaeaea; margin: 20px 0;" />
        <p style="font-size: 12px; color: #888; text-align: center;">Enviado via {html.escape(settings.APP_NAME)}</p>
    </div>
    """

    return assunto, final_html
