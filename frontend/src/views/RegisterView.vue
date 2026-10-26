<template>
  <div class="register-page">
    <div class="split-layout">
      <!-- Painel Esquerdo (Testimonial/Branding) -->
      <div class="left-pane">
        <div class="logo">
          <h2>{{ APP_NAME }}</h2>
        </div>
        <div class="testimonial">
          <p>Propostas profissionais em minutos, com a sua marca.</p>
          <ul class="benefits">
            <li><i class="pi pi-sparkles"></i> Texto da proposta gerado por IA a partir dos seus modelos</li>
            <li><i class="pi pi-link"></i> Link para o cliente visualizar e aceitar online</li>
            <li><i class="pi pi-bell"></i> Aviso quando o cliente abre ou aceita</li>
            <li><i class="pi pi-file-pdf"></i> PDF pronto para enviar por e-mail ou WhatsApp</li>
          </ul>
        </div>
      </div>

      <!-- Painel Direito (Formulário) -->
      <div class="right-pane">
        <div class="top-actions">
          <button type="button" class="theme-toggle" :aria-label="isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'" @click="toggleTheme">
            <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'"></i>
          </button>
        </div>

        <div class="register-form-container fade-in">
          <h1 class="register-title">Criar uma conta</h1>
          <p class="register-subtitle">Comece grátis, sem cartão de crédito</p>

          <form @submit.prevent="handleRegister" class="register-form">
            <div class="field-row">
              <div class="field">
                <label>Nome da empresa</label>
                <InputText v-model="form.empresa" placeholder="Sua Empresa Ltda." required />
              </div>
              <div class="field">
                <label>Nome completo</label>
                <InputText v-model="form.nome" placeholder="João Silva" required />
              </div>
            </div>

            <div class="field-row">
              <div class="field">
                <label>E-mail</label>
                <InputText v-model="form.email" type="email" placeholder="email@empresa.com" required />
              </div>
              <div class="field">
                <label>Senha</label>
                <div class="input-wrapper">
                  <InputText 
                    v-model="form.senha" 
                    :type="showPassword ? 'text' : 'password'" 
                    placeholder="••••••••" 
                    required 
                    class="w-full"
                  />
                  <button type="button" class="toggle-password" @click="showPassword = !showPassword">
                    <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
                  </button>
                </div>
                <small class="help-text">Mínimo de 8 caracteres</small>
              </div>
            </div>

            <div class="checkbox-group">
              <div v-if="exigeTermos" class="checkbox-item">
                <Checkbox v-model="form.termos" inputId="termos" :binary="true" />
                <label for="termos">
                  Li e concordo com
                  <template v-if="TERMS_URL">os <a :href="TERMS_URL" target="_blank" rel="noopener">Termos de Uso</a></template>
                  <template v-if="TERMS_URL && PRIVACY_URL"> e </template>
                  <template v-if="PRIVACY_URL">a <a :href="PRIVACY_URL" target="_blank" rel="noopener">Política de Privacidade</a></template>
                </label>
              </div>
            </div>

            <transition name="shake">
              <div v-if="error" class="error-message">
                <i class="pi pi-exclamation-circle"></i>
                {{ error }}
              </div>
            </transition>

            <Button type="submit" label="Criar conta" class="register-btn" :loading="loading" />
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import { APP_NAME, PRIVACY_URL, TERMS_URL } from '../config/branding'
import { isDarkMode, toggleDarkTheme } from '../utils/theme'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const form = reactive({
  empresa: '',
  nome: '',
  email: '',
  senha: '',
  termos: false,
})

// O aceite só é exigido quando os documentos legais estão publicados (VITE_TERMS_URL / VITE_PRIVACY_URL)
const exigeTermos = Boolean(TERMS_URL || PRIVACY_URL)
const isDark = ref(isDarkMode())

function toggleTheme() {
  isDark.value = toggleDarkTheme()
}

async function handleRegister() {
  if (exigeTermos && !form.termos) {
    error.value = 'Você deve concordar com os termos para continuar.'
    return
  }
  if (form.senha.length < 8) {
    error.value = 'A senha deve ter no mínimo 8 caracteres.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.register(form.nome, form.email, form.senha, form.empresa)
    
    // Após cadastro e login, redirecionar para o quiz de configuração
    router.push('/setup')
  } catch (e) {
    error.value = typeof e === 'string' ? e : 'Erro ao registrar. Tente novamente.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  background-color: var(--bg-app);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
}

.split-layout {
  display: flex;
  width: 100%;
}

.left-pane {
  flex: 1;
  background-color: var(--bg-card);
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid var(--border-color);
}

.logo h2 {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
}

.testimonial {
  margin-bottom: auto;
  margin-top: auto;
  max-width: 480px;
}

.testimonial p {
  font-size: 1.15rem;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.testimonial .author {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.right-pane {
  flex: 1.5;
  padding: 2rem 4rem;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-app);
}

.top-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1.5rem;
  align-items: center;
  position: absolute;
  top: 2rem;
  right: 3rem;
}

.theme-toggle {
  background: none;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 1.2rem;
}


.register-form-container {
  max-width: 580px;
  margin: auto;
  width: 100%;
}

.register-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.register-subtitle {
  color: var(--text-secondary);
  margin-bottom: 2.5rem;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.field-row {
  display: flex;
  gap: 1.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.field label {
  font-size: 0.85rem;
  font-weight: 600;
}

.field :deep(.p-inputtext) {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  width: 100%;
}

.field :deep(.p-inputtext:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px #6366f1;
}

.input-wrapper {
  position: relative;
  display: flex;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.help-text {
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1rem 0;
  background-color: var(--bg-card);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.checkbox-item label {
  font-size: 0.85rem;
  color: var(--text-primary);
  line-height: 1.4;
  cursor: pointer;
}

.checkbox-item a {
  color: var(--text-primary);
  text-decoration: underline;
}

.checkbox-item :deep(.p-checkbox-box) {
  background-color: transparent;
  border-color: #555;
  width: 20px;
  height: 20px;
}
.checkbox-item :deep(.p-checkbox-box.p-highlight) {
  background-color: #6366f1;
  border-color: #6366f1;
}

.register-btn {
  background-color: #6366f1 !important;
  color: white !important;
  border: none !important;
  padding: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  width: 100%;
}

.register-btn:hover {
  background-color: #4f46e5 !important;
}


.error-message {
  color: #ef4444;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

@media (max-width: 992px) {
  .split-layout {
    flex-direction: column;
  }
  .left-pane {
    padding: 2rem;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }
  .right-pane {
    padding: 2rem;
  }
}

.benefits {
  list-style: none;
  padding: 0;
  margin: 1.5rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  font-size: 0.95rem;
}

.benefits li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.benefits i {
  opacity: 0.85;
}
</style>
