import html
import re
from datetime import datetime
from io import BytesIO
from typing import Optional
from zoneinfo import ZoneInfo

from xhtml2pdf import pisa

DEFAULT_BRAND_COLOR = "#f39c12"
DEFAULT_TZ = "America/Sao_Paulo"


def fmt_date(dt: Optional[datetime], tz_name: Optional[str] = None) -> str:
    """dd/mm/aaaa no fuso da empresa (datas vêm do banco em UTC)."""
    if not dt:
        return "—"
    if dt.tzinfo is not None:
        try:
            dt = dt.astimezone(ZoneInfo(tz_name or DEFAULT_TZ))
        except Exception:
            dt = dt.astimezone(ZoneInfo(DEFAULT_TZ))
    return dt.strftime("%d/%m/%Y")


def format_brl(value) -> str:
    return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _inline(text: str) -> str:
    """Formatação inline de Markdown sobre texto JÁ escapado."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    # [texto](https://...)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        text,
    )
    # URLs soltas
    text = re.sub(r'(?<!["\'>=])(https?://[^\s<]+)', r'<a href="\1">\1</a>', text)
    return text


def markdown_to_html(text: Optional[str]) -> str:
    """Converte um subconjunto de Markdown em HTML seguro (todo o texto é escapado antes)."""
    if not text:
        return ""

    blocks = html.escape(text.replace("\r\n", "\n")).strip().split("\n\n")
    out = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            out.append(f"<h3>{_inline(block[4:])}</h3>")
        elif block.startswith("## "):
            out.append(f"<h2>{_inline(block[3:])}</h2>")
        elif block.startswith("# "):
            out.append(f"<h1>{_inline(block[2:])}</h1>")
        elif block.startswith(("- ", "* ")):
            items = [re.sub(r"^[-*]\s+", "", line.strip()) for line in block.split("\n") if line.strip()]
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
        elif re.match(r"^\d+[.)]\s", block):
            items = [re.sub(r"^\d+[.)]\s+", "", line.strip()) for line in block.split("\n") if line.strip()]
            out.append("<ol>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ol>")
        else:
            out.append(f"<p>{_inline(block).replace(chr(10), '<br/>')}</p>")
    return "\n".join(out)


def _safe_color(value: Optional[str]) -> str:
    if value and re.fullmatch(r"#?[0-9a-fA-F]{6}", value.strip()):
        v = value.strip()
        return v if v.startswith("#") else f"#{v}"
    return DEFAULT_BRAND_COLOR


def _fmt_qtd(q) -> str:
    q = float(q or 0)
    return str(int(q)) if q == int(q) else f"{q:.2f}".replace(".", ",")


def generate_proposal_pdf(proposta, tipo_doc: str = "Proposta", logo_src: Optional[str] = None) -> bytes:
    """Gera o PDF (bytes) de uma proposta ou orçamento.

    `logo_src` deve ser um data URI já resolvido pelo chamador (nunca uma URL arbitrária:
    o xhtml2pdf buscaria o endereço, abrindo brecha de SSRF).
    """
    from app.schemas.empresa import documento_publico

    empresa = proposta.empresa
    cliente = proposta.cliente
    usuario = getattr(proposta, "usuario", None)
    cor = _safe_color(getattr(empresa, "cor_marca", None))
    empresa_nome = _esc(empresa.nome_fantasia or empresa.razao_social)
    numero = _esc(proposta.numero or "—")
    tipo = _esc(tipo_doc)

    logo_html = ""
    if logo_src and logo_src.startswith("data:image/"):
        logo_html = f'<img src="{logo_src}" style="max-height: 50px; max-width: 180px; margin-bottom: 8px;" /><br/>'

    tz = getattr(empresa, "fuso_horario", None)
    data_emissao_str = fmt_date(proposta.data_emissao, tz)
    data_validade_str = fmt_date(proposta.data_validade, tz)

    corpo_html = markdown_to_html(proposta.observacoes)

    tem_desconto = any(float(item.desconto or 0) > 0 for item in proposta.items)
    itens_html = ""
    for idx, item in enumerate(proposta.items):
        desconto_td = f'<td style="text-align: right;">{format_brl(item.desconto)}</td>' if tem_desconto else ""
        itens_html += f"""
        <tr>
            <td style="text-align: center;">{idx + 1}</td>
            <td>{_esc(item.descricao)}</td>
            <td style="text-align: center;">{_fmt_qtd(item.quantidade)}</td>
            <td style="text-align: right;">{format_brl(item.preco_unitario)}</td>
            {desconto_td}
            <td style="text-align: right; font-weight: bold;">{format_brl(item.subtotal)}</td>
        </tr>
        """
    desconto_th = '<th style="width: 12%;">Desconto</th>' if tem_desconto else ""
    colspan_total = 4 if tem_desconto else 3

    cnpj_empresa = documento_publico(empresa.cnpj)
    linha_contato = " | ".join(
        p for p in [f"Email: {_esc(empresa.email)}" if empresa.email else "", f"Fone: {_esc(empresa.telefone)}" if empresa.telefone else ""] if p
    )
    linha_endereco = ", ".join(_esc(p) for p in [empresa.endereco, empresa.cidade] if p)
    if empresa.estado:
        linha_endereco = f"{linha_endereco} - {_esc(empresa.estado)}" if linha_endereco else _esc(empresa.estado)
    info_empresa = "<br/>".join(
        p for p in [f"CNPJ: {_esc(cnpj_empresa)}" if cnpj_empresa else "", linha_contato, linha_endereco] if p
    )
    doc_cliente = cliente.cnpj or cliente.cpf
    status_val = proposta.status.value if hasattr(proposta.status, "value") else str(proposta.status or "")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4;
                margin: 2cm 1.5cm 2cm 1.5cm;
                @frame footer {{
                    -pdf-frame-content: footer_content;
                    bottom: 1cm;
                    margin-left: 1.5cm;
                    margin-right: 1.5cm;
                    height: 1cm;
                }}
            }}
            body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #212529; font-size: 10pt; line-height: 1.5; }}
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
            .header-left {{ width: 60%; vertical-align: top; }}
            .header-right {{ width: 40%; text-align: right; vertical-align: top; }}
            .brand-title {{ font-size: 20pt; font-weight: bold; color: {cor}; margin: 0; }}
            .brand-subtitle {{ font-size: 8pt; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }}
            .proposal-badge {{ background-color: {cor}; color: white; font-size: 11pt; font-weight: bold; padding: 6px 12px; margin-bottom: 10px; text-align: center; }}
            .info-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
            .info-block {{ width: 48%; vertical-align: top; border: 1px solid #dee2e6; padding: 10px; background-color: #f8f9fa; }}
            .info-block h4 {{ margin: 0 0 8px 0; color: #495057; font-size: 9pt; text-transform: uppercase; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; }}
            .info-block p {{ margin: 2px 0; font-size: 9pt; }}
            .section-title {{ font-size: 12pt; font-weight: bold; color: {cor}; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; margin-top: 20px; margin-bottom: 10px; }}
            .proposta-corpo {{ margin-bottom: 25px; font-size: 9.5pt; text-align: justify; }}
            .proposta-corpo h1 {{ font-size: 14pt; color: #343a40; margin-top: 15px; }}
            .proposta-corpo h2 {{ font-size: 12pt; color: #495057; margin-top: 15px; }}
            .proposta-corpo h3 {{ font-size: 11pt; color: #495057; margin-top: 10px; }}
            .proposta-corpo p {{ margin: 0 0 10px 0; }}
            .proposta-corpo ul, .proposta-corpo ol {{ margin: 0 0 10px 20px; padding: 0; }}
            .proposta-corpo li {{ margin-bottom: 4px; }}
            .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
            .items-table th {{ background-color: #dee2e6; color: #212529; font-size: 9pt; font-weight: bold; padding: 8px; border: 1px solid #ced4da; }}
            .items-table td {{ padding: 8px; font-size: 9pt; border: 1px solid #dee2e6; vertical-align: middle; }}
            .total-row td {{ border-top: 2px solid {cor}; }}
            .signature-section {{ margin-top: 50px; width: 100%; border-collapse: collapse; }}
            .signature-box {{ width: 45%; text-align: center; vertical-align: top; }}
            .signature-line {{ border-top: 1px solid #adb5bd; margin-top: 40px; padding-top: 5px; font-size: 9pt; color: #495057; }}
        </style>
    </head>
    <body>
        <div id="footer_content" style="font-size: 8pt; color: #6c757d;">
            <table style="width: 100%; border: none;">
                <tr>
                    <td style="text-align: left; border: none;">{empresa_nome} • {tipo} #{numero}</td>
                    <td style="text-align: right; border: none;">Página <pdf:pagenumber> de <pdf:pagecount></td>
                </tr>
            </table>
        </div>

        <table class="header-table">
            <tr>
                <td class="header-left">
                    {logo_html}
                    <div class="brand-title">{empresa_nome}</div>
                    <div class="brand-subtitle">{tipo} comercial</div>
                    <p style="margin: 8px 0 0 0; font-size: 8.5pt; color: #6c757d; line-height: 1.3;">{info_empresa}</p>
                </td>
                <td class="header-right">
                    <div class="proposal-badge">{tipo} #{numero}</div>
                    <p style="margin: 0; font-size: 9pt; color: #495057;">
                        <strong>Emissão:</strong> {data_emissao_str}<br/>
                        <strong>Validade:</strong> {data_validade_str}
                    </p>
                </td>
            </tr>
        </table>

        <table class="info-grid">
            <tr>
                <td class="info-block">
                    <h4>Dados do Cliente</h4>
                    <p><strong>{_esc(cliente.razao_social)}</strong></p>
                    {f"<p>CNPJ/CPF: {_esc(doc_cliente)}</p>" if doc_cliente else ""}
                    {f"<p>Responsável: {_esc(cliente.contato_nome)}</p>" if cliente.contato_nome else ""}
                    {f"<p>Email: {_esc(cliente.email)}</p>" if cliente.email else ""}
                    {f"<p>Telefone: {_esc(cliente.telefone)}</p>" if cliente.telefone else ""}
                </td>
                <td style="width: 4%;"></td>
                <td class="info-block">
                    <h4>Identificação</h4>
                    <p><strong>Assunto:</strong> {_esc(proposta.titulo)}</p>
                    {f"<p><strong>Elaborado por:</strong> {_esc(usuario.nome)}</p>" if usuario else ""}
                    {f"<p>Cargo: {_esc(usuario.cargo)}</p>" if usuario and usuario.cargo else ""}
                    <p><strong>Status:</strong> {_esc(status_val.upper())}</p>
                </td>
            </tr>
        </table>

        {f'<div class="section-title">Descrição Geral &amp; Escopo</div><div class="proposta-corpo">{corpo_html}</div>' if corpo_html else ""}

        <div class="section-title">Especificação de Valores</div>
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width: 5%;">Item</th>
                    <th>Descrição</th>
                    <th style="width: 8%;">Qtd</th>
                    <th style="width: 15%;">Preço Unit.</th>
                    {desconto_th}
                    <th style="width: 17%;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {itens_html}
                <tr class="total-row">
                    <td colspan="{colspan_total}" style="border: none; background: white;"></td>
                    <td style="text-align: right; font-weight: bold;">Valor Total:</td>
                    <td style="text-align: right; font-weight: bold; font-size: 11pt; color: {cor};">{format_brl(proposta.valor_total)}</td>
                </tr>
            </tbody>
        </table>

        {f'<div class="section-title">Condições de Pagamento</div><div style="font-size: 9.5pt;">{markdown_to_html(proposta.condicoes_pagamento)}</div>' if proposta.condicoes_pagamento else ""}

        <table class="signature-section">
            <tr>
                <td class="signature-box">
                    <div class="signature-line">{_esc(empresa.razao_social)}<br/>Responsável Técnico/Comercial</div>
                </td>
                <td style="width: 10%;"></td>
                <td class="signature-box">
                    <div class="signature-line">{_esc(cliente.razao_social)}<br/>De acordo do Cliente</div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(src=html_content, dest=pdf_buffer, encoding="utf-8")
    if pisa_status.err:
        raise RuntimeError(f"Erro ao converter HTML para PDF: {pisa_status.err}")
    return pdf_buffer.getvalue()
