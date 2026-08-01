# Plano: Reformular o Assistente de Configuração + tornar o sistema funcional

## Objetivo

1. Reformular o assistente de configuração (`SetupView.vue`): remover os passos **Telegram** e **Pagamento**, tornar **Plano** e **WhatsApp** realmente funcionais, adicionar passo de **E-mail (SMTP)**, e eliminar toda a UI falsa do wizard.
2. Corrigir os bloqueadores que impedem o sistema de funcionar em produção.
3. Limpeza ampla: remover/ligar UI morta, padronizar marca e idioma, fechar brechas de multi-tenancy e segurança.

## Decisões tomadas (não reabrir)

| Tema | Decisão |
|---|---|
| Telegram e Pagamento | Removidos **apenas do wizard**. Colunas `telegram_conectado`, `stripe_*`, `pagamento_modo_teste` permanecem no banco e em `EmpresaView.vue`. `status_pagamento` continua sendo usado pelo superadmin. |
| Passo Plano | Fica e passa a funcionar: nova tabela `planos`, seleção real, limites aplicados. Plano pago = solicitação de upgrade com `status_pagamento='pendente'` para o superadmin aprovar. |
| Passo WhatsApp | Fica e passa a funcionar via **Uazapi**. Servidor Uazapi é do operador (superadmin), com **uma instância por empresa** criada automaticamente. QR code exibido dentro do wizard. |
| Envio WhatsApp | Apenas `POST /send/text` com mensagem + link público. Sem anexo de PDF. |
| Marca | Vem de variável de ambiente. Padrão: **Dekto** / **dekto.com**. |
| Escopo | Wizard + bloqueadores críticos + limpeza ampla, em fases. |

## Contexto essencial

- Stack: FastAPI + SQLAlchemy async + Alembic + Postgres; Vue 3 + PrimeVue 4 + Pinia + Vite; nginx serve o SPA e faz proxy de `/api/`.
- Multi-tenancy é resolvido **exclusivamente pelo `empresa_id` do JWT** (`app/core/dependencies.py:42-46`). `DomainResolutionMiddleware` é código morto.
- Head atual do Alembic: `f2cfd74b241a`. Toda migration nova encadeia a partir dela.
- Não existe suíte de testes em nenhum lado. Os `backend/test_*.py` são scripts ad-hoc, alguns com credenciais reais e execução no import.
- Uazapi: base `https://{subdominio}.uazapi.com`; header `token` (instância) e `admintoken` (admin); endpoints `POST /instance/init`, `POST /instance/connect`, `GET /instance/status`, `POST /instance/disconnect`, `POST /send/text`. Estados: `disconnected` | `connecting` | `connected`. **Confirmar os nomes exatos dos campos de resposta na spec OpenAPI de https://docs.uazapi.com antes de codar o parser; ler defensivamente (`qrcode`/`qrCode`/`base64`, `instance.status`/`status`, `owner`).**

---

## Fase 0 — Bloqueadores (fazer primeiro, nada funciona bem sem isso)

1. **Colunas de e-mail ausentes em todas as migrations.** `empresas.email_assunto_padrao` e `empresas.email_corpo_padrao` existem em `app/models/empresa.py:68-69`, `app/schemas/empresa.py:38-39,79-80`, são lidas em `app/services/email.py:101-102` e escritas por `ConfiguracoesView.vue:521-522`, mas **não existem em nenhuma migration**. Um banco criado só com `alembic upgrade head` quebra em toda query `SELECT empresas.*` (login incluído). Criar migration nova: `add_column('empresas', Column('email_assunto_padrao', String(255), nullable=True))` e `('email_corpo_padrao', Text, nullable=True)`.
2. **`NameError` no reset de senha.** `app/routers/superadmin.py:246` usa `uuid.uuid4()` mas o import em `:6` é `from uuid import UUID`. A ação `resetar_senha_admin` (chamada por `SuperAdminEmpresasView.vue:333`) sempre retorna 500. Adicionar `import uuid`.
3. **`GET /api/empresas/me` devolve menos campos que `PUT`.** `app/routers/empresas.py:97-119` monta o `EmpresaResponse` à mão e omite `cor_marca`, `subdominio`, `dominio_personalizado`, `pais`, `moeda`, `idioma`, `setor`, `plano`, `status_pagamento`, `email_*` — por isso o wizard e `EmpresaView` não conseguem pré-carregar nada. Trocar por `EmpresaResponse.model_validate(empresa)` em `:97-119` e `:59-81`.
4. **Refresh de token quebrado em produção.** `Dockerfile` do frontend define `VITE_API_URL=/`, então `api.js:37` gera `//api/auth/refresh` (URL protocol-relative → `https://api/auth/refresh`). Corrigir: normalizar a baseURL (`const baseURL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')`) e usar caminho relativo no refresh.
5. **Logos quebradas em produção (mesmo bug).** As 5 cópias de `backendUrl()` (`EmpresaView.vue:260`, `PropostaEditorView.vue:586`, `PublicPropostaView.vue:144`, `PublicOrcamentoView.vue:142`, `admin/SuperAdminEmpresasView.vue:256`) geram `//uploads/...`. Extrair um único `src/utils/assetUrl.js` e usar nos 5 lugares.
6. **nginx bloqueia o upload de logo e não serve `/uploads/`.** `frontend/nginx.conf`: adicionar `client_max_body_size 5m` (hoje o default de 1 MB rejeita silenciosamente o "máximo 2 MB" prometido em `SetupView.vue:98`), adicionar `location /uploads/ { proxy_pass ... }` (sem isso o `try_files` devolve `index.html` para imagens), subir `proxy_read_timeout` para as chamadas de IA, e remover o `Connection 'upgrade'` incondicional em `:23`.
7. **Path traversal em `/uploads/{path:path}`.** `app/main.py:74-89` faz `os.path.join("uploads", path)` sem normalizar (e `storage.py:123` só faz `lstrip("/")`). Resolver com `os.path.realpath` e afirmar que o resultado está dentro da raiz `uploads/`.
8. **Bloqueio de empresa é cosmético.** `app/routers/auth.py:86-90` checa `user.ativo` mas nunca `empresa.ativo` nem `status_pagamento`. Criar dependência `require_empresa_ativa` em `app/core/dependencies.py` e aplicar no `login` e no `get_current_user`; também checar `empresa.ativo` em `app/routers/public.py:18-30` e `:114-126`.
9. **Tempestade de N+1 em toda request autenticada.** `app/models/empresa.py:83-88` declara 6 relacionamentos `lazy="selectin"`; como `get_current_user` faz `selectinload(Usuario.empresa)`, cada request carrega todos os usuários, clientes, categorias, serviços, propostas e logs da empresa. Trocar para `lazy="select"` (ou `raise`) e carregar explicitamente onde necessário. Idem `app/models/log_admin.py:28-29`.
10. **Remover o `print` do corpo da request no handler 422** (`app/main.py:36-37`) — vaza senhas de `/api/auth/login` no log.

