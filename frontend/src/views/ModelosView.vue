<template>
  <div class="modelos-view fade-in">
    <div class="page-header">
      <div>
        <h2>Modelos de Proposta</h2>
        <p class="page-desc">Gerencie os moldes de proposta com variáveis dinâmicas para preenchimento pela IA</p>
      </div>
      <Button label="Novo Modelo" icon="pi pi-plus" @click="openDialog()" />
    </div>

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

    <Dialog v-model:visible="dialogVisible" :header="editingModelo ? 'Editar Modelo' : 'Novo Modelo'" modal :style="{ width: '1000px', maxWidth: '95vw' }">
      <form @submit.prevent="handleSave" class="dialog-form">
        <!-- Card do Assistente de IA -->
        <div class="ai-assistant-card">
          <div class="ai-assistant-header" @click="aiPanelOpen = !aiPanelOpen">
            <div class="ai-title">
              <i class="pi pi-sparkles ai-sparkle-icon"></i>
              <div>
                <span class="ai-heading">Criar Modelo com Inteligência Artificial</span>
                <span class="ai-subheading">A IA redige o escopo e posiciona as variáveis dinâmicas automaticamente</span>
              </div>
            </div>
            <div class="ai-header-right">
              <span class="ai-credits-pill" v-if="aiCredits && aiCredits.limit > 0">
                <i class="pi pi-bolt"></i> {{ aiCredits.remaining }} / {{ aiCredits.limit }} créditos hoje
              </span>
              <Button 
                :icon="aiPanelOpen ? 'pi pi-chevron-up' : 'pi pi-sparkles'" 
                :label="aiPanelOpen ? 'Ocultar' : 'Usar IA'"
                size="small"
                severity="help"
                :outlined="!aiPanelOpen"
                @click.stop="aiPanelOpen = !aiPanelOpen"
              />
            </div>
          </div>

          <div v-if="aiPanelOpen" class="ai-assistant-body">
            <div class="field">
              <label class="ai-field-label">O que este modelo de proposta deve conter?</label>
              <Textarea
                v-model="aiBriefing"
                rows="3"
                placeholder="Ex: Crie um modelo para manutenção preventiva de ar-condicionado corporativo com visitas mensais, SLA de 4 horas em chamados urgentes, garantia de peças e faturamento a cada 30 dias..."
                class="w-full ai-textarea"
                :disabled="generatingAI"
              />
            </div>

            <div class="ai-options-row">
              <div class="ai-option-item">
                <label>Segmento / Tipo:</label>
                <Select
                  v-model="aiTipo"
                  :options="tipoOptions"
                  optionLabel="label"
                  optionValue="value"
                  size="small"
                  class="ai-select"
                  :disabled="generatingAI"
                />
              </div>

              <div class="ai-option-item">
                <label>Tom de Voz:</label>
                <Select
                  v-model="aiTom"
                  :options="tomOptions"
                  optionLabel="label"
                  optionValue="value"
                  size="small"
                  class="ai-select"
                  :disabled="generatingAI"
                />
              </div>

              <div class="ai-generate-action">
                <Button
                  label="Gerar Modelo com IA"
                  icon="pi pi-sparkles"
                  severity="help"
                  :loading="generatingAI"
                  :disabled="!aiBriefing.trim() || (aiCredits && aiCredits.remaining <= 0)"
                  @click="gerarModeloComIA"
                  class="btn-gerar-ia"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="field">
          <label for="titulo">Título do Modelo *</label>
          <InputText id="titulo" v-model="form.titulo" required placeholder="Ex: Modelo de Serviços de TI" autofocus />
        </div>

        <div class="editor-layout">
          <div class="editor-main" @dragover.prevent @drop.prevent="onDrop">
            <label>Conteúdo do Modelo *</label>
            <div
              ref="editorRef"
              class="model-editor"
              contenteditable="true"
              @input="onEditorInput"
              @paste="onPaste"
              @keydown.enter.prevent="onEnter"
              @keydown.backspace="onBackspace"
            >
            </div>
            <small class="helper-text">
              Arraste variáveis da paleta lateral ou digite o texto do modelo. Variáveis são inseridas como blocos coloridos.
            </small>
          </div>
          <div class="editor-sidebar">
            <VariablePalette @insert-var="insertVariable" />
          </div>
        </div>

        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" outlined @click="dialogVisible = false; cleanEditorState()" />
          <Button type="submit" :label="editingModelo ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="saving" class="save-btn" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { htmlToMarkdown, isVariableTag, markdownToHtml } from '@/utils/varEditor'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import VariablePalette from '../components/VariablePalette.vue'
import api from '../services/api'

