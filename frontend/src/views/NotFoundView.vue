<template>
  <AuthShell title="Página não encontrada" subtitle="O endereço acessado não existe ou foi movido." icon="pi pi-compass">
    <div class="auth-form">
      <Button
        :label="authStore.isAuthenticated ? 'Voltar ao painel' : 'Ir para o login'"
        icon="pi pi-home"
        class="auth-btn"
        @click="router.push(authStore.isAuthenticated ? '/' : '/login')"
      />
    </div>
  </AuthShell>
</template>

<script setup>
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import AuthShell from '../components/AuthShell.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
</script>
