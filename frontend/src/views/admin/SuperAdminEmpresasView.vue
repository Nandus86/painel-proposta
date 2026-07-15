<template>
  <div class="superadmin-view fade-in">
    <div class="page-header">
      <h2>Gestão de Empresas (SaaS)</h2>
      <p class="page-desc">Visão de Superusuário: Gerencie os tenants, planos e status financeiro.</p>
    </div>

    <div class="content-card glass">
      <DataTable
        :value="empresas"
        :paginator="true"
        :rows="10"
        dataKey="id"
        :loading="loading"
        stripedRows
        class="custom-datatable"
      >
        <template #empty>
          Nenhuma empresa encontrada.
        </template>
        
        <Column field="logo_url" header="Logo">
          <template #body="slotProps">
            <img v-if="slotProps.data.logo_url" :src="backendUrl(slotProps.data.logo_url)" alt="Logo" class="table-logo" />
            <div v-else class="no-logo-avatar">
              {{ slotProps.data.razao_social.charAt(0) }}
            </div>
          </template>
        </Column>
        
        <Column field="razao_social" header="Empresa / Contato" sortable>
          <template #body="slotProps">
            <div class="empresa-info">
              <span class="empresa-name">{{ slotProps.data.razao_social }}</span>
              <span class="empresa-subinfo">CNPJ: {{ slotProps.data.cnpj }}</span>
              <span class="empresa-subinfo" v-if="slotProps.data.email">
                <i class="pi pi-envelope text-xs"></i> {{ slotProps.data.email }}
              </span>
              <span class="empresa-subinfo" v-if="slotProps.data.telefone">
                <i class="pi pi-phone text-xs"></i> {{ slotProps.data.telefone }}
              </span>
              <span class="empresa-subinfo" v-if="slotProps.data.cidade">
                <i class="pi pi-map-marker text-xs"></i> {{ slotProps.data.cidade }}{{ slotProps.data.estado ? ' - ' + slotProps.data.estado : '' }}
              </span>
            </div>
          </template>
        </Column>
        
        <Column field="plano" header="Plano" sortable>
          <template #body="slotProps">
            <Tag :severity="getPlanoSeverity(slotProps.data.plano)" :value="slotProps.data.plano.toUpperCase()"></Tag>
          </template>
        </Column>

        <Column field="status_pagamento" header="Pagamento" sortable>
          <template #body="slotProps">
            <Tag :severity="getPagamentoSeverity(slotProps.data.status_pagamento)" :value="formatStatus(slotProps.data.status_pagamento)"></Tag>
          </template>
        </Column>

        <Column field="ativo" header="Acesso" sortable>
          <template #body="slotProps">
            <Tag :severity="slotProps.data.ativo ? 'success' : 'danger'" :value="slotProps.data.ativo ? 'ATIVO' : 'BLOQUEADO'"></Tag>
          </template>
        </Column>
        
        <Column header="Ações" :exportable="false" style="min-width: 8rem">
          <template #body="slotProps">
            <Button icon="pi pi-cog" text rounded aria-label="Opções" @click="openEditDialog(slotProps.data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Edit Dialog -->
    <Dialog v-model:visible="editDialog" :style="{ width: '450px' }" header="Gerenciar Empresa" :modal="true" class="p-fluid">
      <div v-if="selectedEmpresa" class="mt-2">
        <h3 class="mb-4 text-lg font-bold">{{ selectedEmpresa.razao_social }}</h3>
        
        <div class="field mb-4">
          <label for="plano" class="font-bold">Plano de Assinatura</label>
          <Dropdown id="plano" v-model="editData.plano" :options="planos" optionLabel="label" optionValue="value" placeholder="Selecione um plano" />
        </div>

        <div class="field mb-4">
          <label for="status_pagamento" class="font-bold">Status Financeiro</label>
          <Dropdown id="status_pagamento" v-model="editData.status_pagamento" :options="statusPagamento" optionLabel="label" optionValue="value" placeholder="Selecione um status" />
        </div>

        <div class="field mb-4 flex align-items-center">
          <ToggleSwitch v-model="editData.ativo" inputId="ativo" />
          <label for="ativo" class="ml-2 font-bold mb-0">Acesso Ativo (Desmarque para bloquear)</label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Salvar Alterações" icon="pi pi-check" @click="saveEmpresa" :loading="saving" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import ToggleSwitch from 'primevue/toggleswitch'
import api from '../../services/api'

const toast = useToast()
const empresas = ref([])
const loading = ref(false)

const editDialog = ref(false)
const selectedEmpresa = ref(null)
const editData = ref({
  plano: '',
  status_pagamento: '',
  ativo: true
})
const saving = ref(false)

const planos = [
  { label: 'Gratuito', value: 'gratuito' },
  { label: 'Básico', value: 'basico' },
  { label: 'Pro', value: 'pro' },
  { label: 'Premium', value: 'premium' }
]

const statusPagamento = [
  { label: 'Em Dia', value: 'em_dia' },
  { label: 'Inadimplente', value: 'inadimplente' },
  { label: 'Cancelado', value: 'cancelado' }
]

function backendUrl(path) {
  if (!path) return ''
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000'
  return `${baseUrl}${path}`
}

function getPlanoSeverity(plano) {
  switch (plano?.toLowerCase()) {
    case 'premium': return 'warning' // Gold/Yellow
    case 'pro': return 'info'
    case 'basico': return 'success'
    default: return 'secondary'
  }
}

function getPagamentoSeverity(status) {
  switch (status?.toLowerCase()) {
    case 'em_dia': return 'success'
    case 'inadimplente': return 'danger'
    case 'cancelado': return 'secondary'
    default: return 'info'
  }
}

function formatStatus(status) {
  if (!status) return ''
  return status.replace('_', ' ').toUpperCase()
}

function openEditDialog(empresa) {
  selectedEmpresa.value = { ...empresa }
  editData.value = {
    plano: empresa.plano || 'gratuito',
    status_pagamento: empresa.status_pagamento || 'em_dia',
    ativo: empresa.ativo !== false // default true
  }
  editDialog.value = true
}

function hideDialog() {
  editDialog.value = false
}

async function saveEmpresa() {
  if (!selectedEmpresa.value) return
  saving.value = true
  try {
    const { data } = await api.put(`/api/empresas/admin/${selectedEmpresa.value.id}/status`, editData.value)
    
    // Update locally
    const index = empresas.value.findIndex(e => e.id === selectedEmpresa.value.id)
    if (index !== -1) {
      empresas.value[index] = data
    }
    
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa atualizada', life: 3000 })
    editDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao atualizar', life: 3000 })
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/empresas/admin/todas')
    empresas.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar empresas', life: 3000 })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}
.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
}
.page-desc {
  color: var(--text-muted);
  font-size: 0.95rem;
}
.content-card {
  padding: 1.5rem;
  border-radius: 12px;
}
.table-logo {
  max-height: 40px;
  max-width: 80px;
  object-fit: contain;
  border-radius: 4px;
}
.no-logo-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--surface-200);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}
.empresa-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.empresa-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.1rem;
}
.empresa-subinfo {
  font-size: 0.75rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.text-xs {
  font-size: 0.7rem;
}
.flex {
  display: flex;
}
.align-items-center {
  align-items: center;
}
.mb-4 {
  margin-bottom: 1rem;
}
.mt-2 {
  margin-top: 0.5rem;
}
.mb-0 {
  margin-bottom: 0;
}
.ml-2 {
  margin-left: 0.5rem;
}
.text-lg {
  font-size: 1.125rem;
}
.font-bold {
  font-weight: 700;
}
</style>
