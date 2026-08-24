<template>
  <div class="usuarios-view fade-in">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-titles">
        <h2>Gestão de Usuários & Equipe</h2>
        <p class="page-desc">Gerencie permissões, cargos e os acessos da sua empresa</p>
      </div>

      <div class="header-actions">
        <Button
          v-if="quota && !quota.pode_adicionar"
          label="Fazer Upgrade de Plano"
          icon="pi pi-bolt"
          severity="warning"
          outlined
          @click="showPlanosModal = true"
        />
        <Button
          label="Novo Usuário"
          icon="pi pi-user-plus"
          @click="openDialog()"
          :disabled="quota && !quota.pode_adicionar"
          :title="quota && !quota.pode_adicionar ? 'Limite de usuários atingido no seu plano' : 'Adicionar novo membro'"
        />
      </div>
    </div>

    <!-- Quota / Capacity Banner -->
    <div class="quota-card glass">
      <div class="quota-left">
        <div class="quota-badge" :class="quota?.plano_slug || 'gratuito'">
          <i :class="getPlanIcon(quota?.plano_slug)"></i>
          <span>Plano {{ quota?.plano_nome || 'Gratuito' }}</span>
        </div>
        <div class="quota-info">
          <div class="quota-title">
            <span>Capacidade da Equipe:</span>
            <strong>
              {{ quota?.ativos ?? 0 }} {{ quota?.max_usuarios ? `/ ${quota.max_usuarios}` : '' }} membros ativos
              <span v-if="!quota?.max_usuarios" class="unlimited-tag">Ilimitado</span>
            </strong>
          </div>
          <p class="quota-desc">
            {{ quotaDesc }}
          </p>
        </div>
      </div>

      <div class="quota-right">
        <div class="quota-progress-wrapper" v-if="quota?.max_usuarios">
          <div class="progress-bar-bg">
            <div
              class="progress-bar-fill"
              :style="{ width: `${quotaPercent}%` }"
              :class="{ full: quotaPercent >= 100, warning: quotaPercent >= 80 && quotaPercent < 100 }"
            ></div>
          </div>
          <span class="progress-text">{{ quotaPercent }}% utilizado</span>
        </div>

        <button class="upgrade-link-btn" @click="showPlanosModal = true">
          <i class="pi pi-sparkles"></i>
          <span>Alterar Plano</span>
        </button>
      </div>
    </div>

    <!-- Filters & Search Bar -->
    <div class="filter-bar glass">
      <div class="search-box">
        <i class="pi pi-search search-icon"></i>
        <InputText
          v-model="search"
          placeholder="Buscar por nome, e-mail ou cargo..."
          class="search-input"
          @input="debouncedFetch"
        />
        <i v-if="search" class="pi pi-times clear-search" @click="search = ''; fetchUsuarios()"></i>
      </div>

      <div class="filter-dropdowns">
        <select v-model="selectedRole" class="filter-select" @change="fetchUsuarios">
          <option value="">Todas as Permissões</option>
          <option value="admin">👑 Administrador</option>
          <option value="gerente">👔 Gerente</option>
          <option value="vendedor">💼 Vendedor</option>
        </select>

        <select v-model="selectedStatus" class="filter-select" @change="fetchUsuarios">
          <option value="all">Todos os Status</option>
          <option value="active">🟢 Apenas Ativos</option>
          <option value="inactive">🔴 Apenas Inativos</option>
        </select>
      </div>
    </div>

    <!-- Table Card -->
    <div class="table-card glass">
      <DataTable
        :value="usuarios"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
        class="custom-table"
      >
        <!-- Nome & Perfil -->
        <Column field="nome" header="Membro" sortable>
          <template #body="{ data }">
            <div class="user-cell">
              <div class="user-avatar" :style="{ background: getAvatarGradient(data.nome) }">
                {{ getInitials(data.nome) }}
              </div>
              <div class="user-details">
                <div class="user-name-line">
                  <span class="user-name">{{ data.nome }}</span>
                  <span v-if="data.id === authStore.user?.id" class="me-badge">Você</span>
                </div>
                <div class="user-email">{{ data.email }}</div>
              </div>
            </div>
          </template>
        </Column>

        <!-- Cargo / Função -->
        <Column field="cargo" header="Cargo / Função" sortable>
          <template #body="{ data }">
            <span class="cargo-text" v-if="data.cargo">
              <i class="pi pi-briefcase mr-1 opacity-70"></i>
              {{ data.cargo }}
            </span>
            <span class="text-muted text-xs" v-else>Não informado</span>
          </template>
        </Column>

        <!-- Contato / Telefone -->
        <Column field="telefone" header="Telefone">
          <template #body="{ data }">
            <span class="phone-text" v-if="data.telefone">
              <i class="pi pi-phone mr-1 opacity-70"></i>
              {{ data.telefone }}
            </span>
            <span class="text-muted text-xs" v-else>—</span>
          </template>
        </Column>

        <!-- Permissão -->
        <Column field="role" header="Permissão" sortable>
          <template #body="{ data }">
            <span class="role-badge" :class="data.role">
              <i :class="getRoleIcon(data.role)"></i>
              {{ roleLabels[data.role] || data.role }}
            </span>
          </template>
        </Column>

        <!-- Status -->
        <Column field="ativo" header="Status" sortable>
          <template #body="{ data }">
            <button
              class="status-toggle-btn"
              :class="data.ativo ? 'active' : 'inactive'"
              @click="toggleUserStatus(data)"
              :disabled="data.id === authStore.user?.id"
              :title="data.id === authStore.user?.id ? 'Você não pode desativar seu próprio usuário' : (data.ativo ? 'Clique para desativar' : 'Clique para ativar')"
            >
              <span class="status-dot"></span>
              <span>{{ data.ativo ? 'Ativo' : 'Inativo' }}</span>
            </button>
          </template>
        </Column>

        <!-- Último Acesso -->
        <Column field="ultimo_login" header="Último Acesso" sortable>
          <template #body="{ data }">
            <span class="text-xs" :class="data.ultimo_login ? 'text-secondary' : 'text-muted'">
              <i class="pi pi-history mr-1 opacity-70"></i>
              {{ formatRelativeTime(data.ultimo_login) }}
            </span>
          </template>
        </Column>

        <!-- Ações -->
        <Column header="Ações" style="width: 110px" alignFrozen="right">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                title="Editar Usuário"
                @click="openDialog(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                title="Desativar Usuário"
                @click="confirmDelete(data)"
                :disabled="data.id === authStore.user?.id"
              />
            </div>
          </template>
        </Column>

        <!-- Empty State -->
        <template #empty>
          <div class="empty-table">
            <i class="pi pi-users empty-icon"></i>
            <h4>Nenhum membro encontrado</h4>
            <p>Tente ajustar os filtros de busca ou adicione um novo usuário.</p>
            <Button
              v-if="quota?.pode_adicionar"
              label="Adicionar Primeiro Membro"
              icon="pi pi-plus"
              size="small"
              class="mt-2"
              @click="openDialog()"
            />
          </div>
        </template>
      </DataTable>
    </div>

    <!-- User Form Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingUser ? 'Editar Membro da Equipe' : 'Adicionar Novo Membro'"
      modal
      :style="{ width: '540px' }"
      class="user-dialog"
    >
      <form @submit.prevent="handleSave" class="dialog-form">
        <!-- Nome Completo -->
        <div class="form-group">
          <label>Nome Completo <span class="required">*</span></label>
          <InputText v-model="form.nome" placeholder="Ex: Lucas Carvalho" required />
        </div>

        <!-- E-mail -->
        <div class="form-group">
          <label>E-mail de Acesso <span class="required">*</span></label>
          <InputText v-model="form.email" type="email" placeholder="lucas@empresa.com.br" required />
        </div>

        <!-- Cargo e Telefone -->
        <div class="form-row">
          <div class="form-group">
            <label>Cargo / Função</label>
            <InputText v-model="form.cargo" placeholder="Ex: Executivo de Vendas" />
          </div>
          <div class="form-group">
            <label>Telefone / WhatsApp</label>
            <InputText v-model="form.telefone" placeholder="(11) 98765-4321" />
          </div>
        </div>

        <!-- Nível de Permissão com Cartões Explicativos -->
        <div class="form-group">
          <label>Nível de Permissão <span class="required">*</span></label>
          <div class="role-selector-grid">
            <div
              v-for="opt in roleOptions"
              :key="opt.value"
              class="role-card"
              :class="{ selected: form.role === opt.value }"
              @click="form.role = opt.value"
            >
              <div class="role-card-header">
                <i :class="opt.icon"></i>
                <strong>{{ opt.label }}</strong>
              </div>
              <p class="role-card-desc">{{ opt.desc }}</p>
            </div>
          </div>
        </div>

        <!-- Senha -->
        <div class="form-group" v-if="!editingUser">
          <label>Senha de Acesso <span class="required">*</span></label>
          <div class="password-wrapper">
            <InputText
              v-model="form.senha"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder="Mínimo 6 caracteres"
              minlength="6"
              class="w-full"
            />
            <i
              class="pi password-toggle-icon"
              :class="showPassword ? 'pi-eye-slash' : 'pi-eye'"
              @click="showPassword = !showPassword"
            ></i>
          </div>
        </div>

        <div class="form-group" v-else>
          <label>Redefinir Senha <span class="text-muted text-xs">(opcional, deixe vazio para manter)</span></label>
          <div class="password-wrapper">
            <InputText
              v-model="form.senha"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Nova senha (deixe vazio para não alterar)"
              minlength="6"
              class="w-full"
            />
            <i
              class="pi password-toggle-icon"
              :class="showPassword ? 'pi-eye-slash' : 'pi-eye'"
              @click="showPassword = !showPassword"
            ></i>
          </div>
        </div>

        <!-- Actions -->
        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button
            type="submit"
            :label="editingUser ? 'Salvar Alterações' : 'Criar Usuário'"
            icon="pi pi-check"
            :loading="saving"
          />
        </div>
      </form>
    </Dialog>

    <!-- Modal de Planos Integrado -->
    <PlanosModal
      v-model:visible="showPlanosModal"
      @plano-alterado="onPlanoAlterado"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import PlanosModal from '@/components/PlanosModal.vue'
