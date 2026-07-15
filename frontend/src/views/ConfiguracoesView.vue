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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import api from '../services/api'

const authStore = useAuthStore()
const toast = useToast()

const config = ref(null)

const smtpPassword = ref('')
const showSmtpPwd = ref(false)
const saving = ref(false)


onMounted(async () => {
  try {
    const { data } = await api.get('/api/empresas/me')
    config.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar configurações', life: 3000 })
  }

})

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

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .field.span-2 {
    grid-column: span 1;
  }
}
</style>
