<template>
  <div class="setup-page">
    <!-- Header -->
    <header class="setup-header">
      <div class="logo">
        <h2>Dekto <span>Configuração</span></h2>
      </div>
      <button class="skip-btn" @click="finishSetup">Ir para o painel</button>
    </header>

    <!-- Stepper -->
    <div class="stepper-container">
      <div class="stepper">
        <template v-for="(s, index) in steps" :key="s.id">
          <div class="step-wrapper">
            <div 
              class="step-circle" 
              :class="{ active: step === s.id, completed: step > s.id }"
            >
              <i v-if="step > s.id" class="pi pi-check"></i>
              <span v-else>{{ s.id }}</span>
            </div>
            <span class="step-label" :class="{ active: step === s.id }">{{ s.label }}</span>
          </div>
          <div v-if="index < steps.length - 1" class="step-line" :class="{ completed: step > s.id }"></div>
        </template>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="step-content-container fade-in">
      
      <!-- STEP 1: MARCA -->
      <div v-if="step === 1" class="step-content text-center">
        <h1 class="step-title">A sua marca</h1>
        <p class="step-subtitle">Logótipo, cor e setor — visíveis nas propostas para clientes.</p>

        <div class="form-grid">
          <div class="field">
            <label>Nome da empresa</label>
            <InputText v-model="form.empresa" placeholder="Fernando Dias Oliveira's Team" />
            <small class="char-count">{{ form.empresa.length }} / 60 caracteres</small>
          </div>

          <div class="field">
            <label>Telefone</label>
            <InputText v-model="form.telefone" placeholder="+351 9** *** ***" />
            <small class="help-text">Usado apenas nas propostas que você cria, como contato que seus clientes veem na oferta e na página de agradecimento.</small>
          </div>
          
          <h3 class="section-title">País e fuso horário</h3>
          <p class="section-subtitle">Usado para agendamento de propostas e relatórios.</p>

          <div class="field-row">
            <div class="field">
              <label>País</label>
              <select v-model="form.pais" class="custom-select">
                <option value="Brasil">Brasil</option>
                <option value="Portugal">Portugal</option>
              </select>
            </div>
            <div class="field">
              <label>Fuso horário</label>
              <select v-model="form.fuso" class="custom-select">
                <option value="GMT-3">São Paulo (GMT-3) - Horário Padrão de B...</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label>Moeda padrão</label>
            <small class="help-text-top">Usada em propostas e relatórios.</small>
            <select v-model="form.moeda" class="custom-select w-half">
              <option value="BRL">R$ Brazilian Real (BRL)</option>
              <option value="GBP">£ British Pound (GBP)</option>
              <option value="EUR">€ Euro (EUR)</option>
            </select>
          </div>

          <div class="field">
            <label>Idioma de comunicação da organização</label>
            <small class="help-text-top">Idioma dos e-mails do sistema enviados para sua organização</small>
            <select v-model="form.idioma" class="custom-select w-half">
              <option value="PT">Português</option>
              <option value="EN">English</option>
            </select>
          </div>

          <div class="field logo-upload">
            <label>Logótipo da empresa</label>
            <div class="upload-area">
              <div class="upload-circle">
                <i class="pi pi-upload"></i>
                <span>Carregar</span>
              </div>
              <div class="upload-info">
                <p>JPG, PNG, WebP ou SVG</p>
                <p>Tamanho máximo 2 MB</p>
              </div>
            </div>
          </div>

          <div class="field brand-colors">
            <label>Cor da marca</label>
            <div class="color-options">
              <div 
                v-for="c in predefinedColors" :key="c" 
                class="color-circle" 
                :style="{ background: c, border: form.cor_marca === c ? '2px solid white' : 'none', outline: form.cor_marca === c ? '2px solid #3b82f6' : 'none' }"
                @click="form.cor_marca = c"
              ></div>
            </div>
            <div class="custom-color">
              <span>Cor personalizada</span>
              <div class="color-preview" :style="{ background: form.cor_marca }"></div>
              <input type="color" v-model="form.cor_marca" class="color-input" style="width:50px; padding:0; border:none; background:none; cursor:pointer;" />
            </div>
          </div>

          <div class="field">
            <label>Setor</label>
            <select v-model="form.setor" class="custom-select">
              <option value="Outro">Outro</option>
              <option value="Tecnologia">Tecnologia</option>
            </select>
          </div>

          <!-- Preview Card -->
          <div class="preview-card">
            <div class="preview-header">PRÉ-VISUALIZAÇÃO</div>
            <div class="preview-content">
              <div class="preview-logo">AB</div>
              <div class="preview-text">
                <h4>{{ form.empresa || 'Sua Empresa' }}</h4>
                <p>{{ form.setor || 'Setor' }}</p>
              </div>
            </div>
            <button class="preview-btn">Ver proposta</button>
          </div>
        </div>
      </div>

      <!-- STEP 2: PLANO -->
      <div v-if="step === 2" class="step-content text-center">
        <div class="plan-icon"><i class="pi pi-sparkles"></i></div>
        <h1 class="step-title">Escolha o seu plano</h1>
        <p class="step-subtitle">Pode alterá-lo mais tarde na faturação. Não é necessário pagamento durante a configuração.</p>

        <div class="billing-toggle">
          <span>Faturação</span>
          <div class="toggle-buttons">
            <button class="active">Mensal</button>
            <button>Anual</button>
          </div>
          <span class="annual-discount">Anual: pague 11 meses e use 12.</span>
        </div>

        <div class="plans-grid">
          <div class="plan-card active">
            <div class="plan-check"><i class="pi pi-check"></i></div>
            <h3>Grátis</h3>
            <div class="price">Grátis</div>
            <ul class="plan-features">
              <li>Propostas mensais: 3</li>
              <li>Limite de usuários: 1</li>
            </ul>
          </div>
          <div class="plan-card">
            <h3>Inicial</h3>
            <div class="price">€39<span>/mês</span></div>
            <ul class="plan-features">
              <li>Propostas mensais: 20</li>
              <li>Limite de usuários: 2</li>
            </ul>
          </div>
          <div class="plan-card">
            <div class="popular-badge">MAIS POPULAR</div>
            <h3>Pro</h3>
            <div class="price">€69<span>/mês</span></div>
            <ul class="plan-features">
              <li>Propostas mensais: 50</li>
              <li>Limite de usuários: 5</li>
            </ul>
          </div>
          <div class="plan-card">
            <h3>Empresarial</h3>
            <div class="price">€129<span>/mês</span></div>
            <ul class="plan-features">
              <li>Propostas mensais: Ilimitado</li>
              <li>Limite de usuários: Ilimitado</li>
            </ul>
          </div>
        </div>

        <p class="tax-info">Os preços não incluem IVA; é adicionado no pagamento conforme o seu país. Com um número fiscal válido, não é cobrado IVA.</p>
        <button class="compare-btn"><i class="pi pi-table"></i> Comparar todos os planos</button>
      </div>

      <!-- STEP 3: DOMÍNIO -->
      <div v-if="step === 3" class="step-content text-center">
        <div class="domain-icon"><i class="pi pi-globe"></i></div>
        <h1 class="step-title">Configurações de domínio</h1>
        <p class="step-subtitle">Defina o endereço onde suas propostas serão exibidas</p>

        <div class="domain-box">
          <h3>Subdomínio</h3>
          <p>Defina o endereço onde suas propostas serão exibidas</p>
          <div class="subdomain-input">
            <input type="text" v-model="form.subdominio" placeholder="sua-empresa" />
            <span class="domain-suffix">.dekto.com</span>
          </div>
          <div class="subdomain-preview">
            {{ form.subdominio || 'sua-empresa' }}.dekto.com/p/proposta-exemplo
          </div>
          <div class="status-active"><i class="pi pi-check"></i> Subdomínio ativo</div>
        </div>

        <div class="domain-box mt-4">
          <h3>Domínio personalizado (opcional)</h3>
          <p>Use um subdomínio que controla (ex.: propostas.suaempresa.com). As propostas aparecem em propostas.suaempresa.com/p/abc. Reforça a imagem da empresa.</p>
          <div class="custom-domain-input">
            <input type="text" v-model="form.dominio_personalizado" placeholder="propostas.empresa.com" />
            <button class="add-btn" @click.prevent="alert('Verificação de domínio será ativada no futuro!')">Verificar</button>
          </div>
          <small class="domain-note">Nota: não use https nem www. Exemplo: propostas.seusite.com</small>
        </div>
      </div>

      <!-- STEP 4: WHATSAPP -->
      <div v-if="step === 4" class="step-content text-center">
        <div class="whatsapp-icon"><i class="pi pi-whatsapp"></i></div>
        <h1 class="step-title">Propostas por WhatsApp</h1>
        <p class="step-subtitle">Conecte sua conta do WhatsApp para que as propostas também possam ser enviadas aos clientes pelo WhatsApp — assim como o e-mail.</p>

        <div class="whatsapp-box">
          <div class="whatsapp-box-icon"><i class="pi pi-whatsapp"></i></div>
          <h3>Conectar WhatsApp</h3>
          <p>Escaneie o QR code com o WhatsApp para conectar sua conta.</p>
          
          <div class="privacy-alert">
            <i class="pi pi-shield"></i>
            <div>
              <strong>A sua privacidade está protegida</strong>
              <p>Não conseguimos ver as suas mensagens. Apenas acionamos propostas e lembretes.</p>
            </div>
          </div>

          <button class="connect-wpp-btn" @click="form.whatsapp_conectado = !form.whatsapp_conectado">
            <i class="pi pi-qrcode"></i> {{ form.whatsapp_conectado ? 'WhatsApp Conectado' : 'Conectar WhatsApp' }}
          </button>
        </div>
      </div>

      <!-- STEP 5: TELEGRAM -->
      <div v-if="step === 5" class="step-content text-center">
        <h1 class="step-title">Notificações Telegram</h1>
        <p class="step-subtitle">Receba alertas quando os clientes interagem com as suas propostas.</p>

        <div class="telegram-box">
          <div class="tg-icon"><i class="pi pi-telegram"></i></div>
          <div class="tg-content">
            <h3>Atualizações em tempo real</h3>
            <ul>
              <li>- Quando uma proposta é aberta</li>
              <li>- Aceitação ou recusa</li>
              <li>- Pagamentos e sinais</li>
              <li>- Pedidos de chamada de volta</li>
            </ul>
          </div>
        </div>

        <button class="connect-tg-btn" @click="form.telegram_conectado = !form.telegram_conectado">
          <i class="pi pi-telegram"></i> {{ form.telegram_conectado ? 'Telegram Conectado' : 'Ligar Telegram' }}
        </button>
        <button class="skip-link" @click="nextStep">Saltar por agora</button>
      </div>

      <!-- STEP 6: PAGAMENTO -->
      <div v-if="step === 6" class="step-content text-center">
        <h1 class="step-title">Pagamentos</h1>
        <p class="step-subtitle">Ligue Stripe ou PayTR para receber pagamentos nas propostas (opcional).</p>

        <div class="payment-tabs">
          <button class="active">Stripe</button>
          <button>PayTR</button>
          <button><i class="pi pi-building"></i> Transferência bancária</button>
        </div>

        <div class="payment-form">
          <div class="field">
            <label>Publishable key</label>
            <InputText v-model="form.stripe_publishable_key" placeholder="pk_test_..." />
          </div>
          <div class="field">
            <label>Secret key</label>
            <InputText v-model="form.stripe_secret_key" placeholder="sk_test_..." />
          </div>
          
          <div class="test-mode-toggle" @click="form.pagamento_modo_teste = !form.pagamento_modo_teste" style="cursor: pointer;">
            <div class="tm-label">
              <i class="pi pi-shield"></i> Modo de teste
            </div>
            <div class="toggle-switch" :class="{ active: form.pagamento_modo_teste }"></div>
          </div>

          <div class="security-info">
            <i class="pi pi-credit-card"></i>
            <span>As chaves são encriptadas e armazenadas com segurança. Pode alterá-las nas definições.</span>
          </div>

          <button class="save-continue-btn" @click="finishSetup">Guardar e continuar</button>
          <button class="skip-link" @click="finishSetup">Saltar e concluir</button>
        </div>
      </div>

    </div>

    <!-- Footer Controls -->
    <footer class="setup-footer">
      <button class="nav-btn prev" :disabled="step === 1" @click="prevStep">
        <i class="pi pi-arrow-left"></i> Voltar
      </button>
      <div class="step-counter">{{ step }} / {{ steps.length }}</div>
      <button class="nav-btn next" @click="nextStep">
        <span v-if="step < steps.length">Próximo</span>
        <span v-else>Concluir</span>
        <i v-if="step < steps.length" class="pi pi-arrow-right"></i>
        <i v-else class="pi pi-check"></i>
      </button>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')

