from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime
import re

from app.models.proposta import Proposta


def markdown_to_html(text: str) -> str:
    """Converte trechos simples de Markdown para HTML básico."""
    if not text:
        return ""
    
    # Substituir quebras de linha duplas por parágrafos
    paragraphs = text.strip().split("\n\n")
    html_paragraphs = []
    
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
            
        # Headers
        if p_clean.startswith("### "):
            html_paragraphs.append(f"<h3>{p_clean[4:]}</h3>")
        elif p_clean.startswith("## "):
            html_paragraphs.append(f"<h2>{p_clean[3:]}</h2>")
        elif p_clean.startswith("# "):
            html_paragraphs.append(f"<h1>{p_clean[2:]}</h1>")
        # Bullet lists
        elif p_clean.startswith("- ") or p_clean.startswith("* "):
            items = p_clean.split("\n")
            list_items = []
            for item in items:
                item_text = re.sub(r"^[-*]\s+", "", item.strip())
                # Bold inside lists
                item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
                list_items.append(f"<li>{item_text}</li>")
            html_paragraphs.append("<ul>" + "".join(list_items) + "</ul>")
        else:
            # Paragraph with Bold support
            p_clean = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", p_clean)
            p_clean = re.sub(r"\*(.*?)\*", r"<em>\1</em>", p_clean)
            # Support simple inline lists or line breaks inside paragraph
            p_clean = p_clean.replace("\n", "<br/>")
            html_paragraphs.append(f"<p>{p_clean}</p>")
            
    return "\n".join(html_paragraphs)


