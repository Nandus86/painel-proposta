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
import { ref, onMounted } from 'vue'
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
import api from '../services/api'

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

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      prefixo_proposta: config.value.prefixo_proposta,
      validade_padrao_dias: config.value.validade_padrao_dias,
      modelo_proposta_padrao: config.value.modelo_proposta_padrao,

      smtp_host: config.value.smtp_host,
      smtp_port: config.value.smtp_port,
      smtp_user: config.value.smtp_user
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
</style>
