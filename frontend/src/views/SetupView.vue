<template>
  <div class="setup-page">
    <!-- Header -->
    <header class="setup-header glass">
      <div class="header-left">
        <div class="logo">
          <h2>{{ APP_NAME }} <span class="setup-badge">Assistente de Configuração</span></h2>
        </div>
      </div>

      <div class="header-right">
        <span class="progress-pill">
          Etapa {{ step }} de {{ steps.length }} ({{ Math.round((step / steps.length) * 100) }}%)
        </span>
        <button class="skip-btn" @click="skipToDashboard">
          <span>Ir para o Painel</span>
          <i class="pi pi-arrow-right"></i>
        </button>
      </div>
    </header>

    <!-- Clickable Interactive Stepper -->
    <div class="stepper-container">
      <div class="stepper-track">
        <template v-for="(s, index) in steps" :key="s.id">
          <!-- Step Clickable Button -->
          <div
            class="step-item"
            :class="{
              active: step === s.id,
              completed: step > s.id,
              clickable: true,
            }"
            @click="goToStep(s.id)"
            :title="`Ir para etapa ${s.id}: ${s.label}`"
          >
            <div class="step-circle">
              <i v-if="step > s.id" class="pi pi-check"></i>
              <i v-else :class="s.icon"></i>
            </div>
            <div class="step-text">
              <span class="step-number">Passo {{ s.id }}</span>
              <span class="step-label">{{ s.label }}</span>
            </div>
          </div>

          <!-- Connecting Line -->
          <div
            v-if="index < steps.length - 1"
            class="step-line"
            :class="{ completed: step > s.id + 1 || (step === s.id + 1 && step > s.id) }"
          ></div>
        </template>
      </div>
    </div>

    <!-- Main Content Container -->
    <main class="step-content-container fade-in">
      <div v-if="error" class="setup-error">
        <i class="pi pi-exclamation-triangle mr-2"></i>
        <span>{{ error }}</span>
      </div>

      <!-- ========================================== -->
      <!-- STEP 1: MARCA & IDENTIDADE VISUAL         -->
      <!-- ========================================== -->
      <div v-if="step === 1" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge brand"><i class="pi pi-palette"></i></div>
          <h1 class="step-title">Identidade da sua Marca</h1>
          <p class="step-subtitle">Personalize a identidade visual e os dados que aparecerão nas suas propostas e orçamentos.</p>
        </div>

        <div class="step-card glass">
          <!-- Live Preview Box -->
          <div class="brand-preview-box" :style="{ borderColor: form.cor_marca }">
            <div class="preview-badge" :style="{ background: form.cor_marca }">Prévia do Cabeçalho da Proposta</div>
            <div class="preview-content">
              <div class="preview-logo-wrapper">
                <img v-if="logoPreview" :src="logoPreview" alt="Logo" class="preview-logo" />
                <div v-else class="preview-logo-placeholder" :style="{ background: form.cor_marca }">
                  <i class="pi pi-image"></i>
                </div>
              </div>
              <div class="preview-meta">
                <h4 class="preview-name">{{ form.empresa || 'Nome da Sua Empresa' }}</h4>
                <p class="preview-contact">{{ form.telefone || '+55 (11) 98765-4321' }} • {{ form.setor }}</p>
              </div>
            </div>
          </div>

          <div class="form-grid">
            <div class="form-row">
              <div class="field flex-2">
                <label for="nome-empresa">Nome da Empresa / Fantasia <span class="required">*</span></label>
                <InputText id="nome-empresa" v-model="form.empresa" placeholder="Ex: Nexus Soluções Digitais" maxlength="60" />
                <small class="char-count">{{ form.empresa.length }} / 60 caracteres</small>
              </div>

              <div class="field flex-1">
                <label for="telefone">Telefone / WhatsApp Comercial</label>
                <InputText id="telefone" v-model="form.telefone" placeholder="+55 (11) 98765-4321" />
              </div>
            </div>

            <!-- Upload Logo & Cor da Marca -->
            <div class="form-row">
              <div class="field flex-1">
                <label>Logotipo da Empresa</label>
                <div class="upload-area">
                  <div class="upload-circle" @click="$refs.logoFile.click()" :title="'Clique para selecionar imagem'">
                    <img v-if="logoPreview" :src="logoPreview" alt="Logo preview" class="logo-preview-img" />
                    <div v-else class="upload-placeholder">
                      <i class="pi pi-cloud-upload"></i>
                      <span>Upload</span>
                    </div>
                  </div>
                  <input ref="logoFile" type="file" accept="image/*" @change="handleLogoUpload" style="display:none" />
                  <div class="upload-info">
                    <button type="button" class="btn-upload-trigger" @click="$refs.logoFile.click()">
                      <i class="pi pi-upload"></i> {{ logoPreview ? 'Alterar Logo' : 'Escolher Arquivo' }}
                    </button>
                    <p class="upload-help">PNG, JPG ou SVG (Máx. 2MB)</p>
                  </div>
                </div>
                <small v-if="uploadingLogo" class="text-primary"><i class="pi pi-spin pi-spinner"></i> Enviando imagem...</small>
              </div>

              <div class="field flex-1">
                <label>Cor Principal da Marca</label>
                <div class="color-picker-wrapper">
                  <div class="color-options">
                    <button
                      v-for="c in predefinedColors"
                      :key="c"
                      type="button"
                      class="color-circle"
                      :style="{ background: c }"
                      :class="{ selected: form.cor_marca === c }"
                      @click="form.cor_marca = c"
                      :title="c"
                    ></button>
                  </div>
                  <div class="custom-color-inline">
                    <input type="color" v-model="form.cor_marca" class="color-native-picker" />
                    <span class="color-hex-code">{{ form.cor_marca }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Setor, País e Moeda -->
            <div class="form-row">
              <div class="field flex-1">
                <label for="setor">Setor de Atuação</label>
                <select id="setor" v-model="form.setor" class="custom-select">
                  <option value="Tecnologia">Tecnologia & Software</option>
                  <option value="Marketing">Marketing & Publicidade</option>
                  <option value="Design">Design & Criatividade</option>
                  <option value="Consultoria">Consultoria Empresarial</option>
                  <option value="Advocacia">Advocacia & Jurídico</option>
                  <option value="Engenharia">Engenharia & Obras</option>
                  <option value="Arquitetura">Arquitetura & Urbanismo</option>
                  <option value="Saúde">Saúde & Bem-estar</option>
                  <option value="Educação">Educação & Treinamentos</option>
                  <option value="Comércio">Comércio & Varejo</option>
                  <option value="Serviços">Prestação de Serviços</option>
                  <option value="Outro">Outro Setor</option>
                </select>
              </div>

              <div class="field flex-1">
                <label for="fuso">Fuso Horário</label>
                <select id="fuso" v-model="form.fuso" class="custom-select">
                  <option value="GMT-3">Brasília (GMT-3)</option>
                  <option value="GMT-4">Manaus (GMT-4)</option>
                  <option value="GMT-2">Fernando de Noronha (GMT-2)</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- STEP 2: ESCOLHA DO PLANO                  -->
      <!-- ========================================== -->
      <div v-if="step === 2" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge plan"><i class="pi pi-sparkles"></i></div>
          <h1 class="step-title">Escolha o Plano Ideal</h1>
          <p class="step-subtitle">Comece no Gratuito e escale sua capacidade comercial conforme sua empresa cresce.</p>
        </div>

        <div v-if="stepError" class="setup-error">{{ stepError }}</div>

        <!-- Billing Toggle -->
        <div class="billing-toggle-container">
          <div class="toggle-pill">
            <button :class="{ active: billingCycle === 'mensal' }" @click="billingCycle = 'mensal'">
              Mensal
            </button>
            <button :class="{ active: billingCycle === 'anual' }" @click="billingCycle = 'anual'">
              Anual <span class="discount-badge">-15% OFF</span>
            </button>
          </div>
        </div>

        <!-- Plans Grid -->
        <div class="plans-grid">
          <div
            v-for="plano in planosDisponiveis"
            :key="plano.slug"
            class="plan-card glass"
            :class="{
              selected: planosSelected === plano.slug,
              featured: plano.destaque,
            }"
            @click="selectPlan(plano.slug)"
          >
            <div v-if="plano.destaque" class="popular-tag">
              <i class="pi pi-star-fill mr-1"></i> MAIS POPULAR
            </div>

            <div class="plan-header">
              <div class="plan-title-group">
                <h3>{{ plano.nome }}</h3>
                <p class="plan-desc">{{ plano.descricao || getPlanDefaultDesc(plano.slug) }}</p>
              </div>
              <div class="plan-check" v-if="planosSelected === plano.slug">
                <i class="pi pi-check"></i>
              </div>
            </div>

            <div class="plan-pricing">
              <template v-if="billingCycle === 'mensal' && plano.preco_mensal">
                <span class="price-val">{{ formatCurrency(plano.preco_mensal) }}</span>
                <span class="price-cycle">/mês</span>
              </template>
              <template v-else-if="billingCycle === 'anual' && plano.preco_anual">
                <span class="price-val">{{ formatCurrency(plano.preco_anual / 12) }}</span>
                <span class="price-cycle">/mês</span>
                <div class="annual-total">Faturado {{ formatCurrency(plano.preco_anual) }}/ano</div>
              </template>
              <template v-else>
                <span class="price-val free">Grátis</span>
                <span class="price-cycle">/sempre</span>
              </template>
            </div>

            <ul class="plan-features">
              <li>
                <i class="pi pi-check-circle check-icon"></i>
                <span>
                  <strong>{{ plano.max_propostas_mes ? `${plano.max_propostas_mes} propostas & orçamentos` : 'Propostas & Orçamentos Ilimitados' }}</strong> /mês
                </span>
              </li>
              <li>
                <i class="pi pi-check-circle check-icon"></i>
                <span>
                  <strong>{{ plano.max_usuarios ? `${plano.max_usuarios} ${plano.max_usuarios === 1 ? 'usuário' : 'usuários'}` : 'Usuários Ilimitados' }}</strong>
                </span>
              </li>
              <li>
                <i class="pi pi-check-circle check-icon"></i>
                <span><strong>{{ plano.ai_credits_limit || 20 }} créditos</strong> de IA/dia</span>
              </li>
              <li>
                <i class="pi" :class="plano.permite_dominio_proprio ? 'pi-check-circle check-icon' : 'pi-times-circle times-icon'"></i>
                <span :class="{ 'disabled-feature': !plano.permite_dominio_proprio }">Domínio personalizado</span>
              </li>
            </ul>

            <button
              type="button"
              class="select-plan-btn"
              :class="{ active: planosSelected === plano.slug }"
            >
              {{ planosSelected === plano.slug ? '✓ Plano Selecionado' : 'Selecionar Plano' }}
            </button>
          </div>
        </div>

        <p class="plan-instant-note">
          <i class="pi pi-bolt mr-1 text-primary"></i>
          O plano selecionado entra em vigor imediatamente após a conclusão do setup.
        </p>
      </div>

      <!-- ========================================== -->
      <!-- STEP 3: DOMÍNIO & LINKS                   -->
      <!-- ========================================== -->
      <div v-if="step === 3" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge domain"><i class="pi pi-globe"></i></div>
          <h1 class="step-title">Domínio e Links Públicos</h1>
          <p class="step-subtitle">Escolha o endereço onde seus clientes acessarão e assinarão suas propostas online.</p>
        </div>

        <div class="domain-cards-grid">
          <!-- Subdomínio Gratuito -->
          <div class="domain-card glass">
            <div class="card-icon-title">
              <i class="pi pi-link text-primary"></i>
              <div>
                <h3>Subdomínio do Painel</h3>
                <p>Link oficial rápido e seguro incluso em todos os planos.</p>
              </div>
            </div>

            <div class="subdomain-input-group">
              <div class="input-with-suffix">
                <input
                  type="text"
                  v-model="form.subdominio"
                  placeholder="sua-empresa"
                  class="subdomain-input"
                  @input="sanitizeSubdomain"
                />
                <span class="suffix-label">.{{ ROOT_DOMAIN }}</span>
              </div>
            </div>

            <div class="url-preview-box">
              <span class="url-label">Prévia do link do cliente:</span>
              <code class="url-code">https://{{ form.subdominio || 'sua-empresa' }}.{{ ROOT_DOMAIN }}/p/PROP-001</code>
            </div>
          </div>

          <!-- Domínio Personalizado -->
          <div class="domain-card glass" :class="{ 'disabled-tier': !permiteDominioProprio }">
            <div class="card-icon-title">
              <i class="pi pi-shield text-warning"></i>
              <div>
                <div class="title-with-badge">
                  <h3>Domínio Próprio (CNAME)</h3>
                  <span v-if="!permiteDominioProprio" class="tier-lock-badge">Requer Plano Pro</span>
                </div>
                <p>Use seu próprio endereço (ex: <code>propostas.suaempresa.com.br</code>).</p>
              </div>
            </div>

            <div class="custom-domain-group">
              <div class="domain-input-row">
                <InputText
                  v-model="form.dominio_personalizado"
                  placeholder="propostas.suaempresa.com.br"
                  :disabled="!permiteDominioProprio"
                  class="flex-1"
                />
                <Button
                  label="Verificar DNS"
                  icon="pi pi-check-circle"
                  severity="secondary"
                  :disabled="!permiteDominioProprio || !form.dominio_personalizado"
                  @click="handleVerifyDomain"
                />
              </div>
              <small class="domain-helper">Insira apenas o domínio sem "https://" ou "www/".</small>
            </div>

            <div class="dns-instruction-box" v-if="permiteDominioProprio">
              <strong>Como configurar no seu DNS:</strong>
              <p>Crie uma entrada <code>CNAME</code> apontando seu subdomínio para <code>cname.{{ ROOT_DOMAIN }}</code>.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- STEP 4: WHATSAPP                          -->
      <!-- ========================================== -->
      <div v-if="step === 4" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge whatsapp"><i class="pi pi-whatsapp"></i></div>
          <h1 class="step-title">Conexão com WhatsApp</h1>
          <p class="step-subtitle">Envie orçamentos e propostas instantâneas diretamente no WhatsApp dos seus clientes.</p>
        </div>

        <div class="whatsapp-card glass">
          <WhatsAppConnect />
        </div>
      </div>

      <!-- ========================================== -->
      <!-- STEP 5: E-MAIL (SMTP)                     -->
      <!-- ========================================== -->
      <div v-if="step === 5" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge email"><i class="pi pi-envelope"></i></div>
          <h1 class="step-title">Configurar Servidor de E-mail</h1>
          <p class="step-subtitle">Configure o envio de notificações e propostas usando o seu próprio provedor de e-mail (SMTP).</p>
        </div>

        <div class="step-card glass">
          <!-- Preset Providers -->
          <div class="preset-providers">
            <span class="preset-title">Preenchimento rápido:</span>
            <div class="preset-buttons">
              <button type="button" class="preset-btn" @click="applySmtpPreset('gmail')">
                <i class="pi pi-google mr-1"></i> Gmail / Google Workspace
              </button>
              <button type="button" class="preset-btn" @click="applySmtpPreset('outlook')">
                <i class="pi pi-microsoft mr-1"></i> Outlook / Office 365
              </button>
              <button type="button" class="preset-btn" @click="applySmtpPreset('hostinger')">
                <i class="pi pi-server mr-1"></i> Hostinger
              </button>
            </div>
          </div>

          <div class="form-grid">
            <div class="form-row">
              <div class="field flex-2">
                <label for="smtp-host">Host do Servidor SMTP</label>
                <InputText id="smtp-host" v-model="form.smtp_host" placeholder="smtp.gmail.com" />
              </div>

              <div class="field flex-1">
                <label for="smtp-port">Porta de Conexão</label>
                <select id="smtp-port" v-model="form.smtp_port" class="custom-select">
                  <option :value="null">Selecione...</option>
                  <option :value="587">587 (TLS / STARTTLS - Recomendado)</option>
                  <option :value="465">465 (SSL)</option>
                  <option :value="25">25 (Sem criptografia)</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="field flex-1">
                <label for="smtp-user">Usuário / E-mail de Envio</label>
                <InputText id="smtp-user" v-model="form.smtp_user" placeholder="comercial@empresa.com.br" />
              </div>

              <div class="field flex-1">
                <label for="smtp-pass">Senha ou Senha de App</label>
                <InputText id="smtp-pass" type="password" v-model="form.smtp_password" placeholder="••••••••" />
              </div>
            </div>

            <!-- Test Connection Button -->
            <div class="smtp-test-section">
              <Button
                label="Testar Conexão SMTP"
                icon="pi pi-send"
                severity="secondary"
                outlined
                @click="handleTestSmtp"
                :loading="testingSmtp"
                :disabled="!form.smtp_host || !form.smtp_user"
              />

              <div v-if="smtpTestOk" class="smtp-result ok">
                <i class="pi pi-check-circle"></i>
                <span>E-mail de teste enviado e validado com sucesso!</span>
              </div>
              <div v-if="smtpTestError" class="smtp-result error">
                <i class="pi pi-times-circle"></i>
                <span>{{ smtpTestError }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- STEP 6: REVISÃO & CONCLUSÃO               -->
      <!-- ========================================== -->
      <div v-if="step === 6" class="step-content">
        <div class="step-heading text-center">
          <div class="step-icon-badge check"><i class="pi pi-check-circle"></i></div>
          <h1 class="step-title">Tudo Pronto para Decolar! 🚀</h1>
          <p class="step-subtitle">Confira o resumo das suas configurações antes de acessar seu painel.</p>
        </div>

        <div class="review-card glass">
          <div class="review-grid">
            <!-- Empresa -->
            <div class="review-box">
              <div class="review-icon"><i class="pi pi-building"></i></div>
              <div class="review-details">
                <span class="review-label">Empresa</span>
                <strong>{{ form.empresa || 'Não preenchido' }}</strong>
                <small class="review-sub">{{ form.telefone || 'Sem telefone' }} • {{ form.setor }}</small>
              </div>
              <button class="edit-step-btn" @click="goToStep(1)">Editar</button>
            </div>

            <!-- Plano -->
            <div class="review-box">
              <div class="review-icon"><i class="pi pi-sparkles"></i></div>
              <div class="review-details">
                <span class="review-label">Plano Selecionado</span>
                <strong>Plano {{ getSelectedPlanName() }}</strong>
                <small class="review-sub">Faturamento {{ billingCycle === 'mensal' ? 'Mensal' : 'Anual' }}</small>
              </div>
              <button class="edit-step-btn" @click="goToStep(2)">Editar</button>
            </div>

            <!-- Domínio -->
            <div class="review-box">
              <div class="review-icon"><i class="pi pi-globe"></i></div>
              <div class="review-details">
                <span class="review-label">Endereço de Propostas</span>
                <strong>{{ form.subdominio || 'sua-empresa' }}.{{ ROOT_DOMAIN }}</strong>
                <small class="review-sub" v-if="form.dominio_personalizado">Personalizado: {{ form.dominio_personalizado }}</small>
              </div>
              <button class="edit-step-btn" @click="goToStep(3)">Editar</button>
            </div>

            <!-- WhatsApp & Email -->
            <div class="review-box">
              <div class="review-icon"><i class="pi pi-send"></i></div>
              <div class="review-details">
                <span class="review-label">Canais de Envio</span>
                <strong>WhatsApp & E-mail</strong>
                <small class="review-sub">{{ form.smtp_host ? 'SMTP Configurado' : 'SMTP Opcional Pendente' }}</small>
              </div>
              <button class="edit-step-btn" @click="goToStep(5)">Editar</button>
            </div>
          </div>

          <div class="finish-callout">
            <div class="callout-icon"><i class="pi pi-star"></i></div>
            <div class="callout-text">
              <h4>Seu ambiente está configurado e pronto para gerar vendas</h4>
              <p>Você pode alterar qualquer uma dessas opções mais tarde no menu de Configurações da Empresa.</p>
            </div>
          </div>

          <Button
            label="Concluir e Acessar Meu Painel"
            icon="pi pi-rocket"
            class="finish-huge-btn"
            @click="finishSetup"
            :loading="loading"
          />
        </div>
      </div>
    </main>

    <!-- Navigation Footer -->
    <footer class="setup-footer glass">
      <div class="footer-inner">
        <button
          class="nav-btn prev"
          :disabled="step === 1"
          @click="prevStep"
        >
          <i class="pi pi-arrow-left"></i>
          <span>Voltar</span>
        </button>

        <div class="footer-dots">
          <span
            v-for="s in steps"
            :key="'dot-' + s.id"
            class="footer-dot"
            :class="{ active: step === s.id, completed: step > s.id }"
            @click="goToStep(s.id)"
            :title="s.label"
          ></span>
        </div>

        <button
          class="nav-btn next"
          @click="handleNextOrFinish"
          :disabled="savingStep"
        >
          <span>{{ step < steps.length ? 'Continuar' : 'Concluir' }}</span>
          <i v-if="savingStep" class="pi pi-spin pi-spinner"></i>
          <i v-else-if="step < steps.length" class="pi pi-arrow-right"></i>
          <i v-else class="pi pi-check"></i>
        </button>
      </div>
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
const savingStep = ref(false)
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
  { id: 1, label: 'Marca', icon: 'pi pi-palette' },
  { id: 2, label: 'Plano', icon: 'pi pi-sparkles' },
  { id: 3, label: 'Domínio', icon: 'pi pi-globe' },
  { id: 4, label: 'WhatsApp', icon: 'pi pi-whatsapp' },
  { id: 5, label: 'E-mail', icon: 'pi pi-envelope' },
  { id: 6, label: 'Revisão', icon: 'pi pi-check-circle' },
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
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
})

