<template>
  <div class="setup-page">
    <header class="setup-header">
      <div class="logo">
        <h2>{{ APP_NAME }} <span>Configuração</span></h2>
      </div>
      <button class="skip-btn" @click="router.push('/')">Ir para o painel</button>
    </header>

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

    <div class="step-content-container fade-in">
      <div v-if="error" class="setup-error">{{ error }}</div>

      <!-- STEP 1: MARCA -->
      <div v-if="step === 1" class="step-content text-center">
        <h1 class="step-title">Sua marca</h1>
        <p class="step-subtitle">Logotipo, cor e setor — visíveis nas propostas para clientes.</p>

        <div class="form-grid">
          <div class="field">
            <label for="nome-empresa">Nome da empresa</label>
            <InputText id="nome-empresa" v-model="form.empresa" placeholder="Sua Empresa Ltda" maxlength="60" />
            <small class="char-count">{{ form.empresa.length }} / 60 caracteres</small>
          </div>

          <div class="field">
            <label for="telefone">Telefone</label>
            <InputText id="telefone" v-model="form.telefone" placeholder="+55 (11) 99999-9999" />
            <small class="help-text">Usado como contato nas propostas que seus clientes visualizam.</small>
          </div>

          <h3 class="section-title">País e fuso horário</h3>
          <p class="section-subtitle">Usado para agendamento de propostas e relatórios.</p>

          <div class="field-row">
            <div class="field">
              <label for="pais">País</label>
              <select id="pais" v-model="form.pais" class="custom-select">
                <option value="Brasil">Brasil</option>
              </select>
            </div>
            <div class="field">
              <label for="fuso">Fuso horário</label>
              <select id="fuso" v-model="form.fuso" class="custom-select">
                <option value="GMT-3">Brasília (GMT-3)</option>
                <option value="GMT-4">Manaus (GMT-4)</option>
                <option value="GMT-2">Fernando de Noronha (GMT-2)</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label for="moeda">Moeda padrão</label>
            <small class="help-text-top">Usada em propostas e relatórios.</small>
            <select id="moeda" v-model="form.moeda" class="custom-select w-half">
              <option value="BRL">R$ Real (BRL)</option>
            </select>
          </div>

          <div class="field">
            <label for="idioma">Idioma</label>
            <select id="idioma" v-model="form.idioma" class="custom-select w-half">
              <option value="PT">Português</option>
            </select>
          </div>

          <div class="field">
            <label>Logotipo da empresa</label>
            <div class="upload-area">
              <button type="button" class="upload-circle" @click="$refs.logoFile.click()">
                <i class="pi pi-upload"></i>
                <span v-if="!logoPreview">Carregar</span>
                <img v-else :src="logoPreview" alt="Logo preview" class="logo-preview-img" />
              </button>
              <input ref="logoFile" type="file" accept="image/*" @change="handleLogoUpload" style="display:none" />
              <div class="upload-info">
                <p>JPG, PNG, WebP ou SVG</p>
                <p>Tamanho máximo 2 MB</p>
              </div>
            </div>
            <small v-if="uploadingLogo" class="help-text">Enviando...</small>
          </div>

          <div class="field">
            <label>Cor da marca</label>
            <div class="color-options">
              <button
                v-for="c in predefinedColors" :key="c"
                type="button"
                class="color-circle"
                :style="{ background: c, border: form.cor_marca === c ? '2px solid white' : 'none', outline: form.cor_marca === c ? '2px solid #3b82f6' : 'none' }"
                @click="form.cor_marca = c"
              ></button>
            </div>
            <div class="custom-color">
              <span>Cor personalizada</span>
              <div class="color-preview" :style="{ background: form.cor_marca }"></div>
              <input type="color" v-model="form.cor_marca" class="color-input" style="width:50px; padding:0; border:none; background:none; cursor:pointer;" />
            </div>
          </div>

          <div class="field">
            <label for="setor">Setor</label>
            <select id="setor" v-model="form.setor" class="custom-select">
              <option value="Tecnologia">Tecnologia</option>
              <option value="Marketing">Marketing</option>
              <option value="Design">Design</option>
              <option value="Consultoria">Consultoria</option>
              <option value="Advocacia">Advocacia</option>
              <option value="Engenharia">Engenharia</option>
              <option value="Arquitetura">Arquitetura</option>
              <option value="Saúde">Saúde</option>
              <option value="Educação">Educação</option>
              <option value="Comércio">Comércio</option>
              <option value="Serviços">Serviços</option>
              <option value="Outro">Outro</option>
            </select>
          </div>

          <button type="button" class="skip-link" @click="nextStep">Pular (configurar depois)</button>
        </div>
      </div>

      <!-- STEP 2: PLANO -->
      <div v-if="step === 2" class="step-content text-center">
        <div class="plan-icon"><i class="pi pi-sparkles"></i></div>
        <h1 class="step-title">Escolha seu plano</h1>
        <p class="step-subtitle">O plano gratuito permite 3 propostas por mês. Faça upgrade quando precisar.</p>

        <div v-if="stepError" class="setup-error">{{ stepError }}</div>

        <div class="billing-toggle">
          <span>Faturamento</span>
          <div class="toggle-buttons">
            <button :class="{ active: billingCycle === 'mensal' }" @click="billingCycle = 'mensal'">Mensal</button>
            <button :class="{ active: billingCycle === 'anual' }" @click="billingCycle = 'anual'">Anual</button>
          </div>
        </div>

        <div class="plans-grid">
          <div
            v-for="plano in planosDisponiveis" :key="plano.slug"
            class="plan-card"
            :class="{ active: planosSelected === plano.slug }"
            @click="planosSelected = plano.slug"
          >
            <div v-if="planosSelected === plano.slug" class="plan-check"><i class="pi pi-check"></i></div>
            <div v-if="plano.destaque" class="popular-badge">MAIS POPULAR</div>
            <h3>{{ plano.nome }}</h3>
            <div class="price" v-if="billingCycle === 'mensal' && plano.preco_mensal">
              {{ formatCurrency(plano.preco_mensal) }}<span>/mês</span>
            </div>
            <div class="price" v-else-if="billingCycle === 'anual' && plano.preco_anual">
              {{ formatCurrency(plano.preco_anual / 12) }}<span>/mês</span>
            </div>
            <div class="price" v-else>Grátis</div>
            <ul class="plan-features">
              <li v-if="plano.max_propostas_mes">Propostas mensais: {{ plano.max_propostas_mes }}</li>
              <li v-if="plano.max_usuarios">Usuários: {{ plano.max_usuarios }}</li>
              <li v-if="!plano.max_propostas_mes">Propostas: Ilimitado</li>
              <li v-if="!plano.max_usuarios">Usuários: Ilimitado</li>
              <li>Domínio próprio: {{ plano.permite_dominio_proprio ? 'Sim' : 'Não' }}</li>
            </ul>
          </div>
        </div>

        <p v-if="planoSelecionadoPreco" class="tax-info">Após selecionar, seu plano e novos limites serão ativados instantaneamente.</p>
        <button type="button" class="skip-link" @click="nextStep">Continuar</button>
      </div>

      <!-- STEP 3: DOMÍNIO -->
      <div v-if="step === 3" class="step-content text-center">
        <div class="domain-icon"><i class="pi pi-globe"></i></div>
        <h1 class="step-title">Configurações de domínio</h1>
        <p class="step-subtitle">Defina o endereço onde suas propostas serão exibidas</p>

        <div class="domain-box">
          <h3>Subdomínio</h3>
          <p>Endereço onde suas propostas serão publicadas</p>
          <div class="subdomain-input">
            <input type="text" v-model="form.subdominio" placeholder="sua-empresa" />
            <span class="domain-suffix">.{{ ROOT_DOMAIN }}</span>
          </div>
          <div class="subdomain-preview">
            {{ form.subdominio || 'sua-empresa' }}.{{ ROOT_DOMAIN }}/p/exemplo
          </div>
        </div>

        <div class="domain-box mt-4">
          <h3>Domínio personalizado (opcional)</h3>
          <p>Use um domínio que você controla (ex.: propostas.suaempresa.com). Requer plano Pro ou Empresarial.</p>
          <div class="custom-domain-input">
            <input type="text" v-model="form.dominio_personalizado" placeholder="propostas.empresa.com" />
            <button type="button" class="add-btn" @click="handleVerifyDomain">Verificar</button>
          </div>
          <small class="domain-note">Não use https nem www. Exemplo: propostas.seusite.com</small>
        </div>
      </div>

      <!-- STEP 4: WHATSAPP -->
      <div v-if="step === 4" class="step-content text-center">
        <h1 class="step-title">WhatsApp</h1>
        <p class="step-subtitle">Envie propostas diretamente pelo WhatsApp dos seus clientes.</p>
        <WhatsAppConnect />
      </div>

      <!-- STEP 5: E-MAIL (SMTP) -->
      <div v-if="step === 5" class="step-content text-center">
        <div class="domain-icon"><i class="pi pi-envelope"></i></div>
        <h1 class="step-title">Configurar E-mail</h1>
        <p class="step-subtitle">Configure seu servidor SMTP para envio de propostas por e-mail.</p>

        <div class="form-grid">
          <div class="field">
            <label for="smtp-host">Servidor SMTP</label>
            <InputText id="smtp-host" v-model="form.smtp_host" placeholder="smtp.gmail.com" />
          </div>
          <div class="field">
            <label for="smtp-port">Porta</label>
            <select id="smtp-port" v-model="form.smtp_port" class="custom-select">
              <option :value="null">Selecione...</option>
              <option :value="587">587 (TLS)</option>
              <option :value="465">465 (SSL)</option>
              <option :value="25">25</option>
            </select>
          </div>
          <div class="field">
            <label for="smtp-user">Usuário</label>
            <InputText id="smtp-user" v-model="form.smtp_user" placeholder="seu-email@gmail.com" />
          </div>
          <div class="field">
            <label for="smtp-pass">Senha</label>
            <InputText id="smtp-pass" type="password" v-model="form.smtp_password" placeholder="••••••••" />
          </div>

          <Button label="Testar envio" icon="pi pi-send" severity="secondary" @click="handleTestSmtp" :loading="testingSmtp" />

          <div v-if="smtpTestOk" class="smtp-ok"><i class="pi pi-check"></i> E-mail de teste enviado com sucesso!</div>
          <div v-if="smtpTestError" class="smtp-error-msg"><i class="pi pi-times"></i> {{ smtpTestError }}</div>
        </div>
      </div>

      <!-- STEP 6: REVISÃO E CONCLUSÃO -->
      <div v-if="step === 6" class="step-content text-center">
        <div class="domain-icon"><i class="pi pi-check-circle"></i></div>
        <h1 class="step-title">Revisão</h1>
        <p class="step-subtitle">Verifique suas configurações antes de começar a usar o {{ APP_NAME }}.</p>

        <div class="review-list">
          <div class="review-item">
            <strong>Empresa:</strong>
            <span :class="{ 'review-empty': !form.empresa }">{{ form.empresa || 'Não configurada' }}</span>
          </div>
          <div class="review-item">
            <strong>Telefone:</strong>
            <span :class="{ 'review-empty': !form.telefone }">{{ form.telefone || 'Não configurado' }}</span>
          </div>
          <div class="review-item">
            <strong>Plano:</strong>
            <span>{{ planoAtual?.nome || 'Gratuito' }}</span>
          </div>
          <div class="review-item">
            <strong>Subdomínio:</strong>
            <span>{{ form.subdominio || 'sua-empresa' }}.{{ ROOT_DOMAIN }}</span>
          </div>
          <div class="review-item">
            <strong>WhatsApp:</strong>
            <span :class="{ 'review-ok': whatsappConectado, 'review-empty': !whatsappConectado }">
              {{ whatsappConectado ? 'Conectado' : 'Não conectado' }}
            </span>
          </div>
          <div class="review-item">
            <strong>E-mail:</strong>
            <span :class="{ 'review-ok': form.smtp_host, 'review-empty': !form.smtp_host }">
              {{ form.smtp_host ? form.smtp_host + ':' + form.smtp_port : 'Não configurado' }}
            </span>
          </div>
        </div>

        <p v-if="!form.smtp_host" class="review-warning">
          <i class="pi pi-exclamation-triangle"></i> Configure o SMTP para conseguir enviar propostas por e-mail.
        </p>

        <div v-if="loading" class="wpp-loading">
          <i class="pi pi-spin pi-spinner"></i>
          <span>Finalizando configuração...</span>
        </div>
      </div>
    </div>

    <footer class="setup-footer">
      <button class="nav-btn prev" :disabled="step === 1" @click="prevStep">
        <i class="pi pi-arrow-left"></i> Voltar
      </button>
      <div class="step-counter">{{ step }} / {{ steps.length }}</div>
      <button class="nav-btn next" @click="step < steps.length ? nextStep() : finishSetup()">
        <span v-if="step < steps.length">Próximo</span>
        <span v-else>Concluir</span>
        <i v-if="step < steps.length" class="pi pi-arrow-right"></i>
        <i v-else class="pi pi-check"></i>
      </button>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import api from '../services/api'
