<template>
  <div class="empresa-view fade-in">
    <div class="page-header">
      <h2>Dados da Empresa</h2>
      <p class="page-desc">Gerencie as informações da sua empresa</p>
    </div>

    <div class="form-card glass" v-if="empresa">
      <form @submit.prevent="handleSave">
        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-image"></i>
            Logotipo da Empresa
          </h3>
          <div class="form-grid">
            <div class="field span-2 logo-upload-container">
              <div class="current-logo" v-if="empresa.logo_url">
                <img :src="backendUrl(empresa.logo_url)" alt="Logo da Empresa" />
              </div>
              <div class="upload-controls">
                <input type="file" ref="logoInput" accept="image/*" @change="handleLogoUpload" style="display: none;" />
                <Button label="Selecionar Nova Logo" icon="pi pi-upload" outlined @click="$refs.logoInput.click()" :disabled="!authStore.isAdmin || uploadingLogo" />
                <span v-if="uploadingLogo" class="loading-text" style="margin-left: 10px;">Enviando...</span>
              </div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-building"></i>
            Informações Gerais
          </h3>
          <div class="form-grid">
            <div class="field span-2">
              <label>Razão Social</label>
              <InputText v-model="empresa.razao_social" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Nome Fantasia</label>
              <InputText v-model="empresa.nome_fantasia" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>CNPJ</label>
              <InputText v-model="empresa.cnpj" disabled />
            </div>
            <div class="field">
              <label>Inscrição Estadual</label>
              <InputText v-model="empresa.inscricao_estadual" :disabled="!authStore.isAdmin" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-phone"></i>
            Contato
          </h3>
          <div class="form-grid">
            <div class="field">
              <label>Email</label>
              <InputText v-model="empresa.email" type="email" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Telefone</label>
              <InputText v-model="empresa.telefone" :disabled="!authStore.isAdmin" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-map-marker"></i>
            Endereço
          </h3>
          <div class="form-grid">
            <div class="field span-2">
              <label>Endereço</label>
              <InputText v-model="empresa.endereco" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Cidade</label>
              <InputText v-model="empresa.cidade" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field-row-inner">
              <div class="field">
                <label>Estado</label>
                <InputText v-model="empresa.estado" :disabled="!authStore.isAdmin" maxlength="2" />
              </div>
              <div class="field">
                <label>CEP</label>
                <InputText v-model="empresa.cep" :disabled="!authStore.isAdmin" />
              </div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-cog"></i>
            Configurações de Proposta
          </h3>
          <div class="form-grid">
            <div class="field">
              <label>Prefixo da Proposta</label>
              <InputText v-model="empresa.prefixo_proposta" :disabled="!authStore.isAdmin" placeholder="PROP" />
            </div>
            <div class="field">
              <label>Validade Padrão (dias)</label>
              <InputText v-model.number="empresa.validade_padrao_dias" :disabled="!authStore.isAdmin" type="number" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-globe"></i>
            Localização e Internacionalização
          </h3>
          <div class="form-grid">
            <div class="field">
              <label>País</label>
              <InputText v-model="empresa.pais" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Fuso Horário</label>
              <InputText v-model="empresa.fuso_horario" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Moeda</label>
              <InputText v-model="empresa.moeda" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Idioma</label>
              <InputText v-model="empresa.idioma" :disabled="!authStore.isAdmin" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-palette"></i>
            Marca e Domínio
          </h3>
          <div class="form-grid">
            <div class="field">
              <label>Setor</label>
              <InputText v-model="empresa.setor" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Cor da Marca (HEX)</label>
              <div style="display: flex; gap: 10px; align-items: center;">
                <input type="color" v-model="empresa.cor_marca" :disabled="!authStore.isAdmin" style="width: 40px; height: 40px; border: none; background: none; cursor: pointer;" />
                <InputText v-model="empresa.cor_marca" :disabled="!authStore.isAdmin" placeholder="#f39c12" />
              </div>
            </div>
            <div class="field">
              <label>Subdomínio (.dekto.com)</label>
              <InputText v-model="empresa.subdominio" :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Domínio Personalizado</label>
              <InputText v-model="empresa.dominio_personalizado" :disabled="!authStore.isAdmin" placeholder="ex: propostas.minhaempresa.com" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">
            <i class="pi pi-link"></i>
            Integrações
          </h3>
          <div class="form-grid">
            <div class="field">
              <label>WhatsApp Conectado</label>
              <Button :label="empresa.whatsapp_conectado ? 'Conectado' : 'Desconectado'" 
                      :icon="empresa.whatsapp_conectado ? 'pi pi-check' : 'pi pi-times'" 
                      :severity="empresa.whatsapp_conectado ? 'success' : 'secondary'"
                      @click="empresa.whatsapp_conectado = !empresa.whatsapp_conectado" 
                      :disabled="!authStore.isAdmin" />
            </div>
            <div class="field">
              <label>Telegram Conectado</label>
              <Button :label="empresa.telegram_conectado ? 'Conectado' : 'Desconectado'" 
                      :icon="empresa.telegram_conectado ? 'pi pi-check' : 'pi pi-times'" 
                      :severity="empresa.telegram_conectado ? 'info' : 'secondary'"
                      @click="empresa.telegram_conectado = !empresa.telegram_conectado" 
                      :disabled="!authStore.isAdmin" />
            </div>
            <div class="field span-2">
              <label>Stripe Publishable Key</label>
              <InputText v-model="empresa.stripe_publishable_key" :disabled="!authStore.isAdmin" placeholder="pk_..." />
            </div>
            <div class="field span-2">
              <label>Stripe Secret Key</label>
              <InputText v-model="empresa.stripe_secret_key" :disabled="!authStore.isAdmin" placeholder="sk_..." />
            </div>
            <div class="field span-2" style="display: flex; flex-direction: row; gap: 10px; align-items: center;">
              <Checkbox v-model="empresa.pagamento_modo_teste" :binary="true" inputId="modoTeste" :disabled="!authStore.isAdmin" />
              <label for="modoTeste" style="margin: 0; cursor: pointer;">Gateway em Modo de Teste</label>
            </div>
          </div>
        </div>

        <div class="form-section">
          <div class="field">
            <label>Observações</label>
            <Textarea v-model="empresa.observacoes" :disabled="!authStore.isAdmin" rows="3" class="w-full" />
          </div>
        </div>

        <div class="form-actions" v-if="authStore.isAdmin">
          <Button type="submit" label="Salvar Alterações" icon="pi pi-check" :loading="saving" />
        </div>
      </form>
    </div>

    <div v-else class="loading-state">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Carregando...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import api from '../services/api'