**Validação da fase:** derrubar o volume do Postgres, `docker compose up --build`, confirmar `alembic upgrade head` limpo, registrar um usuário novo, fazer login, abrir `/empresa` e ver os campos preenchidos, subir um logo de ~1,5 MB e vê-lo renderizado, deixar o access token expirar e confirmar que o refresh funciona.

---

## Fase 1 — Marca e domínio por variável de ambiente

1. Backend `app/config.py`: `APP_NAME` default `"Dekto"`, `BASE_DOMAIN` default `"dekto.com"`; adicionar `FRONTEND_URL`, `ENVIRONMENT`, `LOG_LEVEL`. Fazer o app **falhar no boot** se `SECRET_KEY` continuar no valor default (`config.py:11`) e `ENVIRONMENT != "development"` — hoje essa chave também deriva a chave Fernet (`core/security.py:52`), então trocá-la destrói silenciosamente todas as senhas SMTP e o token do OpenRouter.
2. Frontend: criar `src/config/branding.js` exportando `APP_NAME = import.meta.env.VITE_APP_NAME || 'Dekto'` e `ROOT_DOMAIN = import.meta.env.VITE_ROOT_DOMAIN || 'dekto.com'`. Criar `frontend/.env.example`.
3. Substituir todos os hardcodes: "Dekto" em `AppSidebar.vue:11`, `SuperAdminSidebar.vue:11`, `LoginView.vue:17,81`, `RegisterView.vue:7,11,77`, `SetupView.vue:6`; `.dekto.com` em `SetupView.vue:210,213`; `.painelproposta.com` em `EmpresaView.vue:161,163,172` e `SuperAdminEmpresasView.vue:39`; título em `index.html:8`; "Enviado via Painel Proposta" em `app/services/email.py:116`.
4. `docker-compose.yml`: adicionar `VITE_APP_NAME` e `VITE_ROOT_DOMAIN` ao serviço `frontend`, `BASE_DOMAIN` ao `backend`. Corrigir `VITE_API_URL=/` → vazio. `nginx.conf:3`: `server_name localhost *.dekto.com;`.
5. Alinhar `frontend/package.json:4` (`0.0.0`) com o `v1.0.0` mostrado em `AppSidebar.vue:41`, ou ler a versão do `package.json`.

---

## Fase 2 — Planos reais com limites aplicados

1. **Modelo + migration.** Nova tabela `planos`: `slug` (PK/unique), `nome`, `descricao`, `preco_mensal` (Numeric), `preco_anual`, `moeda`, `max_usuarios` (null = ilimitado), `max_propostas_mes` (null = ilimitado), `ai_credits_limit`, `permite_dominio_proprio` (bool), `ordem`, `ativo`, `destaque` (bool, para o badge "MAIS POPULAR"). Seed dos 4 planos hoje hardcoded em `SetupView.vue:158-193` — **converter os preços de € para a moeda que você vai cobrar**, já que o resto do sistema formata tudo em BRL.
2. `empresas`: adicionar `plano_solicitado` (String, nullable) e `setup_concluido` (Boolean, default false — ver Fase 4). `empresa.plano` continua String mas passa a referenciar `planos.slug`.
3. **Router `app/routers/planos.py`**: `GET /api/planos` (autenticado, lista ativos, ordenado); `POST/PUT/DELETE /api/admin/planos` (`require_superuser`).
4. **Solicitação de upgrade**: `POST /api/empresas/me/plano` com `{slug}`. Se o plano for gratuito → aplica em `empresa.plano` na hora. Se pago → grava `plano_solicitado`, seta `status_pagamento='pendente'` e cria `LogAdmin`. Nunca aplicar plano pago sozinho.
5. **Aprovação**: em `SuperAdminEmpresasView.vue`, mostrar `plano_solicitado` e um botão Aprovar/Recusar que chama a ação do superadmin (aplica `plano = plano_solicitado`, limpa `plano_solicitado`, seta `status_pagamento='em_dia'`, grava log). Hoje há **duas** APIs mutando o mesmo estado (`PUT /api/empresas/admin/{id}/status` em `:365` e `POST /api/superadmin/empresas/{id}/acao` em `:311/:321/:333`) e só uma grava log — unificar em `superadmin.py`.
6. **Aplicação dos limites** (hoje inexistente; `plano` só é lido em `empresas.py:221`):
   - Dependência `verificar_cota_propostas`: conta `Proposta` do mês corrente por `empresa_id` e devolve 402/429 acima de `max_propostas_mes`. Aplicar em `propostas.py:106` e `orcamentos.py:106`.
   - Dependência `verificar_cota_usuarios` em `usuarios.py:62`.
   - `ai.py:86` passa a ler `ai_credits_limit` do plano em vez do campo fixo em `empresa` (`empresa.py:60`, default 20).
   - `empresas.py:221` (domínio próprio) passa a ler `plano.permite_dominio_proprio` em vez do literal `("pro","premium")`.
   - `dashboard.py`: expor `propostas_mes` e a cota, para a UI mostrar "12 de 20 propostas este mês".
