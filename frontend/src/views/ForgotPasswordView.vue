<template>
  <AuthShell
    title="Esqueceu a senha?"
    subtitle="Informe seu e-mail e enviaremos um link para criar uma nova senha."
    icon="pi pi-key"
  >
    <form v-if="!sent" @submit.prevent="handleSubmit" class="auth-form">
      <div class="field">
        <label for="email">Email</label>
        <div class="input-wrapper">
          <i class="pi pi-envelope"></i>
          <InputText
            id="email"
            v-model="email"
            type="email"
            placeholder="seu@email.com"
            autocomplete="email"
            required
            autofocus
          />
        </div>
      </div>

      <transition name="shake">
        <div v-if="error" class="auth-message error" role="alert">
          <i class="pi pi-exclamation-circle"></i>
          <span>{{ error }}</span>
        </div>
      </transition>

      <Button type="submit" label="Enviar link" icon="pi pi-send" :loading="loading" class="auth-btn" />
    </form>

    <div v-else class="auth-form">
      <div class="auth-message success" role="status">
        <i class="pi pi-check-circle"></i>
        <span>{{ message }} Verifique também a caixa de spam.</span>
      </div>
      <Button label="Voltar para o login" icon="pi pi-arrow-left" class="auth-btn" @click="router.push({ path: '/login', query: { email } })" />
    </div>

    <template #footer>
      <p class="auth-footer">
        Lembrou a senha? <router-link to="/login" class="auth-link">Entrar</router-link>
      </p>
    </template>
  </AuthShell>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import AuthShell from '../components/AuthShell.vue'
import api from '../services/api'
import { errorMessage } from '@/utils/errors'

const router = useRouter()
const email = ref('')
const loading = ref(false)
const error = ref('')
const sent = ref(false)
const message = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/api/auth/esqueci-senha', { email: email.value.trim() })
    message.value = data.message
    sent.value = true
  } catch (e) {
    error.value = errorMessage(e, 'Não foi possível enviar o link agora. Tente novamente.')
  } finally {
    loading.value = false
  }
}
</script>
