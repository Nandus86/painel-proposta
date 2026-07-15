<template>
  <div class="categorias-view fade-in">
    <div class="page-header">
      <div>
        <h2>Categorias</h2>
        <p class="page-desc">Gerencie as categorias de serviços e produtos</p>
      </div>
      <Button label="Nova Categoria" icon="pi pi-plus" @click="openDialog()" />
    </div>

    <!-- Search -->
    <div class="search-bar glass">
      <span class="p-input-icon-left w-full">
        <i class="pi pi-search"></i>
        <InputText v-model="search" placeholder="Buscar categoria..." class="w-full" @input="debouncedFetch" />
      </span>
      <div class="search-stats" v-if="total > 0">
        <span>{{ total }} categoria{{ total !== 1 ? 's' : '' }}</span>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card glass">
      <DataTable
        :value="categorias"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
      >
        <Column field="nome" header="Nome" sortable>
          <template #body="{ data }">
            <div class="cell-primary">{{ data.nome }}</div>
            <div class="cell-secondary text-truncate" style="max-width: 300px" v-if="data.descricao">{{ data.descricao }}</div>
          </template>
        </Column>
        <Column field="ativa" header="Status">
          <template #body="{ data }">
            <span class="status-badge" :class="data.ativa ? 'active' : 'inactive'">
              {{ data.ativa ? 'Ativa' : 'Inativa' }}
            </span>
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
            <i class="pi pi-tags"></i>
            <p>Nenhuma categoria encontrada</p>
            <Button label="Criar Primeira Categoria" icon="pi pi-plus" size="small" @click="openDialog()" />
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Pagination -->
    <div class="pagination-bar" v-if="total > limit">
      <Button icon="pi pi-angle-left" severity="secondary" text :disabled="skip === 0" @click="skip = Math.max(0, skip - limit); fetchCategorias()" />
      <span class="pagination-info">{{ skip + 1 }}–{{ Math.min(skip + limit, total) }} de {{ total }}</span>
      <Button icon="pi pi-angle-right" severity="secondary" text :disabled="skip + limit >= total" @click="skip += limit; fetchCategorias()" />
    </div>

    <!-- Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="editingCategoria ? 'Editar Categoria' : 'Nova Categoria'" modal :style="{ width: '450px' }">
      <form @submit.prevent="handleSave" class="dialog-form">
        <div class="field">
          <label>Nome da Categoria *</label>
          <InputText v-model="form.nome" required autofocus />
        </div>
        <div class="field">
          <label>Descrição</label>
          <Textarea v-model="form.descricao" rows="3" />
        </div>
        <div class="field-checkbox">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.ativa" class="p-checkbox" />
            Categoria ativa
          </label>
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button type="submit" :label="editingCategoria ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" />
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

const categorias = ref([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const total = ref(0)
const skip = ref(0)
const limit = 20
const dialogVisible = ref(false)
const editingCategoria = ref(null)

const defaultForm = { nome: '', descricao: '', ativa: true }
const form = reactive({ ...defaultForm })

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { skip.value = 0; fetchCategorias() }, 300)
}

async function fetchCategorias() {
  loading.value = true
  try {
    const params = { skip: skip.value, limit }
    if (search.value) params.search = search.value
    const { data } = await api.get('/api/categorias', { params })
    categorias.value = data.items
    total.value = data.total
  } catch {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar categorias', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openDialog(cat = null) {
  editingCategoria.value = cat
  if (cat) {
    Object.keys(defaultForm).forEach(key => form[key] = cat[key])
  } else {
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingCategoria.value) {
      await api.put(`/api/categorias/${editingCategoria.value.id}`, form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Categoria atualizada', life: 3000 })
    } else {
      await api.post('/api/categorias', form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Categoria criada', life: 3000 })
    }
    dialogVisible.value = false
    await fetchCategorias()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar', life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(cat) {
  confirm.require({
    message: `Deseja excluir a categoria "${cat.nome}"?`,
    header: 'Confirmar Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Excluir',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/categorias/${cat.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Categoria excluída', life: 3000 })
        await fetchCategorias()
      } catch {
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não é possível excluir categorias em uso.', life: 4000 })
      }
    },
  })
}

onMounted(fetchCategorias)
</script>

<style scoped>
.categorias-view { display: flex; flex-direction: column; gap: 1.25rem; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-header h2 { font-size: 1.35rem; font-weight: 700; }
.page-desc { color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }

.search-bar { padding: 0.75rem 1rem; display: flex; align-items: center; gap: 1rem; }
.search-bar .p-input-icon-left { width: 100%; position: relative; }
.search-bar .p-input-icon-left > i { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); z-index: 1; }
.search-bar :deep(.p-inputtext) { padding-left: 2.25rem !important; }
.w-full { width: 100%; }

.search-stats { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }
.table-card { padding: 0; overflow: hidden; }

.cell-primary { font-weight: 600; font-size: 0.9rem; }
.cell-secondary { font-size: 0.8rem; color: var(--text-muted); }
.text-truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.status-badge { padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.status-badge.active { background: rgba(16, 185, 129, 0.15); color: var(--accent-400); }
.status-badge.inactive { background: rgba(244, 63, 94, 0.15); color: var(--danger-400); }

.action-buttons { display: flex; gap: 0.25rem; }
.empty-table { display: flex; flex-direction: column; align-items: center; padding: 3rem; gap: 0.75rem; color: var(--text-muted); }
.empty-table i { font-size: 2rem; }

.pagination-bar { display: flex; align-items: center; justify-content: center; gap: 0.75rem; }
.pagination-info { font-size: 0.85rem; color: var(--text-secondary); }

.dialog-form { display: flex; flex-direction: column; gap: 1rem; padding-top: 0.5rem; }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); }
.field :deep(.p-inputtext), .field :deep(.p-textarea) { width: 100%; }
.field-checkbox { display: flex; align-items: center; margin-top: 0.5rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer; }

.dialog-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }
</style>