import { APP_NAME, ROOT_DOMAIN } from '../config/branding'
import WhatsAppConnect from '../components/WhatsAppConnect.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const stepError = ref('')
const uploadingLogo = ref(false)
const logoPreview = ref(null)
const logoFile = ref(null)
const testingSmtp = ref(false)
const smtpTestOk = ref(false)
const smtpTestError = ref('')
const billingCycle = ref('mensal')

const step = ref(1)
const steps = [
  { id: 1, label: 'Marca' },
  { id: 2, label: 'Plano' },
  { id: 3, label: 'Domínio' },
  { id: 4, label: 'WhatsApp' },
  { id: 5, label: 'E-mail' },
  { id: 6, label: 'Revisão' },
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
  smtp_host: '',
  smtp_port: null,
  smtp_user: '',
  smtp_password: '',
})

const planosDisponiveis = ref([])
const planosSelected = ref('gratuito')
const planoAtual = ref(null)
const whatsappConectado = ref(false)

const planoSelecionadoPreco = computed(() => {
  const p = planosDisponiveis.value.find(pl => pl.slug === planosSelected.value)
  return p?.preco_mensal && p.preco_mensal > 0
})

const predefinedColors = ['#6366f1', '#3b82f6', '#14b8a6', '#22c55e', '#f97316', '#ef4444', '#ec4899', '#64748b']

