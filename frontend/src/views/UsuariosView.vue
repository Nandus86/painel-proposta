<template>
  <div class="usuarios-view fade-in">
    <div class="page-header">
      <div>
        <h2>Usuários</h2>
        <p class="page-desc">Gerencie a equipe da sua empresa</p>
      </div>
      <Button
        label="Novo Usuário"
        icon="pi pi-plus"
        @click="openDialog()"
      />
    </div>

    <!-- Search -->
    <div class="search-bar glass">
      <span class="p-input-icon-left w-full">
        <i class="pi pi-search"></i>
        <InputText v-model="search" placeholder="Buscar por nome ou email..." class="w-full" @input="debouncedFetch" />
      </span>
    </div>

    <!-- Table -->
    <div class="table-card glass">
      <DataTable
        :value="usuarios"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
        class="custom-table"
      >
        <Column field="nome" header="Nome" sortable>
          <template #body="{ data }">
            <div class="user-cell">
              <div class="user-avatar-sm">
                {{ data.nome?.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() }}
              </div>
              <div>
                <div class="cell-primary">{{ data.nome }}</div>
                <div class="cell-secondary">{{ data.email }}</div>
              </div>
            </div>
          </template>
        </Column>
        <Column field="cargo" header="Cargo" />
        <Column field="role" header="Permissão">
          <template #body="{ data }">
            <span class="role-badge" :class="data.role">
              {{ roleLabels[data.role] }}
            </span>
          </template>
        </Column>
        <Column field="ativo" header="Status">
          <template #body="{ data }">
            <span class="status-badge" :class="data.ativo ? 'active' : 'inactive'">
              {{ data.ativo ? 'Ativo' : 'Inativo' }}
            </span>
          </template>
        </Column>
        <Column header="Ações" style="width: 120px">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                @click="openDialog(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                @click="confirmDelete(data)"
                :disabled="data.id === authStore.user?.id"
              />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-table">
            <i class="pi pi-users"></i>
            <p>Nenhum usuário encontrado</p>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingUser ? 'Editar Usuário' : 'Novo Usuário'"
      modal
      :style="{ width: '480px' }"
      class="user-dialog"
    >
      <form @submit.prevent="handleSave" class="dialog-form">
        <div class="field">
          <label>Nome Completo *</label>
          <InputText v-model="form.nome" required />
        </div>
        <div class="field">
          <label>Email *</label>
          <InputText v-model="form.email" type="email" required />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Cargo</label>
            <InputText v-model="form.cargo" placeholder="Ex: Gerente Comercial" />
          </div>
          <div class="field">
            <label>Telefone</label>
            <InputText v-model="form.telefone" placeholder="(00) 00000-0000" />
          </div>
        </div>
        <div class="field">
          <label>Permissão *</label>
          <Select v-model="form.role" :options="roleOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="field" v-if="!editingUser">
          <label>Senha *</label>
          <InputText v-model="form.senha" type="password" required placeholder="Mínimo 6 caracteres" />
        </div>
        <div class="field" v-else>
          <label>Nova Senha (deixe vazio para manter)</label>
          <InputText v-model="form.senha" type="password" placeholder="••••••••" />
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button type="submit" :label="editingUser ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import api from '../services/api'

const authStore = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const usuarios = ref([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const dialogVisible = ref(false)
const editingUser = ref(null)

const roleLabels = { admin: 'Admin', gerente: 'Gerente', vendedor: 'Vendedor' }
const roleOptions = [
  { label: 'Administrador', value: 'admin' },
  { label: 'Gerente', value: 'gerente' },
  { label: 'Vendedor', value: 'vendedor' },
]

const form = reactive({
  nome: '',
  email: '',
  cargo: '',
  telefone: '',
  role: 'vendedor',
  senha: '',
})

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchUsuarios, 300)
}

async function fetchUsuarios() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    const { data } = await api.get('/api/usuarios', { params })
    usuarios.value = data.items
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar usuários', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openDialog(user = null) {
  editingUser.value = user
  if (user) {
    Object.assign(form, {
      nome: user.nome,
      email: user.email,
      cargo: user.cargo || '',
      telefone: user.telefone || '',
      role: user.role,
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
      const payload = { ...form }
      if (!payload.senha) delete payload.senha
      await api.put(`/api/usuarios/${editingUser.value.id}`, payload)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Usuário atualizado', life: 3000 })
    } else {
      await api.post('/api/usuarios', form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Usuário criado', life: 3000 })
    }
    dialogVisible.value = false
    await fetchUsuarios()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.response?.data?.detail || 'Erro ao salvar', life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(user) {
  confirm.require({
    message: `Deseja desativar o usuário "${user.nome}"?`,
    header: 'Confirmar Desativação',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Desativar',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/usuarios/${user.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Usuário desativado', life: 3000 })
        await fetchUsuarios()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Erro', detail: e.response?.data?.detail || 'Erro', life: 3000 })
      }
    },
  })
}

onMounted(fetchUsuarios)
</script>

<style scoped>
.usuarios-view {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-header h2 {
  font-size: 1.35rem;
  font-weight: 700;
}

.page-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.search-bar {
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
}

.search-bar .p-input-icon-left {
  width: 100%;
  position: relative;
}

.search-bar .p-input-icon-left > i {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  z-index: 1;
}

.search-bar :deep(.p-inputtext) {
  padding-left: 2.25rem !important;
}

.w-full {
  width: 100%;
}

.table-card {
  padding: 0;
  overflow: hidden;
}

.table-card :deep(.p-datatable) {
  background: transparent;
}

/* User cell */
.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-sm {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.cell-primary {
  font-weight: 600;
  font-size: 0.9rem;
}

.cell-secondary {
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* Badges */
.role-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.role-badge.admin {
  background: rgba(99, 102, 241, 0.15);
  color: var(--primary-400);
}

.role-badge.gerente {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning-400);
}

.role-badge.vendedor {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-400);
}

.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-400);
}

.status-badge.inactive {
  background: rgba(244, 63, 94, 0.15);
  color: var(--danger-400);
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.empty-table {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
  gap: 0.5rem;
  color: var(--text-muted);
}

.empty-table i {
  font-size: 2rem;
}

/* Dialog */
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 0.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
}

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.field :deep(.p-inputtext),
.field :deep(.p-select) {
  width: 100%;
}

.field-row {
  display: flex;
  gap: 1rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