const VAR_COLORS = {
  cliente: '#3b82f6',
  empresa: '#f39c12',
  proposta: '#16a34a',
  itens: '#8b5cf6',
  vendedor: '#ec4899',
  datas: '#06b6d4',
  custom: '#a855f7',
}


const toast = useToast()
const confirm = useConfirm()

const modelos = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingModelo = ref(null)
const editorRef = ref(null)

const defaultForm = { titulo: '', conteudo: '' }
const form = reactive({ ...defaultForm })

// Assistente IA
const aiPanelOpen = ref(false)
const aiBriefing = ref('')
const aiTom = ref('Profissional e Persuasivo')
const aiTipo = ref('Livre')
const generatingAI = ref(false)
const aiCredits = ref({ used: 0, limit: 0, remaining: 0 })

const tomOptions = [
  { label: 'Profissional e Persuasivo', value: 'Profissional e Persuasivo' },
  { label: 'Formal e Técnico', value: 'Formal e Técnico' },
  { label: 'Consultivo e Estratégico', value: 'Consultivo e Estratégico' },
  { label: 'Objetivo e Direto', value: 'Objetivo e Direto' },
  { label: 'Comercial e Enérgico', value: 'Comercial e Enérgico' },
]

const tipoOptions = [
  { label: 'Livre / Conforme Instruções', value: 'Livre' },
  { label: 'Prestação de Serviços', value: 'Serviço' },
  { label: 'Venda / Fornecimento de Produtos', value: 'Produto' },
  { label: 'Parceria / Acordo Comercial', value: 'Comercial' },
  { label: 'Consultoria / Assessoria', value: 'Consultoria' },
  { label: 'Tecnologia / Software / TI', value: 'Tecnologia' },
]

async function fetchAICredits() {
  try {
    const { data } = await api.get('/api/ai/credits')
    aiCredits.value = data
  } catch (e) {
    // Silencioso se IA não configurada
  }
}

async function gerarModeloComIA() {
  const briefing = aiBriefing.value.trim()
  if (!briefing) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Informe as instruções para a IA criar o modelo.', life: 3000 })
    return
  }

  generatingAI.value = true
  try {
    const { data } = await api.post('/api/ai/modelo/gerar', {
      instrucoes: briefing,
      tom: aiTom.value,
      tipo: aiTipo.value !== 'Livre' ? aiTipo.value : null
    })

    if (data.titulo && (!form.titulo || form.titulo.trim() === '' || !editingModelo.value)) {
      form.titulo = data.titulo
    }

    form.conteudo = data.conteudo
    setEditorContent(data.conteudo)

    if (data.creditos_restantes !== undefined) {
      aiCredits.value.remaining = data.creditos_restantes
    }

    toast.add({
      severity: 'success',
      summary: 'Modelo Criado!',
      detail: 'A IA estruturou o modelo e posicionou as variáveis dinâmicas.',
      life: 4000
    })
  } catch (error) {
    const msg = error.response?.data?.detail || 'Erro ao gerar modelo com IA.'
    toast.add({ severity: 'error', summary: 'Erro na IA', detail: msg, life: 5000 })
  } finally {
    generatingAI.value = false
  }
}

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



function setEditorContent(markdown) {
  if (!editorRef.value) return
  editorRef.value.innerHTML = ''
  const lines = markdown.split('\n')
  lines.forEach((line, i) => {
    const span = document.createElement('div')
    span.innerHTML = markdownToHtml(line) || '<br>'
    editorRef.value.appendChild(span)
  })
}

function insertVariable(tag) {
  if (!editorRef.value) return

  const sel = window.getSelection()
  let container = editorRef.value
  let cursorNode = null
  let cursorOffset = 0

  if (sel.rangeCount > 0) {
    const range = sel.getRangeAt(0)
    if (editorRef.value.contains(range.commonAncestorContainer)) {
      cursorNode = range.startContainer
      cursorOffset = range.startOffset
    }
  }

  if (!cursorNode || !editorRef.value.contains(cursorNode)) {
    const lastChild = editorRef.value.lastChild
    if (lastChild) {
      const textNode = document.createTextNode(' ')
      lastChild.appendChild(textNode)
      const range = document.createRange()
      range.setStart(textNode, 1)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
      cursorNode = textNode
      cursorOffset = 1
    }
  }

  if (cursorNode && editorRef.value.contains(cursorNode)) {
    const badgeDiv = document.createElement('span')
    badgeDiv.innerHTML = markdownToHtml(tag)
    const badge = badgeDiv.firstChild

    const range = document.createRange()
    range.setStart(cursorNode, cursorOffset)
    range.collapse(true)

    range.insertNode(badge)

    const space = document.createTextNode(' ')
    range.setStartAfter(badge)
    range.insertNode(space)

    range.setStartAfter(space)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
  }
}

