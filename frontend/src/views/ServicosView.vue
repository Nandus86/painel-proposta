<template>
  <div class="servicos-view fade-in">
    <div class="page-header">
      <div>
        <h2>Serviços e Produtos</h2>
        <p class="page-desc">Gerencie o catálogo para inclusão nas propostas</p>
      </div>
      <Button label="Novo Item" icon="pi pi-plus" @click="openDialog()" />
    </div>

    <!-- Filters & Search -->
    <div class="filters-bar glass">
      <span class="p-input-icon-left flex-1">
        <i class="pi pi-search"></i>
        <InputText v-model="search" placeholder="Buscar por nome ou descrição..." class="w-full" @input="debouncedFetch" />
      </span>
      <div class="filter-group">
        <Select
          v-model="categoriaFilter"
          :options="categorias"
          optionLabel="nome"
          optionValue="id"
          placeholder="Todas as Categorias"
          showClear
          @change="fetchServicos()"
          class="category-select"
        />
      </div>
      <div class="search-stats" v-if="total > 0">
        <span>{{ total }} ite{{ total !== 1 ? 'ns' : 'm' }}</span>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card glass">
      <DataTable
        :value="servicos"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
      >
        <Column field="nome" header="Item" sortable>
          <template #body="{ data }">
            <div class="cell-primary">{{ data.nome }}</div>
            <div class="cell-secondary text-truncate" style="max-width: 250px" v-if="data.descricao_padrao">
              {{ data.descricao_padrao }}
            </div>
          </template>
        </Column>
        <Column field="tipo" header="Tipo">
          <template #body="{ data }">
            <span class="type-badge" :class="data.tipo">{{ formatTipo(data.tipo) }}</span>
          </template>
        </Column>
        <Column header="Categoria">
          <template #body="{ data }">
            <span class="category-tag" v-if="data.categoria">{{ data.categoria.nome }}</span>
            <span class="text-muted" v-else>—</span>
          </template>
        </Column>
        <Column field="preco_base" header="Preço Base">
          <template #body="{ data }">
            <span class="price">{{ formatCurrency(data.preco_base) }}</span>
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
              <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" @click="openDialog(data)" />
              <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="confirmDelete(data)" />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-table">
            <i class="pi pi-box"></i>
            <p>Nenhum item encontrado no catálogo</p>
            <Button label="Cadastrar Primeiro Item" icon="pi pi-plus" size="small" @click="openDialog()" />
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Pagination -->
    <div class="pagination-bar" v-if="total > limit">
      <Button icon="pi pi-angle-left" severity="secondary" text :disabled="skip === 0" @click="skip = Math.max(0, skip - limit); fetchServicos()" />
      <span class="pagination-info">{{ skip + 1 }}–{{ Math.min(skip + limit, total) }} de {{ total }}</span>
      <Button icon="pi pi-angle-right" severity="secondary" text :disabled="skip + limit >= total" @click="skip += limit; fetchServicos()" />
    </div>

    <!-- Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="editingServico ? 'Editar Item' : 'Novo Item'" modal :style="{ width: '600px' }">
      <form @submit.prevent="handleSave" class="dialog-form">
        <div class="field-row">
          <div class="field flex-2">
            <label>Nome *</label>
            <InputText v-model="form.nome" required autofocus />
          </div>
          <div class="field flex-1">
            <label>Tipo *</label>
            <Select v-model="form.tipo" :options="tiposOptions" optionLabel="label" optionValue="value" required />
          </div>
        </div>

        <div class="field">
          <label>Categoria</label>
          <Select
            v-model="form.categoria_id"
            :options="categoriasAtivas"
            optionLabel="nome"
            optionValue="id"
            placeholder="Selecione..."
            showClear
          />
        </div>

        <div class="field">
          <label>Descrição Padrão para Proposta</label>
          <Textarea v-model="form.descricao_padrao" rows="3" />
        </div>

        <div class="field mt-1">
          <label class="text-xs text-primary mb-1"><i class="pi pi-sparkles"></i> Instruções para a IA (Opcional)</label>
          <Textarea v-model="form.instrucoes_ia" rows="2" placeholder="Ex: Fale que o serviço X tem garantia de 1 ano" />
          <small class="text-muted">Essas instruções serão lidas pela IA quando você for gerar uma Proposta incluindo este serviço.</small>
        </div>

        <div class="field-row">
          <div class="field">
            <label>Preço Base (R$)</label>
            <InputText v-model.number="form.preco_base" type="number" step="0.01" min="0" />
          </div>
          <div class="field">
            <label>Custo Base (R$)</label>
            <InputText v-model.number="form.custo_base" type="number" step="0.01" min="0" />
          </div>
        </div>

        <div class="field-checkbox">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.ativo" class="p-checkbox" />
            Item ativo
          </label>
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button type="submit" :label="editingServico ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import api from '../services/api'

const toast = useToast()
const confirm = useConfirm()