7. **UI**: aba "Planos" com CRUD em `SuperAdminConfigView.vue`; card de uso/cota no `DashboardView.vue`.

---

## Fase 3 — WhatsApp via Uazapi

1. **Config do operador** em `sistema_config` (`app/models/sistema_config.py`): `uazapi_base_url` (String), `uazapi_admin_token` (Text, criptografado com `encrypt_data`). Expor em `admin_config.py` com o mesmo padrão `has_*` já usado para o OpenRouter, e nova aba "WhatsApp" em `SuperAdminConfigView.vue` com botão **Testar conexão**. Ao mesmo tempo, corrigir `admin_config.py:22,41`: `select(SistemaConfig)` sem `.where(id==1)` estoura `MultipleResultsFound` se surgir uma segunda linha — usar `db.get(SistemaConfig, 1)`, como `ai.py:90` já faz.
2. **Campos por empresa** (migration): `uazapi_instance_id`, `uazapi_instance_token` (criptografado), `whatsapp_numero`, `whatsapp_status` (`disconnected`/`connecting`/`connected`). Manter `whatsapp_conectado` sincronizado com `whatsapp_status == 'connected'` para não quebrar `EmpresaView.vue:185`.
3. **`app/services/whatsapp.py`** com `httpx.AsyncClient` (timeout explícito, sem `print`):
   - `ensure_instance(empresa)` → `POST {base}/instance/init` com header `admintoken`, nome da instância derivado de `empresa.id`; guarda o token retornado criptografado. Idempotente.
   - `connect(empresa)` → `POST {base}/instance/connect` com header `token`; devolve `{qrcode_base64, paircode, status}`.
   - `get_status(empresa)` → `GET {base}/instance/status`; atualiza `whatsapp_status` e `whatsapp_numero` (campo `owner`).
   - `disconnect(empresa)` → `POST {base}/instance/disconnect`.
   - `send_text(empresa, numero, texto)` → `POST {base}/send/text` com `{number, text, linkPreview: true}`. Normalizar o número para E.164 sem `+` (Uazapi espera `5511999999999`); rejeitar número inválido com 400.
   - Tratar 429 (limite de instâncias do servidor) com mensagem clara, e 401/403 como "credenciais Uazapi inválidas".
4. **`app/routers/whatsapp.py`** (`require_admin`): `POST /api/whatsapp/conectar` (init + connect, devolve QR), `GET /api/whatsapp/status`, `POST /api/whatsapp/desconectar`. Retornar 400 explícito se o operador não configurou `uazapi_base_url`/`admintoken`.
5. **Envio**: `POST /api/propostas/{id}/enviar-whatsapp` e o equivalente em orçamentos. Reaproveitar `build_email_variables` de `app/services/email.py:47` para montar a mensagem (extrair para `app/services/variaveis.py` para não importar `email` no fluxo de WhatsApp) e adicionar a variável `{{link_proposta}}`. Novos campos em `empresas`: `whatsapp_mensagem_padrao`. Ao enviar com sucesso, mudar `status` para `enviada` e gravar timestamp de envio — o envio por e-mail hoje **não faz isso** (`propostas.py:346`), corrigir junto.
6. **Link público correto.** `propostas.py:374` monta o link a partir de `request.headers.get("origin", "https://seu-dominio.com")` — header controlável pelo cliente e com placeholder de fallback. Criar helper `build_public_url(empresa, token, tipo)` que usa `dominio_personalizado` → `subdominio.BASE_DOMAIN` → `FRONTEND_URL`, e usar no e-mail e no WhatsApp.
7. **Frontend**: componente `WhatsAppConnect.vue` (exibe QR em `<img :src="'data:image/png;base64,'+qr">`, faz polling de `/api/whatsapp/status` a cada 3 s com limite de tentativas e `onBeforeUnmount(clearInterval)`, mostra número conectado e botão Desconectar). Usar no passo 4 do wizard **e** em `IntegracoesView.vue`. Botão "Enviar por WhatsApp" em `PropostasView.vue` e `OrcamentosView.vue` (com confirmação e feedback de erro real).

---

## Fase 4 — Reformulação do assistente de configuração

**Passos finais:** 1 Marca e empresa · 2 Plano · 3 Domínio · 4 WhatsApp · 5 E-mail (SMTP) · 6 Revisão e conclusão.