function formatCurrency(val) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
}

async function handleLogoUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    error.value = 'O arquivo deve ter no máximo 2 MB.'
    return
  }
  uploadingLogo.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/api/empresas/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    logoPreview.value = data.logo_url
    if (logoPreview.value && !logoPreview.value.startsWith('http')) {
      const baseUrl = (api.defaults.baseURL || '').replace(/\/+$/, '')
      logoPreview.value = baseUrl + logoPreview.value
    }
  } catch (e) {
    error.value = 'Erro ao fazer upload da logo'
  } finally {
    uploadingLogo.value = false
  }
}

async function handleVerifyDomain() {
  try {
    await api.post('/api/empresas/me/dominio/verificar')
    alert('Verificação solicitada. Siga as instruções de DNS.')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao verificar domínio'
  }
}

async function handleTestSmtp() {
  smtpTestOk.value = false
  smtpTestError.value = ''
  testingSmtp.value = true
  try {
    await api.post('/api/empresas/me/smtp/testar', {
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_user: form.smtp_user,
      smtp_password: form.smtp_password,
    })
    smtpTestOk.value = true
  } catch (e) {
    smtpTestError.value = e.response?.data?.detail || 'Falha ao testar SMTP'
  } finally {
    testingSmtp.value = false
  }
}