const step = ref(1)
const steps = [
  { id: 1, label: 'Marca' },
  { id: 2, label: 'Plano' },
  { id: 3, label: 'Domínio' },
  { id: 4, label: 'WhatsApp' },
  { id: 5, label: 'Telegram' },
  { id: 6, label: 'Pagamento' },
]

const form = reactive({
  empresa: '',
  telefone: '',
  pais: 'Brasil',
  fuso: 'GMT-3',
  moeda: 'BRL',
  idioma: 'PT',
  setor: 'Tecnologia',
  subdominio: '',
  cor_marca: '#6366f1',
  dominio_personalizado: '',
  whatsapp_conectado: false,
  telegram_conectado: false,
  stripe_publishable_key: '',
  stripe_secret_key: '',
  pagamento_modo_teste: true
})

const predefinedColors = ['#6366f1', '#3b82f6', '#14b8a6', '#22c55e', '#f97316', '#ef4444', '#ec4899', '#64748b']

onMounted(() => {
  if (authStore.user?.nome) {
    form.empresa = `Empresa de ${authStore.user.nome}`
    form.subdominio = authStore.user.nome.toLowerCase().replace(/\s+/g, '-') + '-' + Math.floor(Math.random() * 1000)
  }
})

function nextStep() {
  if (step.value < steps.length) {
    step.value++
  } else {
    finishSetup()
  }
}

