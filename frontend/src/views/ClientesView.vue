<template>
  <div class="clientes-view fade-in">
    <div class="page-header">
      <div>
        <h2>Clientes</h2>
        <p class="page-desc">Gerencie sua carteira de clientes</p>
      </div>
      <Button label="Novo Cliente" icon="pi pi-plus" @click="openDialog()" />
    </div>

    <!-- Search -->
    <div class="search-bar glass">
      <span class="p-input-icon-left w-full">
        <i class="pi pi-search"></i>
        <InputText v-model="search" placeholder="Buscar por razão social, fantasia ou CNPJ..." class="w-full" @input="debouncedFetch" />
      </span>
      <div class="search-stats" v-if="total > 0">
        <span>{{ total }} cliente{{ total !== 1 ? 's' : '' }}</span>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card glass">
      <DataTable
        :value="clientes"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
      >
        <Column field="razao_social" header="Cliente" sortable>
          <template #body="{ data }">
            <div>
              <div class="cell-primary">{{ data.nome_fantasia || data.razao_social }}</div>
              <div class="cell-secondary" v-if="data.nome_fantasia">{{ data.razao_social }}</div>
            </div>
          </template>
        </Column>
        <Column header="Documento">
          <template #body="{ data }">
            <span class="mono">{{ data.cnpj || data.cpf || '—' }}</span>
          </template>
        </Column>
        <Column field="contato_nome" header="Contato">
          <template #body="{ data }">
            <div v-if="data.contato_nome">
              <div class="cell-primary">{{ data.contato_nome }}</div>
              <div class="cell-secondary">{{ data.contato_cargo }}</div>
            </div>
            <span v-else class="text-muted">—</span>
          </template>
        </Column>
        <Column field="email" header="Email">
          <template #body="{ data }">
            <span>{{ data.email || '—' }}</span>
          </template>
        </Column>
        <Column field="cidade" header="Cidade">
          <template #body="{ data }">
            <span>{{ data.cidade ? `${data.cidade}/${data.estado}` : '—' }}</span>
          </template>
        </Column>
        <Column header="Ações" style="width: 120px">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" @click="openDialog(data)" />
              <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="confirmDelete(data)" />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-table">
            <i class="pi pi-address-book"></i>
            <p>Nenhum cliente encontrado</p>
            <Button label="Cadastrar Primeiro Cliente" icon="pi pi-plus" size="small" @click="openDialog()" />
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Pagination -->
    <div class="pagination-bar" v-if="total > limit">
      <Button
        icon="pi pi-angle-left"
        severity="secondary"
        text
        :disabled="skip === 0"
        @click="skip = Math.max(0, skip - limit); fetchClientes()"
      />
      <span class="pagination-info">
        {{ skip + 1 }}–{{ Math.min(skip + limit, total) }} de {{ total }}
      </span>
      <Button
        icon="pi pi-angle-right"
        severity="secondary"
        text
        :disabled="skip + limit >= total"
        @click="skip += limit; fetchClientes()"
      />
    </div>

    <!-- Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingCliente ? 'Editar Cliente' : 'Novo Cliente'"
      modal
      :style="{ width: '600px' }"
    >
      <form @submit.prevent="handleSave" class="dialog-form">
        <div class="form-section-title">Dados da Empresa</div>
        <div class="field-row">
          <div class="field flex-2">
            <label>Razão Social *</label>
            <InputText v-model="form.razao_social" required />
          </div>
          <div class="field flex-1">
            <label>Nome Fantasia</label>
            <InputText v-model="form.nome_fantasia" />
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>CNPJ</label>
            <InputText v-model="form.cnpj" placeholder="00.000.000/0000-00" />
          </div>
          <div class="field">
            <label>CPF</label>
            <InputText v-model="form.cpf" placeholder="000.000.000-00" />
          </div>
        </div>

        <div class="form-section-title">Contato</div>
        <div class="field-row">
          <div class="field">
            <label>Email</label>
            <InputText v-model="form.email" type="email" />
          </div>
          <div class="field">
            <label>Telefone</label>
            <InputText v-model="form.telefone" />
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Nome do Contato</label>
            <InputText v-model="form.contato_nome" />
          </div>
          <div class="field">
            <label>Cargo do Contato</label>
            <InputText v-model="form.contato_cargo" />
          </div>
        </div>

        <div class="form-section-title">Endereço</div>
        <div class="field">
          <label>Endereço</label>
          <InputText v-model="form.endereco" />
        </div>
        <div class="field-row">
          <div class="field flex-2">
            <label>Cidade</label>
            <InputText v-model="form.cidade" />
          </div>
          <div class="field flex-1">
            <label>Estado</label>
            <InputText v-model="form.estado" maxlength="2" />
          </div>
          <div class="field flex-1">
            <label>CEP</label>
            <InputText v-model="form.cep" />
          </div>
        </div>

        <div class="field">
          <label>Observações</label>
          <Textarea v-model="form.observacoes" rows="2" class="w-full" />
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button type="submit" :label="editingCliente ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import api from '../services/api'

const toast = useToast()
const confirm = useConfirm()

const clientes = ref([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const total = ref(0)
const skip = ref(0)
const limit = 20
const dialogVisible = ref(false)
const editingCliente = ref(null)

const defaultForm = {
  razao_social: '', nome_fantasia: '', cnpj: '', cpf: '',
  email: '', telefone: '', contato_nome: '', contato_cargo: '',
  endereco: '', cidade: '', estado: '', cep: '', observacoes: '',
}

const form = reactive({ ...defaultForm })

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { skip.value = 0; fetchClientes() }, 300)
}

async function fetchClientes() {
  loading.value = true
  try {
    const params = { skip: skip.value, limit }
    if (search.value) params.search = search.value
    const { data } = await api.get('/api/clientes', { params })
    clientes.value = data.items
    total.value = data.total
  } catch {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar clientes', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openDialog(cliente = null) {
  editingCliente.value = cliente
  if (cliente) {
    Object.keys(defaultForm).forEach(key => {
      form[key] = cliente[key] || ''
    })
  } else {
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingCliente.value) {
      await api.put(`/api/clientes/${editingCliente.value.id}`, form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Cliente atualizado', life: 3000 })
    } else {
      await api.post('/api/clientes', form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Cliente cadastrado', life: 3000 })
    }
    dialogVisible.value = false
    await fetchClientes()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.response?.data?.detail || 'Erro ao salvar', life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(cliente) {
  confirm.require({
    message: `Deseja excluir o cliente "${cliente.nome_fantasia || cliente.razao_social}"?`,
    header: 'Confirmar Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Excluir',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/clientes/${cliente.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Cliente excluído', life: 3000 })
        await fetchClientes()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao excluir', life: 3000 })
      }
    },
  })
}

onMounted(fetchClientes)
</script>

<style scoped>
.clientes-view {
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
  gap: 1rem;
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

.w-full { width: 100%; }

.search-stats {
  font-size: 0.8rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.table-card {
  padding: 0;
  overflow: hidden;
}

.cell-primary {
  font-weight: 600;
  font-size: 0.9rem;
}

.cell-secondary {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.mono {
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
}

.text-muted {
  color: var(--text-muted);
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
  gap: 0.75rem;
  color: var(--text-muted);
}

.empty-table i {
  font-size: 2rem;
}

/* Pagination */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.pagination-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* Dialog */
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 0.5rem;
}

.form-section-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary-400);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border-color);
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
.field :deep(.p-textarea) {
  width: 100%;
}

.field-row {
  display: flex;
  gap: 1rem;
}

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