import api from '../services/api'

const authStore = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const usuarios = ref([])
const quota = ref(null)
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const selectedRole = ref('')
const selectedStatus = ref('all')
const dialogVisible = ref(false)
const showPlanosModal = ref(false)
const showPassword = ref(false)
const editingUser = ref(null)

const roleLabels = { admin: 'Administrador', gerente: 'Gerente', vendedor: 'Vendedor' }

const roleOptions = [
  {
    value: 'admin',
    label: 'Administrador',
    icon: 'pi pi-shield',
    desc: 'Acesso total a todas as configurações, faturamento, equipe e relatórios.',
  },
  {
    value: 'gerente',
    label: 'Gerente',
    icon: 'pi pi-users',
    desc: 'Visualiza e gerencia todas as propostas, clientes e orçamentos da equipe.',
  },
  {
    value: 'vendedor',
    label: 'Vendedor',
    icon: 'pi pi-briefcase',
    desc: 'Cria e acompanha suas próprias propostas comerciais e orçamentos.',
  },
]

const form = reactive({
  nome: '',
  email: '',
  cargo: '',
  telefone: '',
  role: 'vendedor',
  senha: '',
})

// Computeds
const quotaPercent = computed(() => {
  if (!quota.value || !quota.value.max_usuarios) return 0
  const pct = Math.round((quota.value.ativos / quota.value.max_usuarios) * 100)
  return Math.min(pct, 100)
})