const servicos = ref([])
const categorias = ref([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const categoriaFilter = ref(null)
const total = ref(0)
const skip = ref(0)
const limit = 20
const dialogVisible = ref(false)
const editingServico = ref(null)

const tiposOptions = [
  { label: 'Serviço', value: 'servico' },
  { label: 'Produto', value: 'produto' },
  { label: 'Recorrente', value: 'recorrente' },
]

const categoriasAtivas = computed(() => categorias.value.filter(c => c.ativa))

const defaultForm = {
  nome: '', tipo: 'servico', categoria_id: null,
  descricao_padrao: '', instrucoes_ia: '', preco_base: 0, custo_base: 0, ativo: true
}
const form = reactive({ ...defaultForm })

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { skip.value = 0; fetchServicos() }, 300)
}

async function fetchDependencies() {
  try {
    const { data } = await api.get('/api/categorias', { params: { limit: 1000 } })
    categorias.value = data.items
  } catch (e) {
    console.error("Failed to fetch categorias", e)
  }
}

async function fetchServicos() {
  loading.value = true
  try {
    const params = { skip: skip.value, limit }
    if (search.value) params.search = search.value
    if (categoriaFilter.value) params.categoria_id = categoriaFilter.value
    
    const { data } = await api.get('/api/servicos', { params })
    servicos.value = data.items
    total.value = data.total
  } catch {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar catálogo', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openDialog(item = null) {
  editingServico.value = item
  if (item) {
    Object.keys(defaultForm).forEach(key => form[key] = item[key])
  } else {
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingServico.value) {
      await api.put(`/api/servicos/${editingServico.value.id}`, form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item atualizado', life: 3000 })
    } else {
      await api.post('/api/servicos', form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item cadastrado', life: 3000 })
    }
    dialogVisible.value = false
    await fetchServicos()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar', life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(item) {
  confirm.require({
    message: `Deseja excluir "${item.nome}"?`,
    header: 'Confirmar Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Excluir',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/servicos/${item.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item excluído', life: 3000 })
        await fetchServicos()
      } catch {
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao excluir.', life: 4000 })
      }
    },
  })
}

function formatTipo(tipo) {
  return tiposOptions.find(t => t.value === tipo)?.label || tipo
}

function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)
}

onMounted(() => {
  fetchDependencies()
  fetchServicos()
})
</script>

<style scoped>
.servicos-view { display: flex; flex-direction: column; gap: 1.25rem; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-header h2 { font-size: 1.35rem; font-weight: 700; }
.page-desc { color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }

.filters-bar { padding: 0.75rem 1rem; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.filters-bar .p-input-icon-left { position: relative; min-width: 250px; }
.filters-bar .p-input-icon-left > i { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); z-index: 1; }
.filters-bar :deep(.p-inputtext) { padding-left: 2.25rem !important; }
.flex-1 { flex: 1; }
.w-full { width: 100%; }

.category-select { min-width: 200px; }
.search-stats { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }

.table-card { padding: 0; overflow: hidden; }

.cell-primary { font-weight: 600; font-size: 0.9rem; }
.cell-secondary { font-size: 0.8rem; color: var(--text-muted); }
.text-truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.text-muted { color: var(--text-muted); }
.price { font-family: 'Courier New', Courier, monospace; font-weight: 600; }

.type-badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 510; text-transform: uppercase; letter-spacing: 0.5px; }
.type-badge.servico { background: rgba(var(--primary-rgb), 0.06); color: var(--primary-600); border: 1px solid rgba(var(--primary-rgb), 0.15); }
.type-badge.produto { background: rgba(39, 166, 68, 0.04); color: var(--accent-green); border: 1px solid rgba(39, 166, 68, 0.12); }
.type-badge.recorrente { background: rgba(245, 158, 11, 0.04); color: var(--warning-400); border: 1px solid rgba(245, 158, 11, 0.12); }

.category-tag { font-size: 0.75rem; background: var(--bg-card); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid var(--border-color); }

.status-badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 510; border: 1px solid transparent; }
.status-badge.active { background: rgba(39, 166, 68, 0.04); color: var(--accent-green); border-color: rgba(39, 166, 68, 0.12); }
.status-badge.inactive { background: rgba(239, 68, 68, 0.04); color: var(--danger-400); border-color: rgba(239, 68, 68, 0.12); }

.action-buttons { display: flex; gap: 0.25rem; }
.empty-table { display: flex; flex-direction: column; align-items: center; padding: 3rem; gap: 0.75rem; color: var(--text-muted); }
.empty-table i { font-size: 2rem; }

.pagination-bar { display: flex; align-items: center; justify-content: center; gap: 0.75rem; }
.pagination-info { font-size: 0.85rem; color: var(--text-secondary); }

.dialog-form { display: flex; flex-direction: column; gap: 1rem; padding-top: 0.5rem; }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); }
.field :deep(.p-inputtext), .field :deep(.p-textarea), .field :deep(.p-select) { width: 100%; }
.field-row { display: flex; gap: 1rem; }
.flex-2 { flex: 2; }
.field-checkbox { display: flex; align-items: center; margin-top: 0.5rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer; }

.dialog-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem; }
</style>