1. **Remover os passos Telegram e Pagamento** de `SetupView.vue`: bloco `:254-276` (Telegram), bloco `:278-314` (Pagamento), entradas `{id:5}` e `{id:6}` em `:348-355`, campos `telegram_conectado`, `stripe_publishable_key`, `stripe_secret_key`, `pagamento_modo_teste` do `form` (`:369-372`) e do payload de `finishSetup` (`:417-420`), e os CSS órfãos `.telegram-box`/`.tg-*` (`:1099-1152`) e `.payment-*`/`.test-mode-toggle`/`.security-info`/`.save-continue-btn` (`:1166-1267`). Os campos permanecem no banco e em `EmpresaView.vue:177-211`.
2. **Fim do salvamento monolítico.** Hoje o wizard só grava no fim, e a saída pelo header (`:8`) e pelo "Saltar e concluir" (`:312`) chamam `finishSetup()`, que faz `PUT /api/empresas/me` com o form **vazio** → apaga `razao_social`/`nome_fantasia` e escreve `telefone: 'N/A'` (`:405-407`). Isso é perda de dados e piora porque `AppSidebar.vue:72` mantém um link permanente para `/setup`. Corrigir:
   - Cada passo salva o seu próprio recorte ao avançar (`PUT /api/empresas/me` só com os campos do passo; domínio via `PUT /api/empresas/me/dominio`; plano via `POST /api/empresas/me/plano`).
   - "Ir para o painel" faz apenas `router.push('/')`, sem gravar nada.
   - `onMounted` carrega `GET /api/empresas/me` e pré-preenche o form, de modo que reentrar no wizard nunca zera dados.
3. **Marcador de setup explícito.** Substituir a heurística `empresa.telefone` de `app/main.py:104-122` pela coluna `setup_concluido`. Novo `POST /api/setup/concluir` chamado no passo 6. Ajustar `auth.js:17-26` e o guard em `router/index.js:156`. Resetar `setupDone` no `logout()` (`auth.js:75-80`) — hoje o veredito do usuário anterior persiste após trocar de conta.
4. **Passo 1 — Marca e empresa (torná-lo real):**
   - Upload de logo de verdade: hoje `:89-101` é um `div` decorativo, sem `input[type=file]`. Reusar a lógica de `EmpresaView.vue:265-288` (`POST /api/empresas/logo`), com preview e validação de tipo/tamanho (2 MB).
   - Validação por passo: nome da empresa obrigatório e `maxlength=60` (o contador em `:42` não impõe nada); telefone com máscara; remover o auto-invento de nome (`Empresa de X`) e subdomínio aleatório em `:377-381` — pré-preencher com o nome que o usuário digitou no cadastro.
   - `RegisterView.vue:36,149` coleta `form.empresa` e **não envia** (`auth.js:43` só manda nome/email/senha). Adicionar `empresa` ao `RegisterRequest` e usar em `auth.py:39-42` no lugar de `f"Empresa de {nome}"`.
   - Listas reais: fuso horário tem **uma** opção truncada (`:64-66`), setor tem duas (`:122-125`). Popular com listas completas (fusos do Brasil + principais, ~15 setores).
   - Preview: "Ver proposta" (`:138`) não tem handler — remover ou apontar para uma proposta de exemplo. As iniciais do logo estão hardcoded como `AB` (`:132`) — derivar do nome.
5. **Passo 2 — Plano:** cards vindos de `GET /api/planos` com `@click` real (hoje não têm handler e "Grátis" é `active` fixo em `:159`), toggle Mensal/Anual funcional (`:149-156` não tem handler), preço formatado na moeda do plano, e submissão via `POST /api/empresas/me/plano`. Plano pago mostra aviso "sujeito a aprovação". Remover o botão "Comparar todos os planos" (`:196`) ou implementar a tabela comparativa. Ajustar o texto "Não é necessário pagamento durante a configuração" (`:147`), que agora é a regra e não uma ressalva.
6. **Passo 3 — Domínio:** sufixo do `ROOT_DOMAIN` (não `.dekto.com` hardcoded), `PUT /api/empresas/me/dominio` para validar formato/unicidade no servidor, e o botão "Verificar" (`:223`) chamando `POST /api/empresas/me/dominio/verificar` — hoje ele executa `alert(...)` dentro do template, que **lança `TypeError`** porque `alert` não é global permitido no template do Vue 3. Exibir os registros DNS retornados. Remover o "Subdomínio ativo" verde hardcoded (`:215`) e trocar por status real. Bloquear domínio próprio se o plano não permitir, com upsell.
7. **Passo 4 — WhatsApp:** substituir o toggle falso (`:248-250`, que só inverte um booleano local) pelo `WhatsAppConnect.vue` da Fase 3, com QR real. Se o operador não configurou o Uazapi, mostrar o passo como indisponível em vez de prometer conexão.
8. **Passo 5 — E-mail (SMTP), novo:** host/porta/usuário/senha + botão **Testar envio**. Exige novo `POST /api/empresas/me/smtp/testar` (não existe hoje) que dispara um e-mail de teste para o usuário logado. É o único canal de envio realmente implementado, e hoje está escondido em `ConfiguracoesView.vue:78-104`.
9. **Passo 6 — Revisão:** resumo do que foi configurado, com pendências destacadas ("SMTP não configurado — você não conseguirá enviar propostas por e-mail") e `POST /api/setup/concluir`.
10. **Estados e acessibilidade:** `loading` e `error` existem (`:344-345`) e **nunca são renderizados** — um save que falha não mostra nada; renderizar spinner no botão e banner de erro. Trocar `div @click` por `<button>` nos swatches de cor (`:106-111`) e no upload (`:92`); `label for`/`id` em todos os campos (`:40,46,56,63,71,81,90,104,121`); `role="switch"`/`aria-checked` nos toggles.
11. **Responsividade:** o stepper tem largura fixa de ~680 px (`.step-wrapper{width:80px}` `:498` + `.step-line{width:40px}` `:537`) sem `flex-wrap` e **sem nenhuma media query no arquivo** → estoura abaixo de ~700 px. Adicionar `flex-wrap`, e abaixo de 640 px usar só o contador `{{step}}/{{steps.length}}` que já existe em `:323`. Idem `.plans-grid` (`:825`) e os paddings de 3 rem do header/footer (`:452,:1274`).
12. **Idioma pt-BR:** "Logótipo"→"Logotipo" (`:36,90`), "faturação"→"faturamento" (`:147,150`), "Saltar por agora"→"Pular por agora" (`:275`), "Guardar e continuar"→"Salvar e continuar" (`:311`), placeholder `+351 9** *** ***`→`+55 (11) 99999-9999` (`:47`). Mesma passada em `RegisterView.vue:11,77` ("levámos", "gerámos", "a equipa", "utilização").
13. **Sidebar:** o link permanente "Assistente de Configuração" (`AppSidebar.vue:72`) só é seguro depois do item 2; manter, mas renomear para "Reabrir assistente" e exibir apenas para admin.