const quotaDesc = computed(() => {
  if (!quota.value) return 'Carregando capacidade da conta...'
  if (!quota.value.max_usuarios) {
    return 'Seu plano atual permite cadastrar membros ilimitados para sua equipe.'
  }
  const restantes = quota.value.max_usuarios - quota.value.ativos
  if (restantes <= 0) {
    return 'Você atingiu o limite de usuários ativos deste plano. Faça upgrade para adicionar mais pessoas.'
  }
  return `Você ainda pode adicionar mais ${restantes} usuário(s) ativos no seu plano atual.`
})

// Helpers
function getPlanIcon(slug) {
  const map = {
    gratuito: 'pi pi-shield',
    inicial: 'pi pi-compass',
    pro: 'pi pi-bolt',
    empresarial: 'pi pi-crown',
  }
  return map[slug] || 'pi pi-tag'
}

function getRoleIcon(role) {
  const map = {
    admin: 'pi pi-shield',
    gerente: 'pi pi-users',
    vendedor: 'pi pi-briefcase',
  }
  return map[role] || 'pi pi-user'
}

function getInitials(name) {
  if (!name) return 'U'
  return name
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase()
}

function getAvatarGradient(name) {
  const gradients = [
    'linear-gradient(135deg, #6366f1, #4f46e5)',
    'linear-gradient(135deg, #ec4899, #db2777)',
    'linear-gradient(135deg, #10b981, #059669)',
    'linear-gradient(135deg, #f59e0b, #d97706)',
    'linear-gradient(135deg, #06b6d4, #0891b2)',
    'linear-gradient(135deg, #8b5cf6, #7c3aed)',
  ]
  let sum = 0
  for (let i = 0; i < (name || '').length; i++) {
    sum += name.charCodeAt(i)
  }
  return gradients[sum % gradients.length]
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Nunca acessou'
  const date = new Date(dateStr)
  const now = new Date()
  const diffSec = Math.floor((now - date) / 1000)

  if (diffSec < 60) return 'Agora mesmo'
  if (diffSec < 3600) return `Há ${Math.floor(diffSec / 60)} min`
  if (diffSec < 86400) return `Há ${Math.floor(diffSec / 3600)} horas`
  if (diffSec < 172800) return 'Ontem'
  return date.toLocaleDateString('pt-BR')
}