const planosDisponiveis = ref([])
const planosSelected = ref('gratuito')
const planoAtual = ref(null)

const predefinedColors = [
  '#6366f1',
  '#3b82f6',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#f97316',
  '#ef4444',
  '#ec4899',
  '#8b5cf6',
]

const permiteDominioProprio = computed(() => {
  return ['pro', 'empresarial'].includes(planosSelected.value.toLowerCase())
})

function formatCurrency(val) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0)
}

function getPlanDefaultDesc(slug) {
  const map = {
    gratuito: 'Para autônomos iniciando com propostas online',
    inicial: 'Capacidade expandida para pequenas equipes',
    pro: 'Domínio próprio e alta conversão com IA',
    empresarial: 'Máxima escala sem limites de propostas e equipe',
  }
  return map[slug] || ''
}

function getSelectedPlanName() {
  const p = planosDisponiveis.value.find((pl) => pl.slug === planosSelected.value)
  return p?.nome || (planosSelected.value ? planosSelected.value.toUpperCase() : 'Gratuito')
}

function sanitizeSubdomain() {
  form.subdominio = form.subdominio
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '')
    .replace(/--+/g, '-')
}

function selectPlan(slug) {
  planosSelected.value = slug
}

function applySmtpPreset(preset) {
  if (preset === 'gmail') {
    form.smtp_host = 'smtp.gmail.com'
    form.smtp_port = 587
  } else if (preset === 'outlook') {
    form.smtp_host = 'smtp.office365.com'
    form.smtp_port = 587
  } else if (preset === 'hostinger') {
    form.smtp_host = 'smtp.hostinger.com'
    form.smtp_port = 465
  }
}