**Validação da fase:** registrar empresa nova, percorrer os 6 passos preenchendo tudo, confirmar no banco que cada passo gravou; repetir abandonando no passo 3 e confirmar que nada foi apagado; reentrar e confirmar pré-preenchimento; testar em viewport de 375 px; testar navegação por teclado nos toggles e swatches.

---

## Fase 5 — Limpeza ampla

### 5a. UI morta: ligar ou remover

- `DashboardView.vue`: select de moeda sem `v-model` (`:6-10`), date-picker mock (`:11-13`), abas "Todos"/"Somente os meus" (`:78-79`), "Limpar" (`:81`), "Ocultar" (`:82`) — todos sem handler. Cards "Pagamentos pendentes" (`:41`) e "Solicitações de retorno" (`:50`) são `0` hardcoded. "Atividade recente" (`:85-88`) é vazio fixo. Decisão por item: ligar ao `dashboard.py` ou remover. Adicionar `loading`/erro/retry (hoje a falha só faz `console.error` em `:110`, e a tela fica igual a uma conta vazia).
- `AppTopbar.vue`: o painel de notificações é 100% falso — `notifications.js:10 add()` nunca é chamado e `checkExpiringPropostas()` (`:49-53`) descarta o resultado num `catch` vazio e nunca é invocado. Ou implementar (propostas a vencer, proposta visualizada, proposta aceita) ou remover o sino. Remover também o menu de usuário morto (`:70,97-118`) e completar o `pageTitle` (`:87-95` cobre 4 de 15 rotas).
- `AppSidebar.vue:60-79`: **`/usuarios` não está na navegação** — a tela de usuários é inalcançável. Adicionar. Corrigir `isActive` (`:81-84`) para `startsWith`, senão `/propostas/nova` deixa o menu sem item ativo.
- `SuperAdminSidebar.vue:296-298`: `.collapsed .toggle-btn{display:none}` → depois de colapsar **não há como expandir**. Corrigir. `isActive` com `startsWith('/admin')` (`:77-79`) marca Dashboard em todas as páginas.
- `SuperAdminEmpresasView.vue`: `Dropdown` sem `optionLabel`/`optionValue` renderiza `[object Object]` (`:10-11`); `onSearch()`/`onFilter()` são funções vazias (`:377-378`) → os dois filtros são UI morta; o modal de detalhes abre antes do fetch e mostra os dados da empresa anterior (`:299-303`); bloquear/desbloquear são destrutivos sem confirmação (`:66-85`); o reset de senha mostra a senha em texto puro num toast (`:333-338`) — e o backend ainda **persiste essa senha em texto puro** em `log_admin` (`superadmin.py:248`): parar de persistir e trocar por fluxo de e-mail/reset obrigatório.
- `PropostasView.vue:207-209` / `OrcamentosView.vue:202-204`: `sendProposta`/`sendOrcamento` mostram toast de sucesso **sem chamar API** e são código morto — remover.
- Endpoints existentes sem UI: `DELETE /api/propostas/{id}` e `/api/orcamentos/{id}` (não há como excluir nada pela interface), `GET .../{id}/pdf` (não há botão de PDF em lugar nenhum; `html2canvas` está no `package.json` sem nenhum import), `POST /api/clientes/import/csv` (`clientes.py:215`, sem UI). Adicionar as ações.
- `SetupView`/`EmpresaView`/`ConfiguracoesView`/`SuperAdminDashboardView`: falha de carregamento deixa spinner infinito (`EmpresaView.vue:227`, `ConfiguracoesView.vue:205`, `SuperAdminDashboardView.vue:100`) — adicionar erro + retry. `SuperAdminDashboardView.vue:161-201` cria 2 `Chart` sem destruir no unmount.
- `router/index.js`: sem rota catch-all → URL inválida renderiza tela branca. Adicionar 404.
- Componentes/deps mortos: `LiquidGlassCard.vue` + `LiquidGlassDialog.vue` (só se importam entre si; `console.log` em `:62`), dep `liquid-gl`, dep `html2canvas`, `@primevue/themes` duplicado com `@primeuix/themes`. Remover.
- `VariablePalette.vue:82-89,96-103`: variáveis customizadas renderizadas duas vezes. `ConfiguracoesView.vue:456` e `ModelosView.vue:225`: `TAG_RE` global reutilizada com `.test()` → `lastIndex` persiste e o drop falha a cada duas tentativas. `ConfiguracoesView.vue:215`: falta `v-pre`. `ConfiguracoesView.vue:129-149`: o editor de corpo de e-mail está num `TabPanel` lazy, então `editorRef` é `null` no `onMounted` e digitar um caractere **sobrescreve o corpo salvo** com vazio.
- `RegisterView.vue`: links de Termos/Privacidade `href="#"` (`:71`), `toggleTheme()` vazio (`:131-133`), selector de idioma estático (`:23-25`), botão "Cadastrar-se com Google" sem handler e sem OAuth no backend (`:95-99`). Remover o que não existe. Unificar a política de senha (`:63` promete 8+1 maiúscula+1 número, valida só tamanho; `UsuariosView.vue:126` diz 6 e não valida).
- `LoginView.vue`: não há "Esqueci minha senha" e não existe fluxo de reset no backend (só o script `reset_password.py`). Implementar ou remover a expectativa.

