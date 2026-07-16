<template>
  <div class="configuracoes-view fade-in">
    <div class="page-header">
      <h2>Configurações do Sistema</h2>
      <p class="page-desc">Gerencie as preferências globais do painel e chaves de API</p>
    </div>

    <div class="form-card glass" v-if="config">
      <form @submit.prevent="handleSave">
        <Tabs value="geral">
          <TabList>
            <Tab value="geral"><i class="pi pi-cog mr-2"></i> Geral</Tab>
            <Tab value="emails"><i class="pi pi-envelope mr-2"></i> E-mails (SMTP)</Tab>
            <Tab value="email_template"><i class="pi pi-palette mr-2"></i> Modelo de E-mail</Tab>
            <Tab value="variaveis"><i class="pi pi-tags mr-2"></i> Variáveis</Tab>
          </TabList>
          
          <TabPanels>
            <TabPanel value="geral">
              <!-- Proposal Default Settings -->
              <div class="form-section">
                <h3 class="form-section-title">
                  <i class="pi pi-cog"></i>
                  Parâmetros Gerais de Propostas
                </h3>
                <p class="section-desc">Defina o prefixo, prazo de vencimento padrão e o modelo de texto base para novos rascunhos.</p>

                <div class="form-grid">
                  <div class="field">
                    <label>Prefixo de Numeração</label>
                    <InputText v-model="config.prefixo_proposta" :disabled="!authStore.isAdmin" placeholder="PROP" />
                  </div>
                  <div class="field">
                    <label>Validade Padrão (dias)</label>
                    <InputText v-model.number="config.validade_padrao_dias" :disabled="!authStore.isAdmin" type="number" min="1" />
                  </div>
                  <div class="field span-2">
                    <label>Modelo Padrão de Proposta</label>
                    <Textarea 
                      v-model="config.modelo_proposta_padrao" 
                      :disabled="!authStore.isAdmin" 
                      rows="6" 
                      class="w-full"
                      placeholder="Ex: Esta proposta é válida por X dias... Insira o modelo que deseja que carregue automaticamente em novas propostas." 
                    />
                    <small class="helper-text mt-1">
                      Este texto será carregado no campo "Observações/Notas" automaticamente ao criar uma nova proposta.
                    </small>
                  </div>
                </div>
              </div>
            </TabPanel>

            <TabPanel value="emails">
              <!-- SMTP Settings Section -->
              <div class="form-section">
                <h3 class="form-section-title">
                  <i class="pi pi-envelope"></i>
                  Envio de E-mails (SMTP)
                </h3>
                <p class="section-desc">Configure o servidor SMTP (ex: Google, Locaweb) para enviar e-mails em nome da sua empresa.</p>

                <div class="form-grid">
                  <div class="field">
                    <label>Servidor SMTP (Host)</label>
                    <InputText v-model="config.smtp_host" :disabled="!authStore.isAdmin" placeholder="smtp.gmail.com" />
                  </div>
                  <div class="field">
                    <label>Porta</label>
                    <InputText v-model.number="config.smtp_port" :disabled="!authStore.isAdmin" type="number" placeholder="587" />
                  </div>
                  <div class="field">
                    <label>Usuário / E-mail</label>
                    <InputText v-model="config.smtp_user" :disabled="!authStore.isAdmin" placeholder="seuemail@gmail.com" />
                  </div>
                  <div class="field">
                    <label>Senha / Senha de Aplicativo</label>
                    <div class="api-key-input-wrapper">
                      <div class="input-with-button">
                        <InputText
                          v-model="smtpPassword"
                          :type="showSmtpPwd ? 'text' : 'password'"
                          :placeholder="config.has_smtp_password ? '•••••••• (Salva e encriptada)' : 'Sua senha SMTP...'"
                          :disabled="!authStore.isAdmin"
                          class="w-full key-input"
                        />
                        <Button
                          type="button"
                          :icon="showSmtpPwd ? 'pi pi-eye-slash' : 'pi pi-eye'"
                          severity="secondary"
                          text
                          class="toggle-key-btn"
                          @click="showSmtpPwd = !showSmtpPwd"
                          v-tooltip.bottom="showSmtpPwd ? 'Ocultar senha' : 'Mostrar senha'"
                        />
                      </div>
                      <div class="key-status mt-2">
                        <span class="status-pill" :class="config.has_smtp_password ? 'aceita' : 'rascunho'">
                          <i :class="config.has_smtp_password ? 'pi pi-lock-open mr-1' : 'pi pi-lock mr-1'"></i>
                          {{ config.has_smtp_password ? 'Senha configurada e protegida' : 'Nenhuma senha configurada' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabPanel>

            <TabPanel value="email_template">
              <div class="form-section">
                <h3 class="form-section-title">
                  <i class="pi pi-palette"></i>
                  Modelo de E-mail Padrão
                </h3>
                <p class="section-desc">Personalize o e-mail que é enviado ao cliente quando você dispara uma proposta ou orçamento.</p>

                <div class="field mb-3">
                  <label>Assunto do E-mail</label>
                  <InputText 
                    v-model="config.email_assunto_padrao" 
                    :disabled="!authStore.isAdmin" 
                    placeholder="Ex: Proposta Comercial #{numero} - {empresa_razao_social}" 
                  />
                  <small class="helper-text">
                    Você pode usar variáveis aqui também.
                  </small>
                </div>

                <div class="editor-layout">
                  <div class="editor-main" @dragover.prevent @drop.prevent="onDropEmail">
                    <label>Corpo do E-mail (Markdown/HTML)</label>
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
                      Arraste variáveis da paleta lateral ou digite o texto do modelo.
                    </small>
                  </div>
                  <div class="editor-sidebar">
                    <VariablePalette @insert-var="insertVariable" />
                  </div>
                </div>
              </div>
            </TabPanel>

            <TabPanel value="variaveis">
              <div class="form-section">
                <h3 class="form-section-title">
                  <i class="pi pi-tags"></i>
                  Variáveis Customizadas
                </h3>
                <p class="section-desc">
                  Crie variáveis personalizadas para usar nos modelos de proposta. Use o formato
                  <code v-pre>{{nome_variavel}}</code>. Disponíveis na paleta do editor de modelos.
                </p>

                <div class="mb-3">
                  <Button label="Nova Variável" icon="pi pi-plus" size="small" @click="openVarDialog()" :disabled="!authStore.isAdmin" />
                </div>

                <DataTable :value="customVars" size="small" stripedRows v-if="customVars.length > 0">
                  <Column field="tag" header="Tag">
                    <template #body="{ data }">
                      <code class="var-tag-code">{{ data.tag }}</code>
                    </template>
                  </Column>
                  <Column field="nome" header="Nome" />
                  <Column field="valor_padrao" header="Valor Padrão (opcional)">
                    <template #body="{ data }">
                      <span v-if="data.valor_padrao" class="text-secondary">{{ data.valor_padrao }}</span>
                      <span v-else class="text-muted">—</span>
                    </template>
                  </Column>
                  <Column header="Ações" style="width: 120px">
                    <template #body="{ data }">
                      <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" @click="openVarDialog(data)" />
                      <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="deleteVar(data)" />
                    </template>
                  </Column>
                </DataTable>

                <div v-else class="empty-vars">
                  <i class="pi pi-info-circle"></i>
                  <span>Nenhuma variável customizada cadastrada. Crie variáveis para usar nos seus modelos.</span>
                </div>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>

        <!-- Save Button -->
        <div class="form-actions" v-if="authStore.isAdmin">
          <Button type="submit" label="Salvar Configurações" icon="pi pi-check" :loading="saving" class="save-btn" />
        </div>
      </form>
    </div>

    <div v-else class="loading-state">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Carregando configurações...</span>
    </div>

    <Dialog v-model:visible="varDialogVisible" :header="editingVar ? 'Editar Variável' : 'Nova Variável Customizada'" modal :style="{ width: '450px' }">
      <form @submit.prevent="saveVar" class="p-fluid">
        <div class="field mb-3">
          <label for="varTag">Tag *</label>
          <InputText id="varTag" v-model="varForm.tag" required placeholder="{{minha_variavel}}" />
          <small class="helper-text">Formato: {duas chaves}nome_variavel{duas chaves}. Ex: {{custom_saudacao}}</small>
        </div>
        <div class="field mb-3">
          <label for="varNome">Nome *</label>
          <InputText id="varNome" v-model="varForm.nome" required placeholder="Nome descritivo" />
        </div>
        <div class="field mb-3">
          <label for="varPadrao">Valor Padrão (opcional)</label>
          <InputText id="varPadrao" v-model="varForm.valor_padrao" placeholder="Valor usado como fallback" />
        </div>
        <div class="dialog-actions">
          <Button label="Cancelar" severity="secondary" text @click="varDialogVisible = false" />
          <Button type="submit" :label="editingVar ? 'Salvar' : 'Criar'" icon="pi pi-check" :loading="savingVar" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import VariablePalette from '../components/VariablePalette.vue'
import api from '../services/api'

const TAG_RE = /\{\{[a-z][a-z0-9_]*\}\}/g

const authStore = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const config = ref(null)
const customVars = ref([])

const smtpPassword = ref('')
const showSmtpPwd = ref(false)
const saving = ref(false)

const varDialogVisible = ref(false)
const editingVar = ref(null)
const varForm = ref({ tag: '', nome: '', valor_padrao: '' })
const savingVar = ref(false)


onMounted(async () => {
  try {
    const { data } = await api.get('/api/empresas/me')
    config.value = data
    nextTick(() => {
      if (editorRef.value) {
        setEditorContent(config.value.email_corpo_padrao || '')
      }
    })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar configurações', life: 3000 })
  }
  fetchCustomVars()
})

async function fetchCustomVars() {
  try {
    const { data } = await api.get('/api/modelos/variaveis')
    customVars.value = data.customizadas
  } catch (e) {
    console.error('Erro ao carregar variáveis customizadas:', e)
  }
}

function openVarDialog(item = null) {
  editingVar.value = item
  if (item) {
    varForm.value = { tag: item.tag, nome: item.nome, valor_padrao: item.valor_padrao || '' }
  } else {
    varForm.value = { tag: '', nome: '', valor_padrao: '' }
  }
  varDialogVisible.value = true
}

async function saveVar() {
  savingVar.value = true
  try {
    if (editingVar.value) {
      await api.put(`/api/modelos/variaveis/customizadas/${editingVar.value.id}`, varForm.value)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Variável atualizada', life: 3000 })
    } else {
      await api.post('/api/modelos/variaveis/customizadas', varForm.value)
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Variável criada', life: 3000 })
    }
    varDialogVisible.value = false
    await fetchCustomVars()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Erro ao salvar variável'
    toast.add({ severity: 'error', summary: 'Erro', detail: msg, life: 5000 })
  } finally {
    savingVar.value = false
  }
}

async function deleteVar(item) {
  confirm.require({
    message: `Deseja realmente excluir a variável "${item.tag}"?`,
    header: 'Confirmar Exclusão',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Excluir',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await api.delete(`/api/modelos/variaveis/customizadas/${item.id}`)
        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Variável excluída', life: 3000 })
        await fetchCustomVars()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao excluir', life: 3000 })
      }
    }
  })
}