function prevStep() {
  if (step.value > 1) {
    step.value--
  }
}

async function finishSetup() {
  loading.value = true
  error.value = ''
  
  try {
    // Save company details
    await api.put('/api/empresas/me', {
      razao_social: form.empresa,
      nome_fantasia: form.empresa,
      telefone: form.telefone || 'N/A', // backend needs this to mark setup as done
      pais: form.pais,
      fuso_horario: form.fuso,
      moeda: form.moeda,
      idioma: form.idioma,
      setor: form.setor,
      cor_marca: form.cor_marca,
      subdominio: form.subdominio,
      dominio_personalizado: form.dominio_personalizado || null,
      whatsapp_conectado: form.whatsapp_conectado,
      telegram_conectado: form.telegram_conectado,
      stripe_publishable_key: form.stripe_publishable_key || null,
      stripe_secret_key: form.stripe_secret_key || null,
      pagamento_modo_teste: form.pagamento_modo_teste
    })
    
    // Refresh user and setup status
    await authStore.fetchUser()
    await authStore.checkSetupStatus()
    
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao salvar configurações'
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.setup-page {
  min-height: 100vh;
  background-color: var(--bg-app);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
}

/* Header */
.setup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 3rem;
  border-bottom: 1px solid var(--border-color);
}

.logo h2 {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 0;
}

.logo span {
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 0.5rem;
}

.skip-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
}
.skip-btn:hover {
  color: var(--text-primary);
}

