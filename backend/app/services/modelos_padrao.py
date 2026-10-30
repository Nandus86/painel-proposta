"""Modelos de proposta padrão do sistema (Serviço, Produto e Comercial).

Criados automaticamente quando uma nova empresa inicia no sistema,
podendo ser personalizados, excluídos ou complementados pelo usuário a qualquer momento.
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modelo_proposta import ModeloProposta


MODELOS_PADRAO = [
    {
        "titulo": "Proposta de Prestação de Serviços",
        "conteudo": (
            "# Proposta de Prestação de Serviços Profissionais\n\n"
            "**Cliente:** {{cliente}} (A/C: {{cliente_contato}})\n"
            "**Emitente:** {{empresa}}\n"
            "**Documento:** {{proposta_titulo}} | **Nº:** {{proposta_numero}}\n"
            "**Data de Emissão:** {{data_emissao}} | **Validade:** {{validade_dias}} dias (até {{data_validade}})\n\n"
            "---\n\n"
            "## 1. Apresentação e Objetivo\n"
            "A **{{empresa}}** tem a honra de submeter à **{{cliente}}** esta proposta comercial e técnica para a prestação de serviços especializados. Nosso compromisso é entregar soluções de alta qualidade técnica, com agilidade, transparência e foco nos resultados estratégicos do seu negócio.\n\n"
            "## 2. Escopo dos Serviços e Metodologia\n"
            "Os serviços contemplados nesta proposta compreendem o diagnóstico, planejamento, execução e homologação das soluções descritas a seguir:\n\n"
            "{{itens}}\n\n"
            "### Metodologia de Trabalho:\n"
            "- **Alinhamento Inicial:** Definição conjunta de cronograma, responsáveis e marcos de entrega.\n"
            "- **Execução e Controle:** Acompanhamento periódico com validações parciais para assegurar conformidade.\n"
            "- **Entrega e Garantia:** Homologação final com suporte e atendimento dedicado a dúvidas.\n\n"
            "## 3. Investimento e Condições de Pagamento\n"
            "- **Valor Total dos Serviços:** R$ {{valor_total}}\n"
            "- **Condições de Pagamento:** {{condicoes_pagamento}}\n\n"
            "## 4. Prazos e Validade da Proposta\n"
            "- O início das atividades se dará imediatamente após a formalização do aceite.\n"
            "- Esta proposta é válida até **{{data_validade}}** ({{validade_dias}} dias a contar da emissão).\n\n"
            "---\n\n"
            "Ficamos à inteira disposição para ajustes ou esclarecimentos adicionais.\n\n"
            "Atenciosamente,\n\n"
            "**{{vendedor_nome}}**  \n"
            "{{empresa}}  \n"
            "E-mail: {{vendedor_email}} | Tel: {{vendedor_telefone}}\n"
        ),
    },
    {
        "titulo": "Proposta de Fornecimento de Produtos",
        "conteudo": (
            "# Proposta Comercial para Fornecimento de Produtos\n\n"
            "**Cliente:** {{cliente}} | **CNPJ/CPF:** {{cliente_cnpj}}\n"
            "**Contato:** {{cliente_contato}} ({{cliente_email}})\n"
            "**Fornecedor:** {{empresa}} (CNPJ: {{empresa_cnpj}})\n"
            "**Referência:** {{proposta_titulo}} - Proposta Nº {{proposta_numero}}\n"
            "**Data:** {{data_emissao}}\n\n"
            "---\n\n"
            "## 1. Apresentação Comercial\n"
            "Apresentamos nossa cotação para o fornecimento dos produtos e materiais listados abaixo, desenvolvidos segundo elevados padrões de qualidade, procedência garantida e total conformidade com as normas aplicáveis.\n\n"
            "## 2. Relação de Produtos e Especificações\n\n"
            "{{itens}}\n\n"
            "### Condições de Fornecimento:\n"
            "- **Local de Entrega:** {{cliente_endereco}}\n"
            "- **Frete e Embalagem:** Transporte seguro com embalagens adequadas à preservação dos itens.\n"
            "- **Garantia:** Cobertura integral contra defeitos de fabricação com assistência direta da **{{empresa}}**.\n\n"
            "## 3. Resumo Financeiro e Faturamento\n"
            "- **Valor Global da Proposta:** R$ {{valor_total}}\n"
            "- **Forma / Condições de Pagamento:** {{condicoes_pagamento}}\n"
            "- **Faturamento:** Faturamento mediante emissão de Nota Fiscal Eletrônica (NF-e).\n\n"
            "## 4. Validade e Disponibilidade\n"
            "Esta cotação é válida até **{{data_validade}}** ({{validade_dias}} dias corridos), mediante disponibilidade dos itens em estoque no momento da confirmação do pedido.\n\n"
            "---\n\n"
            "Aguardamos a sua confirmação para prosseguirmos com a reserva e faturamento dos itens.\n\n"
            "**{{vendedor_nome}}**  \n"
            "Depto. Comercial — {{empresa}}  \n"
            "Contato: {{vendedor_telefone}} | {{vendedor_email}}\n"
        ),
    },
    {
        "titulo": "Proposta Comercial e Parceria de Negócios",
        "conteudo": (
            "# Proposta Comercial e Parceria Estratégica\n\n"
            "**Preparado para:** {{cliente}}\n"
            "**A/C:** {{cliente_contato}} ({{cliente_email}})\n"
            "**Elaborado por:** {{empresa}} ({{empresa_responsavel}})\n"
            "**Proposta:** {{proposta_titulo}} | **Nº:** {{proposta_numero}}\n"
            "**Emissão:** {{data_emissao}} | **Validade:** até {{data_validade}}\n\n"
            "---\n\n"
            "## 1. Visão Geral e Alinhamento Estratégico\n"
            "Esta proposta tem por finalidade consolidar uma parceria estratégica entre a **{{empresa}}** e a **{{cliente}}**, aliando solidez técnica, inovação contínua e atendimento personalizado para agregar valor competitivo e eficiência às suas operações.\n\n"
            "## 2. Soluções Propostas e Entregáveis\n"
            "Estruturamos as seguintes frentes de atuação para atender com precisão às demandas diagnosticadas:\n\n"
            "{{itens}}\n\n"
            "### Benefícios da Parceria:\n"
            "- **Atendimento Consultivo:** Suporte próximo e canal direto de comunicação comercial e técnica.\n"
            "- **Flexibilidade e Escalabilidade:** Soluções modulares desenhadas para acompanhar a evolução do seu negócio.\n"
            "- **Foco no Retorno (ROI):** Metas claras e transparência total nas etapas e custos.\n\n"
            "## 3. Condições Comerciais e Investimento\n"
            "- **Investimento Global:** R$ {{valor_total}}\n"
            "- **Condições de Pagamento:** {{condicoes_pagamento}}\n\n"
            "## 4. Formalização e Próximos Passos\n"
            "Para confirmar a aprovação desta proposta e dar início ao cronograma, basta manifestar seu aceite através do link eletrônico enviado ou assinar este termo.\n\n"
            "- **Prazo de Validade:** Válida por **{{validade_dias}} dias** (até {{data_validade}}).\n\n"
            "---\n\n"
            "Agradecemos a oportunidade de apresentar esta proposta e estamos prontos para iniciar esta jornada de sucesso em conjunto!\n\n"
            "Atenciosamente,\n\n"
            "**{{vendedor_nome}}**  \n"
            "{{empresa}}  \n"
            "E-mail: {{empresa_email}} | Tel: {{empresa_telefone}}\n"
        ),
    },
]


async def seed_modelos_padrao(
    db: AsyncSession, empresa_id: uuid.UUID, commit: bool = True
) -> list[ModeloProposta]:
    """Cria os 3 modelos padrão para uma empresa caso ela ainda não possua nenhum modelo cadastrado."""
    existing = await db.execute(
        select(ModeloProposta).where(ModeloProposta.empresa_id == empresa_id).order_by(ModeloProposta.titulo)
    )
    modelos = list(existing.scalars().all())
    if modelos:
        return modelos

    novos = []
    for item in MODELOS_PADRAO:
        modelo = ModeloProposta(
            id=uuid.uuid4(),
            empresa_id=empresa_id,
            titulo=item["titulo"],
            conteudo=item["conteudo"],
        )
        db.add(modelo)
        novos.append(modelo)

    if commit:
        await db.commit()
        for m in novos:
            await db.refresh(m)

    novos.sort(key=lambda m: m.titulo)
    return novos
