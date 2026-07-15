<template>
  <div class="modelos-view fade-in">
    <div class="page-header">
      <div>
        <h2>Modelos de Proposta</h2>
        <p class="page-desc">Gerencie os moldes de proposta e termos padrões para o preenchimento da IA</p>
      </div>
      <Button label="Novo Modelo" icon="pi pi-plus" @click="openDialog()" />
    </div>

    <!-- Table / List -->
    <div class="table-card glass mt-4">
      <DataTable
        :value="modelos"
        :loading="loading"
        stripedRows
        responsiveLayout="scroll"
      >
        <Column field="titulo" header="Título" sortable>
          <template #body="{ data }">
            <div class="cell-primary">{{ data.titulo }}</div>
            <div class="cell-secondary text-truncate" style="max-width: 400px">
              {{ cleanSnippet(data.conteudo) }}
            </div>
          </template>
        </Column>
        <Column header="Última Atualização" sortable field="updated_at" style="width: 200px">
          <template #body="{ data }">
            <span class="text-secondary">{{ formatDate(data.updated_at) }}</span>
          </template>
        </Column>
        <Column header="Ações" style="width: 150px">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" @click="openDialog(data)" />
              <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="confirmDelete(data)" />
            </div>
          </template>
        </Column>

        <template #empty>
          <div class="empty-table" v-if="!loading">
            <i class="pi pi-copy"></i>
            <p>Nenhum modelo de proposta cadastrado</p>
            <Button label="Criar Primeiro Modelo" icon="pi pi-plus" size="small" @click="openDialog()" />
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Form Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="editingModelo ? 'Editar Modelo' : 'Novo Modelo'" modal :style="{ width: '800px' }">
      <form @submit.prevent="handleSave" class="dialog-form">
        <div class="field">
          <label for="titulo">Título do Modelo *</label>
          <InputText id="titulo" v-model="form.titulo" required placeholder="Ex: Modelo de Serviços de TI" autofocus />
        </div>

        <div class="grid">
          <!-- Editor Column -->
          <div class="col-12 lg:col-8 field">
            <label for="conteudo">Conteúdo do Modelo *</label>
            <Textarea
              id="conteudo"
              v-model="form.conteudo"
              required
              rows="12"
              class="w-full editor-textarea"
              placeholder="Digite a estrutura da sua proposta. Use as tags explicadas ao lado para dados dinâmicos..."
            />
          </div>
          
          <!-- Helper Variables Column -->
          <div class="col-12 lg:col-4 helper-column">
            <div class="helper-box">
              <h4>Variáveis Dinâmicas</h4>
              <p>Insira essas tags exatas no seu texto. A IA as substituirá automaticamente pelos dados do formulário:</p>
              
              <ul class="variables-list">
                <li>
                  <code v-pre>{{cliente}}</code>
                  <span>Razão social / Nome do cliente</span>
                </li>
                <li>
                  <code v-pre>{{valor_total}}</code>
                  <span>Valor final da proposta</span>
                </li>
                <li>
                  <code v-pre>{{itens}}</code>
                  <span>Listagem descritiva de itens cotações</span>
                </li>
                <li>
                  <code v-pre>{{empresa}}</code>
                  <span>Nome fantasia da sua empresa</span>
                </li>
                <li>
                  <code v-pre>{{telefone}}</code>
                  <span>Telefone da sua empresa</span>
                </li>
                <li>
                  <code v-pre>{{email}}</code>
                  <span>E-mail da sua empresa</span>
                </li>
              </ul>

              <div class="helper-tip mt-3">
                <i class="pi pi-info-circle mr-1"></i>
                Você também pode escrever termos jurídicos, escopos de serviço padrão e cronogramas fixos que a IA irá preservar.
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false" />
          <Button type="submit" :label="editingModelo ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" class="save-btn" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import api from '../services/api'

const toast = useToast()
const confirm = useConfirm()

const modelos = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingModelo = ref(null)

const defaultForm = {
  titulo: '',
  conteudo: ''
}
const form = reactive({ ...defaultForm })

async function fetchModelos() {
  loading.value = true
  try {
    const { data } = await api.get('/api/modelos')
    modelos.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar modelos', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openDialog(item = null) {
  editingModelo.value = item
  if (item) {
    form.titulo = item.titulo
    form.conteudo = item.conteudo
  } else {
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingModelo.value) {
      await api.put(`/api/modelos/${editingModelo.value.id}`, form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Modelo de proposta atualizado', life: 3000 })
    } else {
      await api.post('/api/modelos', form)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Modelo de proposta cadastrado', life: 3000 })
    }
    dialogVisible.value = false
    await fetchModelos()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar modelo', life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(item) {
  confirm.require({
    message: `Deseja realmente excluir o modelo "${item.titulo}"?`,
    header: 'Confirmar Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Excluir',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/modelos/${item.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Modelo excluído', life: 3000 })
        await fetchModelos()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao excluir modelo', life: 3000 })
      }
    }
  })
}

function cleanSnippet(val) {
  if (!val) return ''
  // Strip code variables tags and return simple text summary
  return val.replace(/[{}]/g, '').substring(0, 120) + (val.length > 120 ? '...' : '')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(fetchModelos)
</script>

<style scoped>
.modelos-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
  margin-top: 0.15rem;
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.empty-table {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  gap: 0.75rem;
  color: var(--text-muted);
}

.empty-table i {
  font-size: 2rem;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-top: 0.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.editor-textarea {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
  line-height: 1.5;
}

.helper-column {
  padding-left: 1rem;
}

.helper-box {
  background: var(--surface-100);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 1rem;
}

.helper-box h4 {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.helper-box p {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 0.75rem;
}

.variables-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.variables-list li {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.variables-list code {
  font-family: 'Courier New', Courier, monospace;
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--primary-600);
}

.variables-list span {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.helper-tip {
  font-size: 0.7rem;
  color: var(--text-muted);
  line-height: 1.4;
  display: flex;
  align-items: flex-start;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.save-btn {
  background: var(--primary-500) !important;
  border-color: var(--primary-600) !important;
}

.save-btn:hover {
  background: var(--primary-600) !important;
}
</style>