def generate_proposal_pdf(proposta: Proposta) -> bytes:
    """Gera um PDF em bytes a partir do modelo de Proposta utilizando xhtml2pdf."""
    empresa = proposta.empresa
    cliente = proposta.cliente
    
    # Formatação de datas
    data_emissao_str = proposta.data_emissao.strftime("%d/%m/%Y")
    data_validade_str = proposta.data_validade.strftime("%d/%m/%Y") if proposta.data_validade else "—"
    
    # Converter Markdown das observações para HTML
    corpo_html = markdown_to_html(proposta.observacoes)
    
    # Tabela de itens
    itens_html = ""
    for idx, item in enumerate(proposta.items):
        preco_unit = f"R$ {item.preco_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        subtotal = f"R$ {item.subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        itens_html += f"""
        <tr>
            <td style="text-align: center;">{idx + 1}</td>
            <td>{item.descricao}</td>
            <td style="text-align: center;">{int(item.quantidade) if item.quantidade == int(item.quantidade) else item.quantidade}</td>
            <td style="text-align: right;">{preco_unit}</td>
            <td style="text-align: right; font-weight: bold;">{subtotal}</td>
        </tr>
        """
        
    valor_total_str = f"R$ {proposta.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # CSS Customizado com a Identidade de Cores (Clara, tons de cinza e pêssego/ouro)
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
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                color: #212529;
                font-size: 10pt;
                line-height: 1.5;
            }}
            .header-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}
            .header-left {{
                width: 60%;
                vertical-align: top;
            }}
            .header-right {{
                width: 40%;
                text-align: right;
                vertical-align: top;
            }}
            .brand-title {{
                font-size: 20pt;
                font-weight: bold;
                color: #f39c12; /* Pêssego/Ouro */
                margin: 0;
            }}
            .brand-subtitle {{
                font-size: 8pt;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 2px;
            }}
            .proposal-badge {{
                display: inline-block;
                background-color: #f39c12;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                margin-bottom: 10px;
                text-align: center;
            }}
            .info-grid {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}
            .info-block {{
                width: 50%;
                vertical-align: top;
                border: 1px solid #dee2e6;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }}
            .info-block h4 {{
                margin: 0 0 8px 0;
                color: #495057;
                font-size: 9pt;
                text-transform: uppercase;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 4px;
            }}
            .info-block p {{
                margin: 2px 0;
                font-size: 9pt;
            }}
            .section-title {{
                font-size: 12pt;
                font-weight: bold;
                color: #d6810a;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 4px;
                margin-top: 20px;
                margin-bottom: 10px;
            }}
            .proposta-corpo {{
                margin-bottom: 25px;
                font-size: 9.5pt;
                text-align: justify;
            }}
            .proposta-corpo h2 {{ font-size: 12pt; color: #495057; margin-top: 15px; }}
            .proposta-corpo h3 {{ font-size: 11pt; color: #495057; margin-top: 10px; }}
            .proposta-corpo p {{ margin: 0 0 10px 0; }}
            .proposta-corpo ul {{ margin: 0 0 10px 20px; padding: 0; }}
            .proposta-corpo li {{ margin-bottom: 4px; }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}
            .items-table th {{
                background-color: #dee2e6;
                color: #212529;
                font-size: 9pt;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #ced4da;
            }}
            .items-table td {{
                padding: 8px;
                font-size: 9pt;
                border: 1px solid #dee2e6;
                vertical-align: middle;
            }}
            .total-row {{
                background-color: #fffcf0;
            }}
            .total-row td {{
                border-top: 2px solid #f39c12;
            }}
            .signature-section {{
                margin-top: 50px;
                width: 100%;
                border-collapse: collapse;
            }}
            .signature-box {{
                width: 45%;
                text-align: center;
                vertical-align: top;
            }}
            .signature-line {{
                border-top: 1px solid #adb5bd;
                margin-top: 40px;
                padding-top: 5px;
                font-size: 9pt;
                color: #495057;
            }}
        </style>
    </head>
    <body>
        <!-- Footer definition for xhtml2pdf -->
        <div id="footer_content" style="font-size: 8pt; color: #6c757d;">
            <table style="width: 100%; border: none;">
                <tr>
                    <td style="text-align: left; border: none;">{empresa.nome_fantasia or empresa.razao_social} • Proposta #{proposta.numero}</td>
                    <td style="text-align: right; border: none;">Página <pdf:pagenumber> de <pdf:pagecount></td>
                </tr>
            </table>
        </div>

        <!-- Header -->
        <table class="header-table">
            <tr>
                <td class="header-left">
                    <div class="brand-title">{empresa.nome_fantasia or empresa.razao_social}</div>
                    <div class="brand-subtitle">PROPOSTA COMERCIAL</div>
                    <p style="margin: 8px 0 0 0; font-size: 8.5pt; color: #6c757d; line-height: 1.3;">
                        CNPJ: {empresa.cnpj}<br/>
                        {f"Email: {empresa.email} | " if empresa.email else ""}{f"Fone: {empresa.telefone}" if empresa.telefone else ""}<br/>
                        {empresa.endereco or ""}, {empresa.cidade or ""} - {empresa.estado or ""}
                    </p>
                </td>
                <td class="header-right">
                    <div class="proposal-badge">Proposta #{proposta.numero}</div>
                    <p style="margin: 0; font-size: 9pt; color: #495057;">
                        <strong>Emissão:</strong> {data_emissao_str}<br/>
                        <strong>Validade:</strong> {data_validade_str}
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- Info Blocks -->
        <table class="info-grid">
            <tr>
                <td class="info-block" style="padding-right: 15px;">
                    <h4>Dados do Cliente</h4>
                    <p><strong>{cliente.razao_social}</strong></p>
                    {f"<p>CNPJ/CPF: {cliente.cnpj}</p>" if cliente.cnpj else ""}
                    {f"<p>Responsável: {cliente.contato_nome}</p>" if cliente.contato_nome else ""}
                    {f"<p>Email: {cliente.email}</p>" if cliente.email else ""}
                    {f"<p>Telefone: {cliente.telefone}</p>" if cliente.telefone else ""}
                </td>
                <td style="width: 4%;"></td>
                <td class="info-block">
                    <h4>Identificação do Projeto</h4>
                    <p><strong>Assunto:</strong> {proposta.titulo}</p>
                    <p><strong>Elaborado por:</strong> {proposta.usuario.nome}</p>
                    {f"<p>Cargo: {proposta.usuario.cargo}</p>" if proposta.usuario.cargo else ""}
                    <p><strong>Status:</strong> {proposta.status.value.upper()}</p>
                </td>
            </tr>
        </table>
        
        <!-- Proposal Body Text -->
        <div class="section-title">Descrição Geral & Escopo</div>
        <div class="proposta-corpo">
            {corpo_html}
        </div>
        
        <!-- Proposal Items / Financials -->
        <div class="section-title" style="page-break-before: auto;">Especificação de Valores</div>
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width: 5%;">Item</th>
                    <th style="width: 50%;">Descrição</th>
                    <th style="width: 10%;">Qtd</th>
                    <th style="width: 15%;">Preço Unit.</th>
                    <th style="width: 20%;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {itens_html}
                <tr class="total-row">
                    <td colspan="3" style="border: none; background: white;"></td>
                    <td style="text-align: right; font-weight: bold;">Valor Geral:</td>
                    <td style="text-align: right; font-weight: bold; font-size: 11pt; color: #b06603;">{valor_total_str}</td>
                </tr>
            </tbody>
        </table>
        
        <!-- payment terms -->
        {f'<div class="section-title">Condições de Pagamento</div><p style="font-size: 9.5pt;">{proposta.condicoes_pagamento}</p>' if proposta.condicoes_pagamento else ""}
        
        <!-- Signatures -->
        <table class="signature-section">
            <tr>
                <td class="signature-box">
                    <div class="signature-line">
                        {empresa.razao_social}<br/>
                        Responsável Técnico/Comercial
                    </div>
                </td>
                <td style="width: 10%;"></td>
                <td class="signature-box">
                    <div class="signature-line">
                        {cliente.razao_social}<br/>
                        De acordo do Cliente
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    pdf_buffer = BytesIO()
    # Converter HTML para PDF usando Pisa
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=pdf_buffer
    )
    
    if pisa_status.err:
        raise Exception(f"Erro ao converter HTML para PDF: {pisa_status.err}")
        
    return pdf_buffer.getvalue()
