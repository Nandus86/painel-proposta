<template>
  <div class="superadmin-config-view fade-in">
    <div class="page-header">
      <h2>Configurações do Sistema</h2>
      <p class="page-desc">Visão de Superusuário: Gerencie a Inteligência Artificial global do SaaS.</p>
    </div>

    <div class="form-card glass">
      <form @submit.prevent="handleSave">
        <!-- AI Settings Section -->
        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-sparkles"></i>
            Inteligência Artificial (Global)
          </h3>
          <p class="section-desc">Configure a chave de API e o modelo de IA que serão utilizados globalmente por todas as empresas do sistema.</p>

          <div class="form-grid" v-if="!loadingConfig">
            <div class="field span-2">
              <label>Chave de API do OpenRouter</label>
              <div class="api-key-input-wrapper">
                <div class="input-with-button">
                  <InputText
                    v-model="openrouterKey"
                    :type="showKey ? 'text' : 'password'"
                    :placeholder="config.has_openrouter_key ? '•••••••••••••••••••••••••••••••• (Salva e encriptada)' : 'Sua API Key do OpenRouter (sk-or-...)'"
                    class="w-full key-input"
                  />
                  <Button
                    type="button"
                    :icon="showKey ? 'pi pi-eye-slash' : 'pi pi-eye'"
                    severity="secondary"
                    text
                    class="toggle-key-btn"
                    @click="showKey = !showKey"
                    v-tooltip.bottom="showKey ? 'Ocultar chave' : 'Mostrar chave'"
                  />
                </div>
                <div class="key-status mt-2">
                  <span class="status-pill" :class="config.has_openrouter_key ? 'aceita' : 'rascunho'">
                    <i :class="config.has_openrouter_key ? 'pi pi-lock-open mr-1' : 'pi pi-lock mr-1'"></i>
                    {{ config.has_openrouter_key ? 'Chave configurada e protegida' : 'Nenhuma chave configurada' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="field span-2 mt-2">
              <label for="openrouter-model">Modelo de IA Padrão (OpenRouter)</label>
              <Select
                id="openrouter-model"
                v-model="config.openrouter_model"
                :options="models"
                optionLabel="name"
                optionValue="id"
                placeholder="Selecione o modelo do OpenRouter..."
                :loading="loadingModels"
                filter
                class="w-full"
              />
            </div>
          </div>
          <div v-else class="loading-state">
            <i class="pi pi-spin pi-spinner"></i>
            <span>Carregando configurações globais...</span>
          </div>
        </div>

        <!-- Save Button -->
        <div class="form-actions" v-if="!loadingConfig">
          <Button type="submit" label="Salvar Configurações" icon="pi pi-check" :loading="saving" class="save-btn" />
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Select from 'primevue/select'
import api from '../../services/api'

const toast = useToast()

const config = ref({ has_openrouter_key: false, openrouter_model: '' })
const openrouterKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const models = ref([])
const loadingModels = ref(false)
const loadingConfig = ref(true)

async function fetchModels() {
  loadingModels.value = true
  try {
    const { data } = await api.get('/api/ai/openrouter/models')
    models.value = data
  } catch (e) {
    console.error('Erro ao buscar modelos:', e)
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Erro ao carregar lista de modelos do OpenRouter', life: 3000 })
  } finally {
    loadingModels.value = false
  }
}

async function fetchConfig() {
  loadingConfig.value = true
  try {
    const { data } = await api.get('/api/admin/config')
    config.value = data
  } catch (e) {
    console.error('Erro ao buscar configurações:', e)
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar configurações do sistema', life: 3000 })
  } finally {
    loadingConfig.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchConfig(), fetchModels()])
})

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      openrouter_model: config.value.openrouter_model
    }
    
    // Send key only if user typed a new one
    if (openrouterKey.value.trim()) {
      payload.openrouter_key = openrouterKey.value.trim()
    }

    const { data } = await api.put('/api/admin/config', payload)
    config.value = data
    openrouterKey.value = '' // Clear input after saving
    showKey.value = false
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Configurações globais atualizadas', life: 3000 })
  } catch (e) {
    console.error(e)
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar configurações', life: 3000 })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.superadmin-config-view {
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