/* Stepper */
.stepper-container {
  padding: 2rem 0;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
}

.stepper {
  display: flex;
  align-items: center;
  gap: 0;
}

.step-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  width: 80px;
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--bg-card-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  color: var(--text-secondary);
  border: 1px solid var(--border-color-hover);
}

.step-circle.active {
  background-color: var(--primary-500);
  border-color: var(--primary-500);
  color: var(--text-primary);
}

.step-circle.completed {
  background-color: var(--accent-green);
  border-color: var(--accent-green);
  color: var(--text-primary);
}

.step-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.step-label.active {
  color: var(--text-primary);
}

.step-line {
  width: 40px;
  height: 2px;
  background-color: var(--border-color-hover);
  margin-top: -20px;
}

.step-line.completed {
  background-color: var(--accent-green);
}

/* Main Content */
.step-content-container {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 3rem 1.5rem;
  overflow-y: auto;
}

.step-content {
  width: 100%;
  max-width: 600px;
}

.text-center {
  text-align: center;
}

.step-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.step-subtitle {
  color: var(--text-secondary);
  margin-bottom: 2.5rem;
  font-size: 1rem;
}

/* Form Styles */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  text-align: left;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.field :deep(.p-inputtext) {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  width: 100%;
}

.custom-select {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  width: 100%;
  appearance: none;
}