const editorRef = ref(null)

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
  lines.forEach((line) => {
    const span = document.createElement('div')
    span.innerHTML = markdownToHtml(line) || '<br>'
    editorRef.value.appendChild(span)
  })
}

function insertVariable(tag) {
  // If focused on the subject field
  const activeEl = document.activeElement
  if (activeEl && activeEl.tagName === 'INPUT' && activeEl.closest('.form-section')) {
    const start = activeEl.selectionStart
    const end = activeEl.selectionEnd
    const currentVal = activeEl.value
    activeEl.value = currentVal.substring(0, start) + tag + currentVal.substring(end)
    // dispatch event
    activeEl.dispatchEvent(new Event('input'))
    
    // reset cursor
    setTimeout(() => {
      activeEl.selectionStart = activeEl.selectionEnd = start + tag.length
      activeEl.focus()
    }, 0)
    return
  }

  // Otherwise, insert in contenteditable
  if (!editorRef.value) return

  const sel = window.getSelection()
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
    
    onEditorInput()
  }
}

function onDropEmail(event) {
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
  if (config.value) {
    config.value.email_corpo_padrao = htmlToMarkdown()
  }
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

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      prefixo_proposta: config.value.prefixo_proposta,
      validade_padrao_dias: config.value.validade_padrao_dias,
      modelo_proposta_padrao: config.value.modelo_proposta_padrao,

      smtp_host: config.value.smtp_host,
      smtp_port: config.value.smtp_port,
      smtp_user: config.value.smtp_user,
      
      email_assunto_padrao: config.value.email_assunto_padrao,
      email_corpo_padrao: config.value.email_corpo_padrao
    }
    
    if (smtpPassword.value.trim()) {
      payload.smtp_password = smtpPassword.value.trim()
    }

    const { data } = await api.put('/api/empresas/me', payload)
    config.value = data

    smtpPassword.value = ''
    showSmtpPwd.value = false
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Configurações atualizadas', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar configurações', life: 3000 })
  } finally {
    saving.value = false
  }
}
</script>