### 5b. Duplicação

- `PropostaEditorView.vue` e `OrcamentoEditorView.vue` são ~250 linhas idênticas (`addItem`, `removeItem`, `onServicoChange`, `calculateTotals`, watch, `getStatusSeverity`, `formatCurrency`, `copyPublicLink`, tabela de itens, resumo financeiro). `stores/propostas.js` e `stores/orcamentos.js` são gêmeos, com um bloco `aiCredits` morto em `orcamentos.js:10-14`. Extrair `components/DocumentEditor.vue` + `useDocumentStore(kind)`.
- `app/routers/propostas.py` e `orcamentos.py` são ~95% duplicados (391 linhas cada). Extrair a lógica comum para um serviço.
- `EmpresaResponse`/`UsuarioResponse`/`ClienteResponse` são montados à mão 3-4 vezes cada (`usuarios.py:14-59,107-136,139-183`, `clientes.py:16-71,110-145,148-191`) — usar `model_validate`.
- **Sobreposição de telas:** `prefixo_proposta` e `validade_padrao_dias` são editáveis em `ConfiguracoesView.vue:31,35` **e** `EmpresaView.vue:106,110`, ambos escrevendo `PUT /api/empresas/me`; como `EmpresaView.vue:302` envia o objeto inteiro, salvar lá reverte o que foi salvo em Configurações. Manter só em Configurações. `IntegracoesView.vue` é um placeholder ("Página em branco") enquanto as integrações reais moram em `EmpresaView.vue:177-211` — mover SMTP/WhatsApp/Telegram/Stripe para Integrações e deixar Empresa só com dados cadastrais.

### 5c. Segurança e multi-tenancy

- **Vazamento entre empresas:** `cliente_id` e `servico_id` não são validados contra `empresa_id` em `propostas.py:106-149,177-179` e `orcamentos.py:112,177`. O endpoint de preview (`propostas.py:278-281`) já faz certo — replicar.
- **XSS:** `v-html="marked(...)"` sem sanitização em `PropostaEditorView.vue:213` e `PublicPropostaView.vue:59` (página voltada ao cliente). Adicionar DOMPurify. No backend, `app/services/pdf.py` não escapa **nenhum** valor do usuário (`:70,80,244,255,279-291,325`) — `html.escape()` em tudo antes do markdown.
- `stripe_secret_key` é `String(255)` em texto puro (`empresa.py:47`) e renderizada como input visível (`EmpresaView.vue:201-206`), diferente da senha SMTP que é criptografada. Criptografar e mascarar com flag `has_stripe_secret`.
- `POST /api/empresas/setup` (`empresas.py:23-30`) recebe `admin_email`, `admin_senha`, `admin_nome` como **query params** (senha vai para o log do nginx) e é inalcançável depois da primeira empresa. Remover o endpoint — `auth.py:23 register` já cobre o onboarding.
- `EmpresaUpdate` permite gravar `subdominio`/`dominio_personalizado` direto pelo `PUT /me` (`empresas.py:136-148`), driblando validação, unicidade e checagem de plano de `PUT /me/dominio`. Excluir esses campos do schema de update.
- Público: `public.py:80-101,175-194` aceita aceitar proposta **vencida** (nenhum lugar do sistema aplica `expirada`/`vencido`); `:88-89` permite aceitar proposta já recusada; `:29,:125` incrementa `visualizacoes` com read-modify-write em Python (perde contagem em concorrência) — usar `UPDATE ... SET visualizacoes = visualizacoes + 1`. Adicionar rate limiting. Não existe ação "Recusar" na página pública, então `status='recusada'` é inalcançável pelo cliente.
- `auth.py:108-141`: refresh token stateless sem rotação/blacklist — token antigo vale 7 dias após logout ou troca de senha. Adicionar `POST /api/auth/logout` e invalidação (jti em tabela ou `token_version` no usuário).

### 5d. Correção funcional de propostas/orçamentos/PDF/e-mail