async function saveStep1() {
  if (!form.empresa.trim()) return
  try {
    await api.put('/api/empresas/me', {
      razao_social: form.empresa,
      nome_fantasia: form.empresa,
      telefone: form.telefone || null,
      pais: form.pais,
      fuso_horario: form.fuso,
      moeda: form.moeda,
      idioma: form.idioma,
      setor: form.setor,
      cor_marca: form.cor_marca,
    })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao salvar'
    throw e
  }
}

async function saveEnvioPlano() {
  try {
    await api.post('/api/planos/me/solicitar', { slug: planosSelected.value })
  } catch (e) {
    stepError.value = e.response?.data?.detail || 'Erro ao selecionar plano'
  }
}

async function saveStep3() {
  if (!form.subdominio && !form.dominio_personalizado) return
  try {
    await api.put('/api/empresas/me/dominio', {
      subdominio: form.subdominio || null,
      dominio_personalizado: form.dominio_personalizado || null,
    })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao salvar domínio'
  }
}

async function saveStep5() {
  if (!form.smtp_host) return
  try {
    await api.put('/api/empresas/me', {
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_user: form.smtp_user,
      smtp_password: form.smtp_password || null,
    })
    smtpTestOk.value = false
    smtpTestError.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao salvar SMTP'
  }
}