async function handleLogoUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    error.value = 'O arquivo de logo deve ter no máximo 2 MB.'
    return
  }
  uploadingLogo.value = true
  error.value = ''
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
    error.value = 'Erro ao fazer upload do logotipo.'
  } finally {
    uploadingLogo.value = false
  }
}

async function handleVerifyDomain() {
  try {
    await api.post('/api/empresas/me/dominio/verificar')
    alert('Verificação de domínio solicitada com sucesso!')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao solicitar verificação de domínio.'
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
    smtpTestError.value = e.response?.data?.detail || 'Falha ao testar conexão SMTP.'
  } finally {
    testingSmtp.value = false
  }
}

async function saveCurrentStep() {
  try {
    if (step.value === 1) {
      if (form.empresa && form.empresa.trim()) {
        await api.put('/api/empresas/me', {
          razao_social: form.empresa.trim(),
          nome_fantasia: form.empresa.trim(),
          telefone: form.telefone || null,
          pais: form.pais,
          fuso_horario: form.fuso,
          moeda: form.moeda,
          idioma: form.idioma,
          setor: form.setor,
          cor_marca: form.cor_marca,
        })
      }
    } else if (step.value === 2) {
      if (planosSelected.value) {
        await api.post('/api/planos/me/solicitar', { slug: planosSelected.value })
      }
    } else if (step.value === 3) {
      if (form.subdominio || form.dominio_personalizado) {
        await api.put('/api/empresas/me/dominio', {
          subdominio: form.subdominio || null,
          dominio_personalizado: form.dominio_personalizado || null,
        })
      }
    } else if (step.value === 5) {
      if (form.smtp_host) {
        await api.put('/api/empresas/me', {
          smtp_host: form.smtp_host,
          smtp_port: form.smtp_port,
          smtp_user: form.smtp_user,
          smtp_password: form.smtp_password || null,
        })
      }
    }
  } catch (e) {
    console.warn('Aviso ao auto-salvar etapa:', e)
  }
}

