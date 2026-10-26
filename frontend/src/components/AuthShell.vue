<template>
  <div class="login-page">
    <div class="bg-animation">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <div class="login-container fade-in">
      <div class="login-card glass">
        <div class="login-header">
          <div class="logo-icon">
            <i :class="icon"></i>
          </div>
          <h1 class="login-title">{{ title }}</h1>
          <p v-if="subtitle" class="login-subtitle">{{ subtitle }}</p>
        </div>

        <slot />
      </div>

      <slot name="footer" />
      <p class="login-copyright">
        © {{ year }} {{ APP_NAME }} • Todos os direitos reservados
      </p>
    </div>
  </div>
</template>

<script setup>
import { APP_NAME } from '../config/branding'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: 'pi pi-file-edit' },
})

const year = new Date().getFullYear()
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

@media (prefers-reduced-motion: reduce) {
  .orb { animation: none; }
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

@media (max-width: 480px) {
  .login-page { padding: 1rem; }
  .login-card { padding: 1.75rem 1.25rem; }
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

.login-subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.login-copyright {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.75rem;
}
</style>

<!-- Estilos do formulário: valem para o conteúdo passado no slot -->
<style>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.auth-form .field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auth-form .field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.auth-form .label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.auth-form .forgot-link {
  font-size: 0.8rem;
  color: var(--primary-500);
  text-decoration: none;
  font-weight: 500;
}

.auth-form .forgot-link:hover {
  text-decoration: underline;
}

.auth-form .input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.auth-form .input-wrapper > i {
  position: absolute;
  left: 0.85rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  z-index: 1;
}

.auth-form .input-wrapper .p-inputtext {
  padding-left: 2.5rem !important;
  width: 100%;
  height: 44px;
}

.auth-form .toggle-password {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  z-index: 1;
}

.auth-form .toggle-password:hover {
  color: var(--text-secondary);
}

.auth-message {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.85rem;
  line-height: 1.45;
}

.auth-message.error {
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.2);
  color: var(--danger-400);
}

.auth-message.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: var(--success-500, #16a34a);
}

.auth-message i {
  margin-top: 2px;
}

.auth-btn {
  width: 100%;
  height: 44px;
  font-weight: 600 !important;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700)) !important;
  border: none !important;
  box-shadow: var(--shadow-glow-primary);
  margin-top: 0.5rem;
}

.auth-btn:hover {
  background: linear-gradient(135deg, var(--primary-400), var(--primary-600)) !important;
}

.auth-footer {
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-top: 1.5rem;
}

.auth-link {
  color: var(--primary-500) !important;
  font-weight: 600;
  text-decoration: none;
}

.auth-link:hover {
  color: var(--primary-400) !important;
  text-decoration: underline;
}

.shake-enter-active {
  animation: auth-shake 0.4s ease;
}

@keyframes auth-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  50% { transform: translateX(8px); }
  75% { transform: translateX(-4px); }
}
</style>