async function nextStep() {
  stepError.value = ''
  error.value = ''
  try {
    if (step.value === 1) await saveStep1()
    if (step.value === 2) await saveEnvioPlano()
    if (step.value === 3) await saveStep3()
    if (step.value === 5) await saveStep5()
    step.value++
  } catch {
    // error já definido nas funções
  }
}

function prevStep() {
  if (step.value > 1) step.value--
}

async function finishSetup() {
  loading.value = true
  error.value = ''
  try {
    await api.post('/api/empresas/me/setup-concluir')
    await authStore.fetchUser()
    await authStore.checkSetupStatus()
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao concluir setup'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/api/planos')
    planosDisponiveis.value = data

    const { data: emp } = await api.get('/api/empresas/me')
    if (emp.razao_social && emp.razao_social !== `Empresa de ${authStore.user?.nome || ''}`) {
      form.empresa = emp.razao_social || ''
    }
    form.telefone = emp.telefone || ''
    form.pais = emp.pais || 'Brasil'
    form.fuso = emp.fuso_horario || 'GMT-3'
    form.moeda = emp.moeda || 'BRL'
    form.idioma = emp.idioma || 'PT'
    form.setor = emp.setor || 'Tecnologia'
    form.cor_marca = emp.cor_marca || '#6366f1'
    form.subdominio = emp.subdominio || ''
    form.dominio_personalizado = emp.dominio_personalizado || ''
    form.smtp_host = emp.smtp_host || ''
    form.smtp_port = emp.smtp_port || null
    form.smtp_user = emp.smtp_user || ''
    planosSelected.value = emp.plano || 'gratuito'
    if (emp.logo_url) logoPreview.value = emp.logo_url

    const { data: pData } = await api.get('/api/planos/me/atual')
    planoAtual.value = pData?.detalhes
  } catch {
    planosDisponiveis.value = []
  }
})
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

.stepper-container {
  padding: 2rem 0;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
  overflow-x: auto;
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
  min-width: 60px;
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

.step-circle.active { background-color: var(--primary-500); border-color: var(--primary-500); color: var(--text-primary); }
.step-circle.completed { background-color: var(--accent-green); border-color: var(--accent-green); color: var(--text-primary); }

.step-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; }
.step-label.active { color: var(--text-primary); }

.step-line {
  width: 40px;
  height: 2px;
  background-color: var(--border-color-hover);
  margin-top: -20px;
  min-width: 20px;
}
.step-line.completed { background-color: var(--accent-green); }

.step-content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 3rem 1.5rem;
  overflow-y: auto;
}

.step-content { width: 100%; max-width: 600px; }
.text-center { text-align: center; }