<script>
// Expose component name for route debug
export default {
  name: 'ConfiguracoesView'
}
</script>

<style scoped>
.configuracoes-view {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.25rem;
  font-weight: 590;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.form-card {
  padding: 2rem;
  border-radius: var(--border-radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.form-section {
  margin-bottom: 2.25rem;
  padding-bottom: 1.75rem;
  border-bottom: 1px solid var(--border-color);
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 590;
  color: var(--primary-600);
  margin-bottom: 0.25rem;
}

.section-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field.span-2 {
  grid-column: span 2;
}

.field label {
  font-size: 0.8rem;
  font-weight: 510;
  color: var(--text-secondary);
}

.api-key-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.input-with-button {
  display: flex;
  align-items: center;
  position: relative;
  width: 100%;
}

.key-input {
  padding-right: 2.75rem !important;
  height: 40px;
}

.toggle-key-btn {
  position: absolute;
  right: 0.5rem;
  height: 30px;
  width: 30px;
  min-width: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  z-index: 2;
  color: var(--text-muted);
}

.toggle-key-btn:hover {
  color: var(--text-primary);
}

.key-status {
  display: flex;
  align-items: center;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 510;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.status-pill.aceita {
  background: rgba(39, 166, 68, 0.04);
  border-color: rgba(39, 166, 68, 0.12);
  color: var(--accent-green);
}

.status-pill.rascunho {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}

.helper-text {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.form-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

.save-btn {
  height: 40px;
  font-weight: 510 !important;
  box-shadow: var(--shadow-glow-primary);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.loading-state i {
  font-size: 1.5rem;
}

.var-tag-code {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--primary-500);
  background: rgba(243, 156, 18, 0.08);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.empty-vars {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.85rem;
  justify-content: center;
}

.mb-3 {
  margin-bottom: 1rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.text-secondary {
  color: var(--text-secondary);
}

.text-muted {
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .field.span-2 {
    grid-column: span 1;
  }
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

</style>
