<template>
  <div class="login-page">
    <!-- Background animation -->
    <div class="bg-animation">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <div class="login-container fade-in">
      <div class="login-card glass">
        <!-- Logo -->
        <div class="login-header">
          <div class="logo-icon">
            <i class="pi pi-file-edit"></i>
          </div>
          <h1 class="login-title">Dekto</h1>
          <p class="login-subtitle">Sistema de Propostas — Acesse sua conta</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="field">
            <label for="email">Email</label>
            <div class="input-wrapper">
              <i class="pi pi-envelope"></i>
              <InputText
                id="email"
                v-model="email"
                placeholder="seu@email.com"
                type="email"
                required
                class="w-full"
              />
            </div>
          </div>

          <div class="field">
            <label for="senha">Senha</label>
            <div class="input-wrapper">
              <i class="pi pi-lock"></i>
              <InputText
                id="senha"
                v-model="senha"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                required
                class="w-full"
              />
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
              >
                <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
              </button>
            </div>
          </div>

          <transition name="shake">
            <div v-if="error" class="error-message">
              <i class="pi pi-exclamation-circle"></i>
              {{ error }}
            </div>
          </transition>

          <Button
            type="submit"
            label="Entrar"
            icon="pi pi-sign-in"
            :loading="authStore.loading"
            class="login-btn"
          />
        </form>
      </div>

      <p class="login-footer">
        Não tem uma conta? <router-link to="/register" class="register-link">Criar conta</router-link>
      </p>
      <p class="login-copyright">
        © 2026 Dekto • Todos os direitos reservados
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const senha = ref('')
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
  error.value = ''
  try {
    await authStore.login(email.value, senha.value)
    if (authStore.isSuperuser) {
      router.push('/admin/empresas')
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = typeof e === 'string' ? e : 'Erro ao fazer login. Tente novamente.'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

/* Background orbs */
.bg-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  animation: float 20s infinite ease-in-out;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: rgba(var(--primary-rgb), 0.12);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 350px;
  height: 350px;
  background: rgba(var(--accent-rgb), 0.08);
  bottom: -100px;
  right: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: rgba(var(--primary-rgb), 0.05);
  top: 50%;
  left: 50%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -40px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(40px, 30px) scale(1.02); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
}

.login-card {
  padding: 2.5rem;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  box-shadow: var(--shadow-glow-primary);
}

.logo-icon i {
  font-size: 1.5rem;
  color: white;
}

.login-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.login-title span {
  font-weight: 400;
  color: var(--text-secondary);
}

.login-subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper > i {
  position: absolute;
  left: 0.85rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  z-index: 1;
}

.input-wrapper :deep(.p-inputtext) {
  padding-left: 2.5rem !important;
  width: 100%;
  height: 44px;
}

.w-full {
  width: 100%;
}

.toggle-password {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  z-index: 1;
}

.toggle-password:hover {
  color: var(--text-secondary);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.2);
  border-radius: var(--border-radius-sm);
  color: var(--danger-400);
  font-size: 0.85rem;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-weight: 600 !important;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700)) !important;
  border: none !important;
  box-shadow: var(--shadow-glow-primary);
  margin-top: 0.5rem;
}

.login-btn:hover {
  background: linear-gradient(135deg, var(--primary-400), var(--primary-600)) !important;
}

.login-footer {
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-top: 1.5rem;
}

.register-link {
  color: var(--primary-500) !important;
  font-weight: 600;
  text-decoration: none;
}
.register-link:hover {
  color: var(--primary-400) !important;
  text-decoration: underline;
}

.login-copyright {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.75rem;
}

/* Shake animation for errors */
.shake-enter-active {
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  50% { transform: translateX(8px); }
  75% { transform: translateX(-4px); }
}
</style>