.step-title { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
.step-subtitle { color: var(--text-secondary); margin-bottom: 2.5rem; font-size: 1rem; }

.setup-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  max-width: 600px;
  width: 100%;
}

.form-grid { display: flex; flex-direction: column; gap: 1.5rem; text-align: left; }
.field { display: flex; flex-direction: column; gap: 0.5rem; }
.field label { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }

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

.w-half { width: 50%; }
.char-count, .help-text { color: var(--text-muted); font-size: 0.75rem; }
.help-text-top { color: var(--text-muted); font-size: 0.8rem; margin-top: -0.3rem; margin-bottom: 0.2rem; }

.section-title { margin-top: 1.5rem; font-size: 1.1rem; font-weight: 600; }
.section-subtitle { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem; }

.field-row { display: flex; gap: 1rem; }
.field-row .field { flex: 1; }

.upload-area { display: flex; align-items: center; gap: 1.5rem; margin-top: 0.5rem; }

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
  background: none;
  overflow: hidden;
}
.upload-circle i { font-size: 1.2rem; }

.logo-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.upload-info p { color: var(--text-muted); font-size: 0.85rem; margin: 0.2rem 0; }

.color-options { display: flex; gap: 0.75rem; margin-top: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }

.color-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  background: none;
}

.custom-color { display: flex; align-items: center; gap: 1rem; font-size: 0.9rem; color: var(--text-secondary); }
.color-preview { width: 24px; height: 24px; border-radius: 4px; }

/* Planos */
.plan-icon { font-size: 2rem; margin-bottom: 1rem; color: var(--text-secondary); }

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

.toggle-buttons button.active { background: #333; color: var(--text-primary); }

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
  transition: border-color 0.2s;
}

.plan-card.active { border-color: #22c55e; box-shadow: 0 0 0 1px #22c55e; }

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
}

.plan-card h3 { margin: 0 0 0.5rem 0; font-size: 1.2rem; }
.price { font-size: 1.8rem; font-weight: 700; margin-bottom: 1.5rem; }
.price span { font-size: 1rem; color: var(--text-secondary); font-weight: 400; }

.plan-features { list-style: none; padding: 0; margin: 0; color: var(--text-secondary); font-size: 0.9rem; }
.plan-features li { margin-bottom: 0.5rem; }

.tax-info {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 1.5rem;
  line-height: 1.5;
}

/* Domínio */
.domain-icon { font-size: 2.5rem; color: var(--text-primary); margin-bottom: 1rem; }

.domain-box {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  text-align: left;
}

.domain-box h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
.domain-box p { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem; line-height: 1.4; }

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
  border: 1px solid #222;
}

.mt-4 { margin-top: 1.5rem; }

.custom-domain-input { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
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
.domain-note { color: var(--text-muted); font-size: 0.8rem; }

/* Revisão */
.review-list {
  text-align: left;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.review-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-color);
}

.review-item:last-child { border-bottom: none; }

.review-item strong { color: var(--text-secondary); }
.review-empty { color: var(--text-muted); font-style: italic; }
.review-ok { color: #22c55e; }

.review-warning {
  color: #f97316;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

/* SMTP */
.smtp-ok { color: #22c55e; display: flex; align-items: center; gap: 0.5rem; }
.smtp-error-msg { color: #ef4444; display: flex; align-items: center; gap: 0.5rem; }

/* Footer */
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

.nav-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.nav-btn.next {
  background: var(--primary-500);
  color: var(--text-primary);
  border-color: var(--primary-500);
}

.step-counter { color: var(--text-muted); font-weight: 600; }

.wpp-loading {
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-muted);
}

.skip-link {
  display: block;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  margin: 1.5rem auto 0;
  font-size: 0.9rem;
}

@media (max-width: 700px) {
  .setu-header, .setup-footer { padding: 1rem 1rem; }
  .stepper { flex-wrap: wrap; justify-content: center; row-gap: 1rem; }
  .plans-grid { grid-template-columns: 1fr; }
  .w-half { width: 100%; }
  .step-label { display: none; }
  .step-line { min-width: 10px; width: 20px; }
}
</style>