const authStore = useAuthStore()
const toast = useToast()

const empresa = ref(null)
const saving = ref(false)
const uploadingLogo = ref(false)
const logoInput = ref(null)

function backendUrl(path) {
  if (!path) return ''
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000'
  return `${baseUrl}${path}`
}

async function handleLogoUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  uploadingLogo.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const { data } = await api.post('/api/empresas/logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    empresa.value.logo_url = data.logo_url
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Logo atualizada', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao fazer upload da logo', life: 3000 })
  } finally {
    uploadingLogo.value = false
    if (logoInput.value) logoInput.value.value = ''
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/api/empresas/me')
    empresa.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar empresa', life: 3000 })
  }
})

async function handleSave() {
  saving.value = true
  try {
    const { data } = await api.put('/api/empresas/me', empresa.value)
    empresa.value = data
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa atualizada', life: 3000 })
    
    // Refresh user to instantly apply theme changes if cor_marca changed
    await authStore.fetchUser()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao salvar', life: 3000 })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.empresa-view {
  max-width: 900px;
}

.page-header {
  margin-bottom: 1.5rem;
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

.form-card {
  padding: 2rem;
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
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
  font-weight: 600;
  color: var(--primary-400);
  margin-bottom: 1.25rem;
}

.form-section-title i {
  font-size: 0.9rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
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
  font-weight: 600;
  color: var(--text-secondary);
}

.field :deep(.p-inputtext),
.field :deep(.p-textarea) {
  width: 100%;
}

.w-full {
  width: 100%;
}

.field-row-inner {
  display: flex;
  gap: 1rem;
}

.form-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem;
  color: var(--text-muted);
  font-size: 1rem;
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

.logo-upload-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.current-logo img {
  max-width: 200px;
  max-height: 80px;
  object-fit: contain;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  padding: 0.5rem;
  background-color: var(--surface-card);
}

.upload-controls {
  display: flex;
  align-items: center;
}
</style>