async function goToStep(targetStepId) {
  if (targetStepId === step.value) return
  savingStep.value = true
  await saveCurrentStep()
  savingStep.value = false
  step.value = targetStepId
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handleNextOrFinish() {
  if (step.value < steps.length) {
    savingStep.value = true
    await saveCurrentStep()
    savingStep.value = false
    step.value++
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    finishSetup()
  }
}

function prevStep() {
  if (step.value > 1) {
    step.value--
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

async function finishSetup() {
  loading.value = true
  error.value = ''
  try {
    await saveCurrentStep()
    await api.post('/api/empresas/me/setup-concluir')
    if (authStore.fetchUser) await authStore.fetchUser()
    if (authStore.checkSetupStatus) await authStore.checkSetupStatus()
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao concluir setup.'
  } finally {
    loading.value = false
  }
}

function skipToDashboard() {
  router.push('/')
}

onMounted(async () => {
  try {
    const { data: plans } = await api.get('/api/planos')
    planosDisponiveis.value = plans

    const { data: emp } = await api.get('/api/empresas/me')
    if (emp.razao_social && !emp.razao_social.startsWith('Empresa de ')) {
      form.empresa = emp.razao_social
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
    form.smtp_port = emp.smtp_port || 587
    form.smtp_user = emp.smtp_user || ''
    planosSelected.value = emp.plano || 'gratuito'
    if (emp.logo_url) logoPreview.value = emp.logo_url

    const { data: pData } = await api.get('/api/planos/me/atual')
    planoAtual.value = pData?.detalhes
  } catch (e) {
    console.error('Erro ao carregar dados iniciais do setup:', e)
  }
})
</script>

<style scoped>
.setup-page {
  min-height: 100vh;
  background-color: var(--bg-app);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
}

/* Header */
.setup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 2.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.logo h2 {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.setup-badge {
  font-size: 0.72rem;
  font-weight: 600;
  background: rgba(var(--primary-rgb), 0.12);
  color: var(--primary-400);
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  border: 1px solid rgba(var(--primary-rgb), 0.25);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.progress-pill {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-card-hover);
  padding: 0.35rem 0.85rem;
  border-radius: 20px;
  border: 1px solid var(--border-color);
}

.skip-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all var(--transition-fast);
}

.skip-btn:hover {
  color: var(--text-primary);
  transform: translateX(2px);
}

/* Stepper Track */
.stepper-container {
  padding: 1.5rem 1rem;
  display: flex;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.15);
}

.stepper-track {
  display: flex;
  align-items: center;
  max-width: 960px;
  width: 100%;
  justify-content: space-between;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  padding: 0.5rem 0.85rem;
  border-radius: var(--border-radius-md);
  transition: all var(--transition-fast);
  user-select: none;
}

.step-item:hover {
  background: var(--bg-card-hover);
  transform: translateY(-1px);
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.step-item.active .step-circle {
  background: var(--primary-500);
  border-color: var(--primary-400);
  color: white;
  box-shadow: var(--shadow-glow-primary);
  transform: scale(1.08);
}

.step-item.completed .step-circle {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.step-text {
  display: flex;
  flex-direction: column;
}

.step-number {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.step-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.step-item.active .step-label {
  color: var(--text-primary);
  font-weight: 700;
}

.step-item.completed .step-label {
  color: var(--text-primary);
}

.step-line {
  flex: 1;
  height: 2px;
  background: var(--border-color);
  margin: 0 0.5rem;
  min-width: 20px;
  transition: background 0.3s ease;
}

.step-line.completed {
  background: #10b981;
}

/* Step Content Container */
.step-content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2.5rem 1.5rem 4rem;
  overflow-y: auto;
}

.step-content {
  width: 100%;
  max-width: 820px;
}

.step-heading {
  margin-bottom: 2rem;
}

.step-icon-badge {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  margin-bottom: 1rem;
}

.step-icon-badge.brand { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
.step-icon-badge.plan { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.step-icon-badge.domain { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.step-icon-badge.whatsapp { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.step-icon-badge.email { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.step-icon-badge.check { background: rgba(16, 185, 129, 0.15); color: #10b981; }

.step-title {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.4rem;
  letter-spacing: -0.02em;
}

.step-subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
  margin: 0;
}

.step-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 2rem;
  box-shadow: var(--glass-shadow);
}

.text-center {
  text-align: center;
}

.setup-error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 0.85rem 1.25rem;
  border-radius: var(--border-radius-md);
  margin-bottom: 1.5rem;
  width: 100%;
  max-width: 820px;
  display: flex;
  align-items: center;
}

/* Brand Preview Box */
.brand-preview-box {
  background: var(--bg-app);
  border: 2px solid;
  border-radius: var(--border-radius-md);
  padding: 1rem 1.5rem;
  margin-bottom: 1.75rem;
  position: relative;
  transition: border-color 0.3s ease;
}

.preview-badge {
  position: absolute;
  top: -12px;
  left: 1.25rem;
  font-size: 0.68rem;
  font-weight: 700;
  color: white;
  padding: 0.15rem 0.6rem;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.preview-logo-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
}

.preview-name {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 0.2rem;
}

.preview-contact {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0;
}

/* Form Styles */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: flex;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field.flex-1 { flex: 1; }
.field.flex-2 { flex: 2; }

.field label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.required {
  color: #ef4444;
}

.field :deep(.p-inputtext),
.custom-select {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.65rem 0.9rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.85rem;
  outline: none;
  transition: border-color var(--transition-fast);
}

.field :deep(.p-inputtext:focus),
.custom-select:focus {
  border-color: var(--primary-400);
}

.char-count {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-align: right;
}

/* Upload Area */
.upload-area {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.upload-circle {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: 2px dashed var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: var(--bg-app);
  overflow: hidden;
  transition: border-color var(--transition-fast);
}

.upload-circle:hover {
  border-color: var(--primary-400);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.65rem;
  color: var(--text-muted);
}

.upload-placeholder i {
  font-size: 1.1rem;
}

.logo-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-upload-trigger {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.4rem 0.8rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}

.upload-help {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 0.3rem 0 0;
}

/* Color Picker */
.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.color-options {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.color-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.2s ease;
}

.color-circle:hover {
  transform: scale(1.15);
}

.color-circle.selected {
  border-color: white;
  outline: 2px solid var(--primary-400);
  transform: scale(1.15);
}

.custom-color-inline {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  padding: 0.2rem 0.6rem;
  border-radius: var(--border-radius-sm);
}

.color-native-picker {
  width: 24px;
  height: 24px;
  border: none;
  padding: 0;
  background: none;
  cursor: pointer;
}

.color-hex-code {
  font-family: monospace;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

/* STEP 2: Plans */
.billing-toggle-container {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.toggle-pill {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 30px;
  padding: 4px;
}

.toggle-pill button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.45rem 1.25rem;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all var(--transition-fast);
}

.toggle-pill button.active {
  background: var(--primary-500);
  color: white;
}

.discount-badge {
  background: #10b981;
  color: white;
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-weight: 800;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.plan-card {
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all var(--transition-fast);
  background: var(--bg-card);
}

.plan-card:hover {
  border-color: var(--primary-400);
  transform: translateY(-2px);
}

.plan-card.selected {
  border-color: var(--primary-500);
  background: rgba(var(--primary-rgb), 0.08);
  box-shadow: var(--shadow-glow-primary);
}

.plan-card.featured {
  border-color: rgba(var(--primary-rgb), 0.6);
}

.popular-tag {
  position: absolute;
  top: -12px;
  right: 1.5rem;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.plan-title-group h3 {
  font-size: 1.2rem;
  font-weight: 800;
  margin: 0 0 0.2rem;
}

.plan-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

.plan-check {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--primary-500);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.plan-pricing {
  margin-bottom: 1.25rem;
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.price-val {
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--text-primary);
}

.price-val.free {
  color: #10b981;
}

.price-cycle {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.annual-total {
  width: 100%;
  font-size: 0.72rem;
  color: #10b981;
  font-weight: 600;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  flex: 1;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.check-icon {
  color: #10b981;
  font-size: 0.85rem;
}

.times-icon {
  color: var(--text-muted);
  opacity: 0.5;
  font-size: 0.85rem;
}

.disabled-feature {
  color: var(--text-muted);
  text-decoration: line-through;
  opacity: 0.6;
}

.select-plan-btn {
  width: 100%;
  padding: 0.6rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid var(--border-color);
  background: var(--bg-app);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.select-plan-btn.active {
  background: var(--primary-500);
  border-color: var(--primary-500);
  color: white;
}

.plan-instant-note {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: center;
}

/* STEP 3: Domain Cards */
.domain-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.domain-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card-icon-title {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.card-icon-title i {
  font-size: 1.4rem;
  margin-top: 0.2rem;
}

.card-icon-title h3 {
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0 0 0.2rem;
}

.card-icon-title p {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0;
}

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.tier-lock-badge {
  font-size: 0.65rem;
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-weight: 700;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.input-with-suffix {
  display: flex;
  align-items: center;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
}

.subdomain-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 0.65rem 0.9rem;
  font-size: 0.9rem;
  outline: none;
}

.suffix-label {
  background: var(--bg-card-hover);
  padding: 0.65rem 0.9rem;
  color: var(--text-muted);
  font-size: 0.85rem;
  border-left: 1px solid var(--border-color);
}

.url-preview-box {
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--border-radius-sm);
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.url-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
}

.url-code {
  font-family: monospace;
  font-size: 0.85rem;
  color: var(--primary-400);
}

.domain-input-row {
  display: flex;
  gap: 0.75rem;
}

.domain-helper {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 0.3rem;
  display: block;
}

.dns-instruction-box {
  background: rgba(var(--primary-rgb), 0.08);
  border: 1px solid rgba(var(--primary-rgb), 0.2);
  border-radius: var(--border-radius-sm);
  padding: 0.75rem 1rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.dns-instruction-box code {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  color: var(--primary-300);
}

/* STEP 4: WhatsApp */
.whatsapp-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 2rem;
}

/* STEP 5: SMTP */
.preset-providers {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.preset-title {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 600;
}

.preset-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.preset-btn {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.preset-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--primary-400);
}

.smtp-test-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.smtp-result {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.smtp-result.ok { color: #10b981; }
.smtp-result.error { color: #ef4444; }

/* STEP 6: Review Card */
.review-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.review-box {
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  position: relative;
}

.review-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(var(--primary-rgb), 0.1);
  color: var(--primary-400);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.review-details {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  flex: 1;
  min-width: 0;
}

.review-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
}

.review-details strong {
  font-size: 0.9rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.review-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.edit-step-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.25rem 0.55rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.edit-step-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--primary-400);
}

.finish-callout {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: var(--border-radius-md);
  padding: 1rem 1.25rem;
}

.callout-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #10b981;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.callout-text h4 {
  margin: 0 0 0.2rem;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
}

.callout-text p {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.finish-huge-btn {
  width: 100%;
  padding: 0.9rem;
  font-size: 1rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600)) !important;
  box-shadow: var(--shadow-glow-primary);
}

/* Footer Navigation */
.setup-footer {
  position: sticky;
  bottom: 0;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  padding: 1rem 2.5rem;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 10;
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.3rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-btn.prev {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.nav-btn.prev:hover:not(:disabled) {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.nav-btn.next {
  background: var(--primary-500);
  border: 1px solid var(--primary-500);
  color: white;
  box-shadow: var(--shadow-glow-primary);
}

.nav-btn.next:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.footer-dots {
  display: flex;
  gap: 0.5rem;
}

.footer-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.footer-dot.active {
  background: var(--primary-500);
  transform: scale(1.3);
  box-shadow: var(--shadow-glow-primary);
}

.footer-dot.completed {
  background: #10b981;
}

@media (max-width: 768px) {
  .setup-header {
    padding: 1rem;
    flex-direction: column;
    gap: 0.5rem;
  }
  .stepper-container {
    overflow-x: auto;
    justify-content: flex-start;
  }
  .stepper-track {
    min-width: 600px;
  }
  .form-row {
    flex-direction: column;
  }
  .review-grid {
    grid-template-columns: 1fr;
  }
  .setup-footer {
    padding: 1rem;
  }
}
</style>