- Numeração: `max(numero)+1` (`propostas.py:114-118`) é race condition e não há `UNIQUE(empresa_id, numero)`. Adicionar a constraint + retry. `prefixo_proposta` da empresa nunca é usado na numeração nem no PDF.
- Validade: hardcoded 15 dias em `propostas.py:127`, `:296`, `PropostaEditorView.vue:341`, `OrcamentoEditorView.vue:141,240`, ignorando `empresa.validade_padrao_dias` (default 30). Ler da empresa.
- `status` é definível pelo cliente na criação (`schemas/proposta.py:32,46`) — dá para criar proposta já `aceita`, driblando o fluxo público de aceite. Remover de Create e validar transições no Update.
- Busca por cliente não funciona: `or_()` com um argumento só e a cláusula comentada (`propostas.py:45-51`).
- `generate_proposal_pdf` é síncrono e chamado direto em endpoint async (`propostas.py:250,332`) — travar o event loop inteiro. Usar `run_in_threadpool` (o e-mail já faz certo em `:380`). Idem `storage.py:65,111-112,129-130`.
- PDF de orçamento sai rotulado como "PROPOSTA COMERCIAL" (`pdf.py:257,265,244`) — parametrizar `tipo_doc`. Cores hardcoded `#f39c12` ignoram `empresa.cor_marca`. Logo remota (MinIO) nunca é buscada porque falta `link_callback` no `pisa.CreatePDF` (`pdf.py:57-62`) → logo ausente no PDF em produção. `data_emissao.strftime` sem guarda quebra o preview (`pdf.py:66`).
- Página pública não aplica `cor_marca` (`.doc-top-border` em `PublicPropostaView.vue:222-225` tem altura e nenhum `background`) — a marca do cliente não aparece justamente onde o cliente final olha.
- E-mail: só STARTTLS, sem suporte a TLS implícito na porta 465 (`email.py:28-32`) → quem usa 465 não envia; `smtplib.SMTP` sem context manager vaza socket; `From` ignora `empresa.email` e não tem `Reply-To` do vendedor; o botão "Visualizar" é injetado por `str.replace` exato (`email.py:105`), então qualquer edição do texto pelo usuário deixa um link markdown cru — trocar por variável `{{link_proposta}}`.
- `propostas.py:371` checa só `smtp_host` mas `email.py:12` exige host+porta+usuário+senha → configuração parcial passa e depois estoura 500.
- Excluir orçamento vinculado a proposta gera `IntegrityError` 500 (`orcamentos.py:214-219`); idem excluir cliente com documentos (`clientes.py:194-212`) e categoria em uso (`categorias.py:97`, com TODO). Retornar 409 com mensagem.
- `Proposta.orcamento_id` existe mas **nenhum endpoint converte orçamento em proposta** — feature incompleta. Implementar ou remover o campo do escopo.
- `clientes.py:237-268`: `row_num` referenciado em `:268` só existe dentro do loop → CSV sem linhas de dados dá `UnboundLocalError` 500. Import CSV sem limite de linhas, dedup ou validação por linha.
- Desconto: existe por item, é importado em `PropostaEditorView.vue:524`, mas não tem input e é excluído de `calculateTotals` (`:448`), com a linha "Desconto" fixa em `R$ 0,00` (`:91`) — descontos são silenciosamente perdidos.
- `ai.py:82-87`: o reset diário de créditos é gravado e depois `raise HTTPException(429)` → `get_db` faz rollback e o reset é perdido. Incremento não atômico (`:184`) permite passar do limite. `engine.py:10-13` reescreve silenciosamente qualquer modelo fora da whitelist para `google/gemini-2.5-flash`, então escolher um modelo Mistral/DeepSeek na tela de superadmin **não tem efeito**. `ai.py:19-48` (`/openrouter/models`) está **sem autenticação** e faz chamada externa a cada hit. Erros do provider são devolvidos crus ao cliente (`ai.py:192`, `propostas.py:262,344,388`).

### 5e. Idioma e texto

- Gênero/acentuação de "Orçamento" está errado em toda a feature: `OrcamentoEditorView.vue:8,23,43,252`, `OrcamentosView.vue:5,35,90,91,203`, `PublicOrcamentoView.vue:27,39,98,105,111,152` — e `PublicOrcamentoView.vue:100` tem um botão "APROVAR PROPOSTA" numa página de orçamento. `PropostasView.vue:6` diz "acompanhe seus orçamentos" na tela de Propostas.
- `orcamentos.py:101,175,216,247`: "Orcamento não encontrada".
- Considerar `vue-i18n` com catálogo pt-BR único, já que hoje todas as strings são inline.

### 5f. Infra, dados e qualidade

