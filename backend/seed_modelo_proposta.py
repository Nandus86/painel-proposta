import asyncio
import uuid
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def seed_modelo():
    async with AsyncSessionLocal() as session:
        # Encontrar o usuario e sua empresa
        result = await session.execute(text("SELECT id, empresa_id FROM usuarios WHERE email = 'fernandomskt86@gmail.com'"))
        user = result.fetchone()
        
        if not user:
            print("Usuário fernandomskt86@gmail.com não encontrado!")
            return
            
        user_id, empresa_id = user
        
        # Conteudo Markdown do Modelo
        markdown_content = """# Proposta Comercial: {{proposta_titulo}}

Prezado(a) **{{cliente_contato}}**, representante da empresa **{{cliente}}**,

É com grande satisfação que apresentamos esta proposta comercial elaborada pela **{{empresa}}**. Nosso objetivo é oferecer a melhor solução em serviços e produtos para atender às necessidades do seu negócio.

## 1. Escopo da Proposta

A presente proposta tem como finalidade a prestação de serviços conforme os itens descritos abaixo:

{{itens_tabela}}

## 2. Investimento

O valor total do investimento para a execução dos serviços acima listados é de **{{valor_total}}** ({{valor_total_extenso}}).

**Condições de Pagamento:** {{condicoes_pagamento}}

## 3. Prazos e Validade

- **Data de Emissão:** {{data_emissao}}
- **Validade desta proposta:** {{validade_dias}} dias (Válida até {{data_validade}})

## 4. Contato

Caso tenha alguma dúvida ou deseje negociar as condições apresentadas, sinta-se à vontade para entrar em contato diretamente com o responsável técnico desta proposta.

Atenciosamente,

**{{vendedor_nome}}**
{{vendedor_telefone}} | {{vendedor_email}}
**{{empresa}}**
{{empresa_cnpj}} | {{empresa_endereco}}
"""

        # Inserir o modelo
        modelo_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO modelos_proposta (id, empresa_id, nome, conteudo, criado_por_id, ativo)
                VALUES (:id, :empresa_id, 'Modelo Comercial Padrão', :conteudo, :criado_por_id, true)
            """),
            {
                "id": modelo_id,
                "empresa_id": empresa_id,
                "conteudo": markdown_content,
                "criado_por_id": user_id
            }
        )
        
        await session.commit()
        print("Modelo de proposta criado com sucesso para a empresa do usuário!")

if __name__ == "__main__":
    asyncio.run(seed_modelo())
