<template>
  <header class="topbar glass" :class="{ 'collapsed': collapsed }">
    <div class="topbar-left">
      <button class="mobile-toggle" aria-label="Abrir menu" @click="$emit('toggleSidebar')">
        <i class="pi pi-bars"></i>
      </button>
      <div class="page-title">
        <h1>{{ pageTitle }}</h1>
      </div>
    </div>

    <div class="topbar-right">
      <div class="notif-wrapper" ref="notifWrapper">
        <button
          class="notification-bell"
          :aria-label="`Notificações (${notificationsStore.unreadCount} não lidas)`"
          @click="notificationsStore.togglePanel()"
        >
          <i class="pi pi-bell"></i>
          <span v-if="notificationsStore.unreadCount > 0" class="notification-badge">
            {{ notificationsStore.unreadCount > 9 ? '9+' : notificationsStore.unreadCount }}
          </span>
        </button>
        <div v-if="notificationsStore.showPanel" class="notification-panel glass">
          <div class="notif-header">
            <span>Notificações</span>
            <button v-if="notificationsStore.unreadCount > 0" class="notif-clear" @click="notificationsStore.markAllRead()">
              Marcar todas como lidas
            </button>
          </div>
          <div class="notif-list" v-if="notificationsStore.notifications.length > 0">
            <button
              v-for="n in notificationsStore.notifications"
              :key="n.id"
              class="notif-item"
              :class="{ unread: !n.lida }"
              @click="openNotification(n)"
            >
              <i class="notif-icon" :class="iconFor(n.tipo)"></i>
              <div class="notif-body">
                <div class="notif-title">{{ n.titulo }}</div>
                <div v-if="n.mensagem" class="notif-msg">{{ n.mensagem }}</div>
                <div class="notif-time">{{ formatTime(n.created_at) }}</div>
              </div>
            </button>
          </div>
          <div v-else class="notif-empty">
            <i class="pi pi-inbox"></i>
            <p>Nenhuma notificação por aqui.</p>
            <small>Você será avisado quando um cliente abrir ou aceitar uma proposta.</small>
          </div>
        </div>
      </div>

      <button class="theme-toggle-btn" @click="handleThemeToggle" :title="isDark ? 'Mudar para Tema Claro' : 'Mudar para Tema Escuro'" :aria-label="isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'">
        <i :class="isDark ? 'pi pi-moon' : 'pi pi-sun'"></i>
      </button>

      <div class="user-wrapper" ref="userWrapper">
        <button class="user-btn" @click="showUserMenu = !showUserMenu" :aria-expanded="showUserMenu" aria-haspopup="menu">
          <span class="user-avatar">{{ userInitials }}</span>
          <span class="user-info">
            <span class="user-name">{{ authStore.user?.nome || 'Usuário' }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </span>
          <i class="pi pi-chevron-down user-caret"></i>
        </button>
        <div v-if="showUserMenu" class="user-menu glass" role="menu">
          <div class="user-menu-header">
            <strong>{{ authStore.user?.nome }}</strong>
            <span>{{ authStore.user?.email }}</span>
          </div>
          <button role="menuitem" @click="openPasswordDialog"><i class="pi pi-key"></i> Alterar senha</button>
          <button v-if="authStore.isAdmin" role="menuitem" @click="goTo('/empresa')"><i class="pi pi-building"></i> Minha empresa</button>
          <button v-if="authStore.isAdmin" role="menuitem" @click="goTo('/configuracoes')"><i class="pi pi-cog"></i> Configurações</button>
          <button role="menuitem" class="danger" @click="handleLogout"><i class="pi pi-sign-out"></i> Sair</button>
        </div>
      </div>
    </div>

    <Dialog v-model:visible="passwordDialog" header="Alterar senha" modal :style="{ width: '420px' }" :breakpoints="{ '480px': '95vw' }">
      <form class="password-form" @submit.prevent="submitPassword">
        <div class="field">
          <label for="senha-atual">Senha atual</label>
          <Password inputId="senha-atual" v-model="passwordForm.atual" :feedback="false" toggleMask fluid autocomplete="current-password" />
        </div>
        <div class="field">
          <label for="senha-nova">Nova senha</label>
          <Password inputId="senha-nova" v-model="passwordForm.nova" :feedback="false" toggleMask fluid autocomplete="new-password" />
          <small>Mínimo de 8 caracteres. As outras sessões abertas serão encerradas.</small>
        </div>
        <div class="field">
          <label for="senha-conf">Confirme a nova senha</label>
          <Password inputId="senha-conf" v-model="passwordForm.confirmacao" :feedback="false" toggleMask fluid autocomplete="new-password" />
        </div>
        <Message v-if="passwordError" severity="error" :closable="false">{{ passwordError }}</Message>
        <div class="dialog-actions">
          <Button type="button" label="Cancelar" text @click="passwordDialog = false" />
          <Button type="submit" label="Salvar" icon="pi pi-check" :loading="savingPassword" />
        </div>
      </form>
    </Dialog>
  </header>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '../../stores/auth'
import { useNotificationsStore } from '../../stores/notifications'
import { isDarkMode, toggleDarkTheme } from '../../utils/theme'
import api from '../../services/api'
import { errorMessage } from '@/utils/errors'

defineProps({
  collapsed: Boolean,
})

defineEmits(['toggleSidebar'])

const route = useRoute()
const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const showUserMenu = ref(false)
const isDark = ref(isDarkMode())
const notifWrapper = ref(null)
const userWrapper = ref(null)

const passwordDialog = ref(false)
const savingPassword = ref(false)
const passwordError = ref('')
const passwordForm = reactive({ atual: '', nova: '', confirmacao: '' })

const ICONS = {
  visualizada: 'pi pi-eye text-blue-500',
  aceita: 'pi pi-check-circle text-green-500',
  vencendo: 'pi pi-clock text-orange-500',
  vencida: 'pi pi-calendar-times text-red-500',
}

function iconFor(tipo) {
  return ICONS[tipo] || 'pi pi-info-circle'
}

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return 'Agora'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min atrás`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} h atrás`
  return date.toLocaleDateString('pt-BR')
}