- Índices: nenhuma migration cria índice em `empresa_id` (propostas, orçamentos, clientes, serviços, categorias, usuários) — toda listagem por tenant faz seq scan. Adicionar índices compostos `(empresa_id, created_at)`.
- `database.py:5-10`: sem `pool_pre_ping=True` nem `pool_recycle` → conexões mortas depois de restart do Postgres. `get_db` (`:27`) faz commit em **toda** request, inclusive GET, e os routers misturam `commit()` explícito com `flush()` — padronizar uma estratégia só.
- `bd6b4f3672f9:24`: `orcamentos.token_publico` adicionado `nullable=False` sem `server_default` → quebra em tabela com dados. Vários `create_unique_constraint(None, ...)` deixam os `downgrade()` inoperantes — nomear todas as constraints. `env.py:33-45` sem `compare_type`/`compare_server_default` (foi por isso que as colunas de e-mail passaram batido).
- Remover `DomainResolutionMiddleware` (`app/core/middleware.py`): `request.state.empresa_id` é escrito e **nunca lido**, custando uma query extra por request; e por estar registrado depois do CORS (`main.py:50-51`), uma exceção nele retorna 500 sem headers de CORS.
- Logging: o backend usa `print` em todo lugar (`ai.py:37,191`, `storage.py:57,104,144`, `dependencies.py:70,84` — este último loga e-mail do usuário a cada 403). Configurar `logging` com `LOG_LEVEL`.
- `/api/health` (`main.py:93`) não toca no banco → reporta saudável com Postgres caído.
- Scripts na raiz do backend: `test_key.py:17-19` **imprime a chave descriptografada do OpenRouter**; `check_smtp.py:11`, `reset_password.py:9,16`, `create_superadmin.py:11,14,34`, `test_server_auth.py:3,7` têm e-mails reais, senhas (`admin123`, `teste123`) e um hash bcrypt commitado. Apagar ou mover para `scripts/` com parâmetros de CLI, e **rotacionar essas credenciais**. Vários executam no import, então rodar `pytest` na pasta `backend/` hoje dispara código real contra banco/rede.
- `backend/Dockerfile:22`: `alembic upgrade head` no `CMD` faz cada réplica correr para migrar. Separar em job. Sem multi-stage, roda como root, sem `HEALTHCHECK`, sem `--proxy-headers` (necessário para o `X-Forwarded-For` de `public.py:94`), e `uploads/` sem `VOLUME` → logos locais somem a cada deploy.
- `frontend/Dockerfile:2`: `node:20-alpine` com Vite 8 (exige Node ≥20.19/22) → fixar `node:22-alpine`; trocar `npm install` por `npm ci`; adicionar `.dockerignore`.
- Ferramental ausente: nenhum lint/format/test nos dois lados. Adicionar `pytest` + `pytest-asyncio` + `httpx` e uma pasta `tests/` no backend; `eslint-plugin-vue` + `prettier` + `vitest` no frontend; scripts no `package.json`. Remover `langgraph` (não usado) e fixar as versões `>=` do `requirements.txt`.
- `nginx.conf`: headers de segurança (`X-Content-Type-Options`, `Referrer-Policy`, CSP), cache imutável para `/assets/`, `no-store` no `index.html`, `gzip_types` incluindo `application/json` e `image/svg+xml`.

---

## Ordem de execução recomendada

1. Fase 0 (bloqueadores) — sem ela nada mais é verificável.
2. Fase 1 (marca/env) — barata e desbloqueia o passo de domínio do wizard.
3. Fase 2 (planos) — o passo 2 do wizard depende da tabela `planos`.
4. Fase 3 (Uazapi) — o passo 4 do wizard depende do serviço de WhatsApp.
5. Fase 4 (wizard) — consome tudo acima.
6. Fase 5 (limpeza) — pode ser fatiada em PRs independentes por subseção (5a…5f).

## Riscos

- **Migrations.** A ausência das colunas de e-mail sugere que o banco atual foi alterado fora do Alembic. Antes da Fase 0, comparar o schema real com os modelos (`alembic revision --autogenerate` com `compare_type=True` num banco de cópia) e fazer dump de backup. Rodar a nova migration com `IF NOT EXISTS` ou checagem de existência para não quebrar o ambiente já corrigido à mão.
- **`SECRET_KEY` é a chave Fernet.** Qualquer troca invalida senhas SMTP e o token do OpenRouter armazenados. Se for introduzir `ENCRYPTION_KEY` separada, escrever migração de dados que descriptografa com a antiga e recriptografa com a nova.
- **Uazapi.** Servidores free/demo têm limite de instâncias e devolvem 429; uma instância por empresa pode estourar o limite do seu plano. Validar o limite antes de prometer o passo no wizard. Os nomes dos campos de resposta precisam ser confirmados na spec OpenAPI oficial.
- **Aplicar limites de plano em base existente.** Empresas hoje sem limite podem passar a receber 402/429 assim que a Fase 2 entrar. Fazer rollout em modo aviso primeiro (log + banner) antes de bloquear.
- **Remover UI morta** pode esconder features que você pretendia construir. Decidir "ligar ou remover" item por item na 5a antes de apagar.

## Fora de escopo (registrado, não será feito agora)

- Integração real de Telegram (fica só a flag existente em `EmpresaView`).
- Gateway de pagamento/checkout: o passo sai do wizard e as chaves Stripe seguem editáveis em `EmpresaView`, sem cobrança automatizada. Upgrade de plano é aprovado manualmente pelo superadmin.
- Login social (Google) e verificação de e-mail no cadastro.
- Verificação automática de DNS do domínio próprio (o endpoint continua devolvendo instruções manuais).
- Job agendado para marcar propostas como `expirada` (a Fase 5c só bloqueia o aceite de documento vencido).

## Validação final

- `docker compose down -v && docker compose up --build` a partir de um banco vazio, sem erro de migration.
- Fluxo completo: cadastro → 6 passos do wizard → criar cliente → criar serviço → criar proposta → gerar PDF → enviar por e-mail → enviar por WhatsApp → abrir link público em aba anônima → aceitar → ver o aceite refletido na lista.
- Cotas: com plano gratuito (3 propostas/mês), a 4ª criação deve ser recusada com mensagem clara.
- Multi-tenancy: com dois usuários de empresas diferentes, tentar usar o `cliente_id` da outra empresa numa proposta deve ser recusado.
- Bloqueio: superadmin bloqueia a empresa → login recusado e link público deixa de abrir.
- Mobile: wizard e todos os diálogos em viewport de 375 px sem overflow horizontal.