// Fetch Logic
let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchUsuarios, 300)
}

async function fetchQuota() {
  try {
    const res = await api.get('/api/usuarios/quota')
    if (res.data) quota.value = res.data
  } catch (e) {
    console.error('Erro ao carregar quota de usuários:', e)
  }
}

async function fetchUsuarios() {
  loading.value = true
  try {
    const params = {}
    if (search.value && search.value.trim()) params.search = search.value.trim()
    if (selectedRole.value) params.role = selectedRole.value
    if (selectedStatus.value) params.status = selectedStatus.value

    const { data } = await api.get('/api/usuarios', { params })
    usuarios.value = data.items
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Erro',
      detail: e.response?.data?.detail || 'Erro ao carregar usuários',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Dialog Logic
function openDialog(user = null) {
  editingUser.value = user
  showPassword.value = false

  if (user) {
    Object.assign(form, {
      nome: user.nome,
      email: user.email,
      cargo: user.cargo || '',
      telefone: user.telefone || '',
      role: user.role || 'vendedor',
      senha: '',
    })
  } else {
    Object.assign(form, {
      nome: '',
      email: '',
      cargo: '',
      telefone: '',
      role: 'vendedor',
      senha: '',
    })
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingUser.value) {
      const payload = {
        nome: form.nome,
        email: form.email,
        cargo: form.cargo,
        telefone: form.telefone,
        role: form.role,
      }
      if (form.senha && form.senha.trim().length > 0) {
        payload.senha = form.senha.trim()
      }
      await api.put(`/api/usuarios/${editingUser.value.id}`, payload)
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Membro atualizado com sucesso!',
        life: 3000,
      })
    } else {
      await api.post('/api/usuarios', {
        nome: form.nome,
        email: form.email,
        cargo: form.cargo,
        telefone: form.telefone,
        role: form.role,
        senha: form.senha,
      })
      toast.add({
        severity: 'success',
        summary: 'Sucesso',
        detail: 'Novo membro adicionado com sucesso!',
        life: 3000,
      })
    }
    dialogVisible.value = false
    await fetchQuota()
    await fetchUsuarios()
  } catch (e) {
    const errorMsg = e.response?.data?.detail || 'Erro ao salvar usuário'
    toast.add({
      severity: 'error',
      summary: 'Erro ao Salvar',
      detail: errorMsg,
      life: 4500,
    })
    if (e.response?.status === 402) {
      showPlanosModal.value = true
    }
  } finally {
    saving.value = false
  }
}

async function toggleUserStatus(user) {
  try {
    await api.patch(`/api/usuarios/${user.id}/toggle-status`)
    toast.add({
      severity: 'success',
      summary: 'Status Atualizado',
      detail: `Usuário ${user.nome} agora está ${!user.ativo ? 'ativo' : 'inativo'}.`,
      life: 3000,
    })
    await fetchQuota()
    await fetchUsuarios()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Erro ao alternar status do usuário'
    toast.add({ severity: 'error', summary: 'Atenção', detail: msg, life: 4000 })
    if (e.response?.status === 402) {
      showPlanosModal.value = true
    }
  }
}