.w-half {
  width: 50%;
}

.char-count, .help-text {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.help-text-top {
  color: var(--text-muted);
  font-size: 0.8rem;
  margin-top: -0.3rem;
  margin-bottom: 0.2rem;
}

.section-title {
  margin-top: 1.5rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.section-subtitle {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.field-row {
  display: flex;
  gap: 1rem;
}
.field-row .field {
  flex: 1;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-top: 0.5rem;
}

.upload-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 1px dashed var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
  gap: 0.3rem;
}
.upload-circle i {
  font-size: 1.2rem;
}

.upload-info p {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin: 0.2rem 0;
}

.brand-colors {
  margin-top: 1rem;
}

.color-options {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
  margin-bottom: 1rem;
}

.color-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
}
.color-circle:first-child {
  border-color: #fff;
}

.custom-color {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}
.color-input {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 0.4rem 1rem;
  border-radius: 6px;
  color: var(--text-primary);
}

.preview-card {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1.5rem;
}

.preview-header {
  font-size: 0.75rem;
  color: var(--text-muted);
  letter-spacing: 1px;
  margin-bottom: 1.5rem;
}

.preview-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.preview-logo {
  width: 48px;
  height: 48px;
  background: #6366f1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
}

.preview-text h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}
.preview-text p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 0.2rem;
}

.preview-btn {
  background: #6366f1;
  color: var(--text-primary);
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

/* Step 2: Planos */
.plan-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.billing-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.toggle-buttons {
  display: flex;
  background: var(--bg-card);
  border-radius: 8px;
  padding: 4px;
}

.toggle-buttons button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.5rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.toggle-buttons button.active {
  background: #333;
  color: var(--text-primary);
}

.annual-discount {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  max-width: 700px;
  margin: 0 auto;
}

.plan-card {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: left;
  position: relative;
  cursor: pointer;
}

.plan-card.active {
  border-color: #22c55e;
  box-shadow: 0 0 0 1px #22c55e;
}

.plan-check {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 24px;
  height: 24px;
  background: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-size: 0.8rem;
}

.popular-badge {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  background: #fff;
  color: #000;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  letter-spacing: 0.5px;
}

.plan-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
}

