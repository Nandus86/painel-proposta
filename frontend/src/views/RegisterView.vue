<template>
  <div class="register-page">
    <div class="split-layout">
      <!-- Painel Esquerdo (Testimonial/Branding) -->
      <div class="left-pane">
        <div class="logo">
          <h2>Dekto</h2>
        </div>
        <div class="testimonial">
          <p>
            "Renovações e novos seguros ficavam parados no CRM sem proposta formal. Com um clique levámos tudo para Dekto, gerámos cotações interativas em lote—a taxa de aceitação subiu tanto que a equipa ainda comenta nos corredores."
          </p>
          <span class="author">— Marina S., Diretora comercial, seguros</span>
        </div>
      </div>

      <!-- Painel Direito (Formulário) -->
      <div class="right-pane">
        <div class="top-actions">
          <button class="theme-toggle" @click="toggleTheme">
            <i class="pi pi-moon"></i>
          </button>
          <div class="lang-selector">
            <span>🇵🇹 Português</span>
          </div>
        </div>

        <div class="register-form-container fade-in">
          <h1 class="register-title">Criar uma conta</h1>
          <p class="register-subtitle">Comece grátis, sem cartão de crédito</p>

          <form @submit.prevent="handleRegister" class="register-form">
            <div class="field-row">
              <div class="field">
                <label>Nome da empresa</label>
                <InputText v-model="form.empresa" placeholder="Exemplo Lda." required />
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
                <small class="help-text">Mín. 8 caracteres, 1 maiúscula e 1 número</small>
              </div>
            </div>

            <div class="checkbox-group">
              <div class="checkbox-item">
                <Checkbox v-model="form.termos" inputId="termos" :binary="true" />
                <label for="termos">
                  Concordo com os <a href="#">Termos de Serviço</a>, <a href="#">Política de Privacidade</a> e <a href="#">Acordo de Processamento de Dados</a>
                </label>
              </div>
              <div class="checkbox-item">
                <Checkbox v-model="form.marketing" inputId="marketing" :binary="true" />
                <label for="marketing">
                  Dicas de utilização e e-mails de marketing apenas da Dekto (opcional)
                </label>
              </div>
            </div>

            <transition name="shake">
              <div v-if="error" class="error-message">
                <i class="pi pi-exclamation-circle"></i>
                {{ error }}
              </div>
            </transition>

            <Button type="submit" label="Cadastrar-se" class="register-btn" :loading="loading" />
            
            <div class="divider">
              <span>OU</span>
            </div>

            <Button type="button" label="Cadastrar-se com Google" class="google-btn" outlined>
              <template #icon>
                <i class="pi pi-google" style="color: #ea4335"></i>
              </template>
            </Button>
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
  marketing: false
})

function toggleTheme() {
  // Lógica de toggle theme no futuro
}

async function handleRegister() {
  if (!form.termos) {
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
    await authStore.register(form.nome, form.email, form.senha)
    
    // Após cadastro e login, redirecionar para o quiz de configuração
    router.push('/setup')
  } catch (e) {
    error.value = e || 'Erro ao registrar. Tente novamente.'
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

.lang-selector {
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
  margin: 0.5rem 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color);
}

.divider span {
  padding: 0 1rem;
}

.google-btn {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  padding: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  width: 100%;
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.google-btn:hover {
  background-color: var(--bg-card-hover) !important;
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
</style>