function confirmDelete(user) {
  confirm.require({
    message: `Deseja realmente desativar o acesso de "${user.nome}"? O usuário perderá o acesso ao painel.`,
    header: 'Confirmar Desativação',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Sim, Desativar',
    rejectLabel: 'Cancelar',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/api/usuarios/${user.id}`)
        toast.add({
          severity: 'success',
          summary: 'Desativado',
          detail: `O usuário ${user.nome} foi desativado com sucesso.`,
          life: 3000,
        })
        await fetchQuota()
        await fetchUsuarios()
      } catch (e) {
        toast.add({
          severity: 'error',
          summary: 'Erro',
          detail: e.response?.data?.detail || 'Erro ao desativar',
          life: 3000,
        })
      }
    },
  })
}

function onPlanoAlterado() {
  fetchQuota()
  fetchUsuarios()
  if (authStore.fetchUser) {
    authStore.fetchUser()
  }
}

onMounted(() => {
  fetchQuota()
  fetchUsuarios()
})
</script>

<style scoped>
.usuarios-view {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-bottom: 2.5rem;
}

/* Page Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-titles h2 {
  font-size: 1.45rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.02em;
}

.page-desc {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 0.2rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

/* Quota / Capacity Card */
.quota-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.25rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.25rem;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--glass-shadow);
}

.quota-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex: 1;
  min-width: 280px;
}

.quota-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.9rem;
  border-radius: var(--border-radius-md);
  font-size: 0.82rem;
  font-weight: 700;
  flex-shrink: 0;
}

.quota-badge.gratuito { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }
.quota-badge.inicial { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
.quota-badge.pro { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
.quota-badge.empresarial { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

.quota-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.quota-title {
  font-size: 0.92rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.unlimited-tag {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  margin-left: 0.3rem;
}

.quota-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0;
}

.quota-right {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.quota-progress-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  width: 140px;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary-500);
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-bar-fill.warning { background: #f59e0b; }
.progress-bar-fill.full { background: #ef4444; }

.progress-text {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-align: right;
}

.upgrade-link-btn {
  background: rgba(var(--primary-rgb), 0.1);
  border: 1px solid rgba(var(--primary-rgb), 0.3);
  color: var(--primary-400);
  padding: 0.45rem 0.9rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all var(--transition-fast);
}

.upgrade-link-btn:hover {
  background: var(--primary-500);
  color: white;
  transform: translateY(-1px);
}

/* Filter Bar */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  border-radius: var(--border-radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 250px;
}

.search-icon {
  position: absolute;
  left: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.search-input {
  width: 100%;
  padding-left: 2.35rem !important;
  font-size: 0.85rem;
}

.clear-search {
  position: absolute;
  right: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
}

.filter-dropdowns {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 0.5rem 0.85rem;
  border-radius: var(--border-radius-sm);
  outline: none;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
}

/* Table Card */
.table-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: var(--glass-shadow);
}

/* User cell */
.user-cell {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.user-name-line {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.user-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text-primary);
}

.me-badge {
  background: rgba(var(--primary-rgb), 0.15);
  color: var(--primary-400);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  text-transform: uppercase;
}

.user-email {
  font-size: 0.76rem;
  color: var(--text-muted);
}

.cargo-text,
.phone-text {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

/* Badges */
.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.role-badge.admin {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.role-badge.gerente {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.role-badge.vendedor {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* Status toggle button */
.status-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.65rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.status-toggle-btn.active {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-toggle-btn.inactive {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-toggle-btn:hover:not(:disabled) {
  filter: brightness(1.2);
  transform: scale(1.03);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.action-buttons {
  display: flex;
  gap: 0.2rem;
}

.empty-table {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 1.5rem;
  gap: 0.5rem;
  color: var(--text-muted);
  text-align: center;
}

.empty-icon {
  font-size: 2.8rem;
  opacity: 0.4;
  margin-bottom: 0.5rem;
}

/* Dialog Form */
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  padding-top: 0.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
}

.form-group label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.required {
  color: var(--danger-400, #ef4444);
}

.form-row {
  display: flex;
  gap: 1rem;
}

.role-selector-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.role-card {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  border-radius: var(--border-radius-md);
  padding: 0.75rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  transition: all var(--transition-fast);
}

.role-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-400);
}

.role-card.selected {
  border-color: var(--primary-500);
  background: rgba(var(--primary-rgb), 0.08);
  box-shadow: var(--shadow-glow-primary);
}

.role-card-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: var(--text-primary);
}

.role-card-desc {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.3;
}

.password-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-toggle-icon {
  position: absolute;
  right: 0.85rem;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-actions {
    flex-direction: column;
  }
  .header-actions button {
    width: 100%;
  }
  .quota-card {
    flex-direction: column;
    align-items: stretch;
  }
  .quota-right {
    justify-content: space-between;
  }
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-dropdowns {
    flex-direction: column;
  }
  .role-selector-grid {
    grid-template-columns: 1fr;
  }
  .form-row {
    flex-direction: column;
  }
}
</style>