function handleThemeToggle() {
  isDark.value = toggleDarkTheme()
}

const pageTitle = computed(() => route.meta.title || 'Painel')

const userInitials = computed(() => {
  const name = authStore.user?.nome || ''
  return name
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || '?'
})

const roleLabel = computed(() => {
  const labels = { admin: 'Administrador', gerente: 'Gerente', vendedor: 'Vendedor' }
  return labels[authStore.user?.role] || ''
})

function openNotification(n) {
  notificationsStore.markRead(n)
  notificationsStore.closePanel()
  if (n.link) router.push(n.link)
}

function goTo(path) {
  showUserMenu.value = false
  router.push(path)
}

function openPasswordDialog() {
  showUserMenu.value = false
  passwordForm.atual = ''
  passwordForm.nova = ''
  passwordForm.confirmacao = ''
  passwordError.value = ''
  passwordDialog.value = true
}

async function submitPassword() {
  passwordError.value = ''
  if (passwordForm.nova.length < 8) {
    passwordError.value = 'A nova senha deve ter pelo menos 8 caracteres.'
    return
  }
  if (passwordForm.nova !== passwordForm.confirmacao) {
    passwordError.value = 'As senhas não conferem.'
    return
  }
  savingPassword.value = true
  try {
    const { data } = await api.post('/api/auth/alterar-senha', {
      senha_atual: passwordForm.atual,
      nova_senha: passwordForm.nova,
    })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    passwordDialog.value = false
    toast.add({ severity: 'success', summary: 'Senha alterada', detail: 'Sua nova senha já está valendo.', life: 4000 })
  } catch (e) {
    passwordError.value = errorMessage(e, 'Não foi possível alterar a senha.')
  } finally {
    savingPassword.value = false
  }
}

