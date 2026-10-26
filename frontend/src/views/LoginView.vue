<template>
  <AuthShell :title="APP_NAME" subtitle="Sistema de Propostas — Acesse sua conta">
    <form @submit.prevent="handleLogin" class="auth-form">
      <div class="field">
        <label for="email">Email</label>
        <div class="input-wrapper">
          <i class="pi pi-envelope"></i>
          <InputText
            id="email"
            v-model="email"
            placeholder="seu@email.com"
            type="email"
            autocomplete="username"
            required
          />
        </div>
      </div>

      <div class="field">
        <div class="label-row">
          <label for="senha">Senha</label>
          <router-link to="/esqueci-senha" class="forgot-link">Esqueci minha senha</router-link>
        </div>
        <div class="input-wrapper">
          <i class="pi pi-lock"></i>
          <InputText
            id="senha"
            v-model="senha"
            :type="showPassword ? 'text' : 'password'"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
          <button
            type="button"
            class="toggle-password"
            :aria-label="showPassword ? 'Ocultar senha' : 'Mostrar senha'"
            @click="showPassword = !showPassword"
          >
            <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
          </button>
        </div>
      </div>

      <transition name="shake">
        <div v-if="error" class="auth-message error" role="alert">
          <i class="pi pi-exclamation-circle"></i>
          <span>{{ error }}</span>
        </div>
      </transition>

      <Button
        type="submit"
        label="Entrar"
        icon="pi pi-sign-in"
        :loading="authStore.loading"
        class="auth-btn"
      />
    </form>

    <template #footer>
      <p class="auth-footer">
        Não tem uma conta? <router-link to="/register" class="auth-link">Criar conta</router-link>
      </p>
    </template>
  </AuthShell>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import AuthShell from '../components/AuthShell.vue'
import { APP_NAME } from '../config/branding'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref(typeof route.query.email === 'string' ? route.query.email : '')
const senha = ref('')
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
  error.value = ''
  try {
    await authStore.login(email.value, senha.value)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : null
    if (redirect && !redirect.startsWith('//')) {
      router.push(redirect)
    } else if (authStore.isSuperuser) {
      router.push('/admin/empresas')
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = typeof e === 'string' ? e : 'Erro ao fazer login. Tente novamente.'
  }
}
</script>
