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

    <Dialog v-model:visible="dialogVisible" :header="editingModelo ? 'Editar Modelo' : 'Novo Modelo'" modal :style="{ width: '960px' }">
      <form @submit.prevent="handleSave" class="dialog-form">
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
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
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

const TAG_RE = /\{\{[a-z][a-z0-9_]*\}\}/g

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

function markdownToHtml(text) {
  if (!text) return ''
  return text.replace(TAG_RE, (match) => {
    const inner = match.slice(2, -2)
    return `<span class="var-badge" contenteditable="false" data-tag="${match}" data-inner="${inner}" style="background:rgba(59,130,246,0.12);color:#3b82f6;border:1px solid rgba(59,130,246,0.3);font-weight:600;border-radius:4px;padding:0 6px;margin:0 1px;font-family:monospace;font-size:0.85em;cursor:default;display:inline-block;white-space:nowrap;">${match}</span>`
  })
}

function htmlToMarkdown() {
  if (!editorRef.value) return ''
  let html = editorRef.value.innerHTML

  html = html.replace(/<span[^>]*data-tag="([^"]*)"[^>]*>.*?<\/span>/g, (_, tag) => tag)

  html = html.replace(/<br\s*\/?>/gi, '\n')
  html = html.replace(/<div>/gi, '').replace(/<\/div>/gi, '\n')
  html = html.replace(/<\/p>/gi, '\n')
  html = html.replace(/<[^>]*>/g, '')

  return html.replace(/\n{3,}/g, '\n\n').trim()
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
  if (tag && TAG_RE.test(tag)) {
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
  form.conteudo = htmlToMarkdown()
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
  } else {
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
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
</style>