function handleClickOutside(e) {
  if (userWrapper.value && !userWrapper.value.contains(e.target)) showUserMenu.value = false
  if (notifWrapper.value && !notifWrapper.value.contains(e.target)) notificationsStore.closePanel()
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    showUserMenu.value = false
    notificationsStore.closePanel()
  }
}

async function handleLogout() {
  showUserMenu.value = false
  notificationsStore.reset()
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  notificationsStore.startPolling()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  notificationsStore.stopPolling()
})
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  right: 0;
  left: var(--sidebar-width);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 90;
  border: none !important;
  border-bottom: 1px solid var(--border-color) !important;
  border-radius: 0 !important;
  transition: left var(--transition-normal);
}

.topbar.collapsed {
  left: var(--sidebar-collapsed-width);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.mobile-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
}

.page-title h1 {
  font-size: 1.125rem;
  font-weight: 590; /* Linear strong weight */
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.theme-toggle-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.theme-toggle-btn:hover {
  background: var(--surface-100);
  color: var(--primary-500);
}

html.dark .theme-toggle-btn:hover {
  background: var(--surface-800);
}








.notification-bell {
  position: relative;
  cursor: pointer;
  font-size: 1.1rem;
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.notification-bell:hover {
  background: var(--surface-100);
  color: var(--primary-500);
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--accent-red);
  color: white;
  font-size: 0.6rem;
  font-weight: 700;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 340px;
  max-height: 400px;
  overflow-y: auto;
  border-radius: var(--border-radius-lg);
  z-index: 200;
  margin-top: 0.5rem;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 0.9rem;
}

.notif-clear {
  background: none;
  border: none;
  color: var(--primary-400);
  font-size: 0.75rem;
  cursor: pointer;
}

.notif-list {
  padding: 0.25rem 0;
}

.notif-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-fast);
}

.notif-item:hover {
  background: var(--surface-100);
}

.notif-item.unread {
  background: rgba(var(--primary-rgb), 0.04);
}

.notif-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.notif-msg {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}

.notif-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.notif-empty {
  padding: 2rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .topbar {
    left: 0;
  }
  .mobile-toggle {
    display: block;
  }
  .user-info,
  .user-caret {
    display: none;
  }
  .notification-panel {
    position: fixed;
    top: var(--topbar-height);
    left: 0.5rem;
    right: 0.5rem;
    width: auto;
  }
}

button.notification-bell {
  background: none;
  border: none;
  padding: 0;
}

.notif-wrapper,
.user-wrapper {
  position: relative;
}

.notification-panel {
  max-height: 440px;
}

button.notif-item {
  display: flex;
  gap: 0.75rem;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  border-bottom: 1px solid var(--border-color);
  font: inherit;
  color: inherit;
}

.notif-icon {
  font-size: 1rem;
  margin-top: 2px;
}

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-empty i {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
  display: block;
}

.notif-empty p {
  margin: 0 0 0.25rem;
  color: var(--text-secondary);
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem 0.25rem 0.25rem;
  border-radius: 999px;
  color: var(--text-secondary);
  transition: background var(--transition-fast);
}

.user-btn:hover {
  background: var(--surface-100);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.15;
}

.user-name {
  font-size: 0.85rem;
  font-weight: 590;
  color: var(--text-primary);
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.user-caret {
  font-size: 0.7rem;
}

.user-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  min-width: 220px;
  border-radius: var(--border-radius-lg);
  z-index: 200;
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
}

.user-menu-header {
  display: flex;
  flex-direction: column;
  padding: 0.6rem 0.75rem 0.7rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
}

.user-menu-header span {
  font-size: 0.75rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu button {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  background: none;
  border: none;
  padding: 0.6rem 0.75rem;
  border-radius: var(--border-radius-sm);
  font: inherit;
  font-size: 0.85rem;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.user-menu button:hover {
  background: var(--surface-100);
}

.user-menu button.danger {
  color: var(--accent-red);
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.password-form .field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.password-form label {
  font-size: 0.85rem;
  font-weight: 600;
}

.password-form small {
  color: var(--text-muted);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

html.dark .user-btn:hover,
html.dark .user-menu button:hover {
  background: var(--surface-800);
}
</style>
