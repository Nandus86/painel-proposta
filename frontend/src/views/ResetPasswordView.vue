<template>
  <AuthShell title="Criar nova senha" subtitle="Escolha uma senha com pelo menos 8 caracteres." icon="pi pi-lock">
    <div v-if="!token" class="auth-form">
      <div class="auth-message error" role="alert">
        <i class="pi pi-exclamation-circle"></i>
        <span>Link inválido. Abra o link exatamente como recebido no e-mail ou solicite um novo.</span>
      </div>
      <Button label="Solicitar novo link" icon="pi pi-refresh" class="auth-btn" @click="router.push('/esqueci-senha')" />
    </div>

    <form v-else-if="!done" @submit.prevent="handleSubmit" class="auth-form">
      <div class="field">
        <label for="senha">Nova senha</label>
        <div class="input-wrapper">
          <i class="pi pi-lock"></i>
          <InputText
            id="senha"
            v-model="senha"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Mínimo de 8 caracteres"
            autocomplete="new-password"
            minlength="8"
            required
            autofocus
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

      <div class="field">
        <label for="confirmacao">Confirme a nova senha</label>
        <div class="input-wrapper">
          <i class="pi pi-lock"></i>
          <InputText
            id="confirmacao"
            v-model="confirmacao"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Repita a senha"
            autocomplete="new-password"
            required
          />
        </div>
      </div>

      <transition name="shake">
        <div v-if="error" class="auth-message error" role="alert">
          <i class="pi pi-exclamation-circle"></i>
          <span>{{ error }}</span>
        </div>
      </transition>

      <Button type="submit" label="Salvar nova senha" icon="pi pi-check" :loading="loading" class="auth-btn" />
    </form>

    <div v-else class="auth-form">
      <div class="auth-message success" role="status">
        <i class="pi pi-check-circle"></i>
        <span>Senha redefinida! Por segurança, todas as sessões abertas foram encerradas.</span>
      </div>
      <Button label="Ir para o login" icon="pi pi-sign-in" class="auth-btn" @click="router.push('/login')" />
    </div>
  </AuthShell>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import AuthShell from '../components/AuthShell.vue'
import api from '../services/api'
import { errorMessage } from '@/utils/errors'

const route = useRoute()
const router = useRouter()

const token = ref(typeof route.query.token === 'string' ? route.query.token : '')
const senha = ref('')
const confirmacao = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const done = ref(false)

onMounted(() => {
  // Tira o token da barra de endereço (não fica no histórico nem em prints de tela)
  if (token.value) router.replace({ path: route.path })
})

async function handleSubmit() {
  error.value = ''
  if (senha.value.length < 8) {
    error.value = 'A senha deve ter pelo menos 8 caracteres.'
    return
  }
  if (senha.value !== confirmacao.value) {
    error.value = 'As senhas não conferem.'
    return
  }
  loading.value = true
  try {
    await api.post('/api/auth/redefinir-senha', { token: token.value, senha: senha.value })
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    done.value = true
  } catch (e) {
    error.value = errorMessage(e, 'Não foi possível redefinir a senha.')
  } finally {
    loading.value = false
  }
}
</script>