function onDrop(event) {
  event.preventDefault()
  const tag = event.dataTransfer.getData('text/plain')
  if (tag && isVariableTag(tag)) {
    editorRef.value.focus()

    const x = event.clientX
    const y = event.clientY
    if (document.caretRangeFromPoint) {
      const range = document.caretRangeFromPoint(x, y)
      if (range) {
        const sel = window.getSelection()
        sel.removeAllRanges()
        sel.addRange(range)
      }
    }

    insertVariable(tag)
  }
}

function onEditorInput() {
  form.conteudo = htmlToMarkdown(editorRef.value)
}

function onPaste(event) {
  event.preventDefault()
  const text = event.clipboardData.getData('text/plain')
  document.execCommand('insertText', false, text)
}

function onEnter(event) {
  event.preventDefault()
  document.execCommand('insertLineBreak')
}

function onBackspace(event) {
  const sel = window.getSelection()
  if (sel.rangeCount === 0) return

  const range = sel.getRangeAt(0)
  if (range.collapsed) {
    const node = range.startContainer
    if (node.nodeType === 3 && range.startOffset === 0) {
      const prev = node.previousSibling
      if (prev && prev.classList && prev.classList.contains('var-badge')) {
        event.preventDefault()
        prev.remove()
        onEditorInput()
      }
    }
  }
}

function cleanEditorState() {
  editorRef.value = null
}

function openDialog(item = null) {
  editingModelo.value = item
  if (item) {
    form.titulo = item.titulo
    form.conteudo = item.conteudo
    aiPanelOpen.value = false
  } else {
    Object.assign(form, defaultForm)
    aiBriefing.value = ''
    aiPanelOpen.value = true
  }
  dialogVisible.value = true
  fetchAICredits()
  nextTick(() => {
    if (editorRef.value) {
      setEditorContent(form.conteudo)
    }
  })
}

async function handleSave() {
  saving.value = true
  try {
    if (editingModelo.value) {
      await api.put(`/api/modelos/${editingModelo.value.id}`, { ...form })
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Modelo de proposta atualizado', life: 3000 })
    } else {
      await api.post('/api/modelos', { ...form })
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Modelo de proposta cadastrado', life: 3000 })
    }
    dialogVisible.value = false
    editorRef.value = null
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
  return val.replace(/[{}]/g, '').substring(0, 120) + (val.length > 120 ? '...' : '')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(() => {
  fetchModelos()
  fetchAICredits()
})
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

.editor-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 1rem;
  min-height: 320px;
}

.editor-main {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.editor-main label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.model-editor {
  flex: 1;
  min-height: 280px;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: 0.75rem;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 0.9rem;
  line-height: 1.7;
  outline: none;
  transition: border-color var(--transition-fast);
}

.model-editor:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.model-editor:empty::before {
  content: 'Digite o conteúdo do modelo aqui...';
  color: var(--text-muted);
  font-style: italic;
}

.editor-sidebar {
  display: flex;
}

.helper-text {
  font-size: 0.7rem;
  color: var(--text-muted);
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

/* Assistente IA */
.ai-assistant-card {
  border: 1px solid rgba(168, 85, 247, 0.35);
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(99, 102, 241, 0.05) 100%);
  border-radius: var(--border-radius-md);
  overflow: hidden;
  margin-bottom: 0.5rem;
  transition: all var(--transition-fast);
}

.ai-assistant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  cursor: pointer;
  background: rgba(168, 85, 247, 0.05);
}

.ai-assistant-header:hover {
  background: rgba(168, 85, 247, 0.1);
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ai-sparkle-icon {
  font-size: 1.35rem;
  color: #a855f7;
}

.ai-heading {
  display: block;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.ai-subheading {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}

.ai-header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ai-credits-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.ai-assistant-body {
  padding: 1rem;
  border-top: 1px solid rgba(168, 85, 247, 0.2);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.ai-field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0.35rem;
}

.ai-textarea {
  border-color: rgba(168, 85, 247, 0.3) !important;
  font-size: 0.88rem;
  line-height: 1.5;
}

.ai-textarea:focus {
  border-color: #a855f7 !important;
  box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.2) !important;
}

.ai-options-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.85rem;
}

.ai-option-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 180px;
}

.ai-option-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}

.ai-select {
  width: 100%;
}

.ai-generate-action {
  margin-left: auto;
}

.btn-gerar-ia {
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%) !important;
  border: none !important;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.3);
}

.btn-gerar-ia:hover {
  background: linear-gradient(135deg, #9333ea 0%, #6d28d9 100%) !important;
}
</style>