.price {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}
.price span {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 400;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.plan-features li {
  margin-bottom: 0.5rem;
}

.tax-info {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 2rem;
  line-height: 1.5;
}

.compare-btn {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* Step 3: Domínio */
.domain-icon {
  font-size: 2.5rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.domain-box {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  text-align: left;
}

.domain-box h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}
.domain-box p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  line-height: 1.4;
}

.subdomain-input {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.subdomain-input input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 0.8rem 1rem;
  outline: none;
}
.domain-suffix {
  padding: 0.8rem 1rem;
  color: var(--text-secondary);
  border-left: 1px solid #333;
  background: var(--bg-app);
}

.subdomain-preview {
  background: var(--bg-card);
  padding: 0.8rem 1rem;
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 1rem;
  border: 1px solid #222;
}

.status-active {
  color: #22c55e;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mt-4 { margin-top: 1.5rem; }

.custom-domain-input {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.custom-domain-input input {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.8rem 1rem;
  border-radius: 8px;
}
.add-btn {
  background: #333;
  color: var(--text-primary);
  border: none;
  padding: 0 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
.domain-note {
  color: var(--text-muted);
}

/* Step 4: WhatsApp */
.whatsapp-icon {
  font-size: 2.5rem;
  color: #22c55e;
  margin-bottom: 1rem;
}

.whatsapp-box {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2.5rem 2rem;
  margin-top: 2rem;
}

.whatsapp-box-icon {
  width: 48px;
  height: 48px;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin: 0 auto 1rem;
}

.whatsapp-box h3 {
  margin: 0 0 0.5rem 0;
}
.whatsapp-box p {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.privacy-alert {
  background: rgba(34, 197, 94, 0.05);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  text-align: left;
  margin-bottom: 2rem;
}
.privacy-alert i {
  color: #22c55e;
  margin-top: 0.2rem;
}
.privacy-alert strong {
  color: #22c55e;
  display: block;
  margin-bottom: 0.2rem;
  font-size: 0.9rem;
}
.privacy-alert p {
  margin: 0;
  font-size: 0.85rem;
  color: #22c55e;
  opacity: 0.8;
}

.connect-wpp-btn {
  background: #f1f1f1;
  color: #000;
  border: none;
  width: 100%;
  padding: 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

/* Step 5: Telegram */
.telegram-box {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  margin: 2rem auto;
  display: flex;
  gap: 1.5rem;
  text-align: left;
}

.tg-icon {
  width: 48px;
  height: 48px;
  background: rgba(56, 189, 248, 0.1);
  color: #38bdf8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.tg-content h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.tg-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
  color: var(--text-secondary);
}
.tg-content ul li {
  margin-bottom: 0.5rem;
}

.connect-tg-btn {
  background: #38bdf8;
  color: #000;
  border: none;
  padding: 0.8rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.skip-link {
  display: block;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  margin: 0 auto;
}
.skip-link:hover {
  color: var(--text-primary);
}

/* Step 6: Pagamentos */
.payment-tabs {
  display: flex;
  background: var(--bg-card);
  border-radius: 8px;
  padding: 4px;
  margin-bottom: 2rem;
}

.payment-tabs button {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.payment-tabs button.active {
  background: #fff;
  color: #000;
}

.payment-form {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.test-mode-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  padding: 1rem;
  border-radius: 8px;
}

.tm-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: #333;
  border-radius: 12px;
  position: relative;
  cursor: pointer;
}
.toggle-switch.active {
  background: #22c55e;
}
.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-switch.active::after {
  transform: translateX(20px);
}

.security-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  padding: 1rem;
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.save-continue-btn {
  background: #f1f1f1;
  color: #000;
  border: none;
  width: 100%;
  padding: 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
}

/* Footer Controls */
.setup-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 3rem;
  border-top: 1px solid var(--border-color);
  background: var(--bg-app);
}

.nav-btn {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border: 1px solid var(--border-color-hover);
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-btn.next {
  background: var(--primary-500);
  color: var(--text-primary);
  border-color: var(--primary-500);
}
.nav-btn.next:hover {
  background: var(--primary-600);
}

.step-counter {
  color: var(--text-muted);
  font-weight: 600;
}
</style>
