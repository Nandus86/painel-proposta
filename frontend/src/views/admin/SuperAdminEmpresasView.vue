<template>
  <div class="superadmin-view fade-in">
    <div class="page-header">
      <h2>Gestão de Empresas (SaaS)</h2>
      <p class="page-desc">Visão de Superusuário: Gerencie os tenants, planos e status financeiro.</p>
    </div>

    <div class="filters-bar">
      <InputText v-model="searchQuery" placeholder="Buscar por razão social..." class="search-input" @input="onSearch" />
      <Dropdown v-model="filtroPlano" :options="planosOptions" placeholder="Filtrar por Plano" class="filter-dropdown" @change="onFilter" />
      <Dropdown v-model="filtroStatus" :options="statusOptions" placeholder="Filtrar por Status" class="filter-dropdown" @change="onFilter" />
    </div>

    <div class="content-card glass">
      <DataTable
        :value="empresasFiltradas"
        :paginator="true"
        :rows="10"
        dataKey="id"
        :loading="loading"
        stripedRows
        class="custom-datatable"
      >
        <template #empty>Nenhuma empresa encontrada.</template>
        
        <Column field="logo_url" header="Logo">
          <template #body="slotProps">
            <img v-if="slotProps.data.logo_url" :src="backendUrl(slotProps.data.logo_url)" alt="Logo" class="table-logo" />
            <div v-else class="no-logo-avatar">{{ slotProps.data.razao_social.charAt(0) }}</div>
          </template>
        </Column>
        
        <Column field="razao_social" header="Empresa" sortable>
          <template #body="slotProps">
            <div class="empresa-info">
              <span class="empresa-name">{{ slotProps.data.razao_social }}</span>
              <span class="empresa-subinfo">CNPJ: {{ slotProps.data.cnpj }}</span>
              <span class="empresa-subinfo" v-if="slotProps.data.email"><i class="pi pi-envelope text-xs"></i> {{ slotProps.data.email }}</span>
              <span class="empresa-subinfo" v-if="slotProps.data.subdominio"><i class="pi pi-globe text-xs"></i> {{ slotProps.data.subdominio }}.painelproposta.com</span>
              <span class="empresa-subinfo" v-if="slotProps.data.dominio_personalizado"><i class="pi pi-link text-xs"></i> {{ slotProps.data.dominio_personalizado }}</span>
            </div>
          </template>
        </Column>
        
        <Column field="plano" header="Plano" sortable>
          <template #body="slotProps">
            <Tag :severity="getPlanoSeverity(slotProps.data.plano)" :value="slotProps.data.plano.toUpperCase()" />
          </template>
        </Column>

        <Column field="status_pagamento" header="Pagamento" sortable>
          <template #body="slotProps">
            <Tag :severity="getPagamentoSeverity(slotProps.data.status_pagamento)" :value="formatStatus(slotProps.data.status_pagamento)" />
          </template>
        </Column>

        <Column field="ativo" header="Acesso" sortable>
          <template #body="slotProps">
            <Tag :severity="slotProps.data.ativo ? 'success' : 'danger'" :value="slotProps.data.ativo ? 'ATIVO' : 'BLOQUEADO'" />
          </template>
        </Column>
        
        <Column header="Ações Rápidas" :exportable="false" style="min-width: 10rem">
          <template #body="slotProps">
            <div class="action-buttons">
              <Button
                v-if="slotProps.data.ativo"
                icon="pi pi-lock"
                text
                rounded
                severity="danger"
                size="small"
                v-tooltip.top="'Bloquear'"
                @click="quickBlock(slotProps.data)"
              />
              <Button
                v-else
                icon="pi pi-unlock"
                text
                rounded
                severity="success"
                size="small"
                v-tooltip.top="'Desbloquear'"
                @click="quickUnblock(slotProps.data)"
              />
              <Button icon="pi pi-info-circle" text rounded size="small" v-tooltip.top="'Detalhes'" @click="openDetailModal(slotProps.data)" />
              <Button icon="pi pi-cog" text rounded size="small" v-tooltip.top="'Gerenciar'" @click="openEditDialog(slotProps.data)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Detail Modal -->
    <Dialog v-model:visible="detailModal" :style="{ width: '650px' }" header="Detalhes da Empresa" :modal="true" class="p-fluid">
      <div v-if="detalhesEmpresa" class="detail-content">
        <Tabs value="geral">
          <TabList>
            <Tab value="geral">Geral</Tab>
            <Tab value="usuarios">Usuários ({{ detalhesEmpresa.estatisticas?.total_usuarios || 0 }})</Tab>
            <Tab value="propostas">Propostas ({{ detalhesEmpresa.estatisticas?.total_propostas || 0 }})</Tab>
            <Tab value="logs">Logs</Tab>
          </TabList>
          <TabPanels>
            <TabPanel value="geral">
              <div class="detail-grid">
                <div class="detail-item"><strong>Razão Social:</strong> {{ detalhesEmpresa.empresa.razao_social }}</div>
                <div class="detail-item"><strong>CNPJ:</strong> {{ detalhesEmpresa.empresa.cnpj }}</div>
                <div class="detail-item"><strong>Plano:</strong> {{ detalhesEmpresa.empresa.plano?.toUpperCase() }}</div>
                <div class="detail-item"><strong>Pagamento:</strong> {{ formatStatus(detalhesEmpresa.empresa.status_pagamento) }}</div>
                <div class="detail-item"><strong>Ativo:</strong> {{ detalhesEmpresa.empresa.ativo ? 'Sim' : 'Não (Bloqueado)' }}</div>
                <div class="detail-item"><strong>Subdomínio:</strong> {{ detalhesEmpresa.empresa.subdominio || '-' }}</div>
                <div class="detail-item"><strong>Domínio Próprio:</strong> {{ detalhesEmpresa.empresa.dominio_personalizado || '-' }}</div>
                <div class="detail-item"><strong>Créditos IA:</strong> {{ detalhesEmpresa.empresa.ai_credits_used_today }}/{{ detalhesEmpresa.empresa.ai_credits_limit }} (hoje)</div>
                <div class="detail-item"><strong>Criado em:</strong> {{ formatDate(detalhesEmpresa.empresa.created_at) }}</div>
              </div>
            </TabPanel>
            <TabPanel value="usuarios">
              <DataTable :value="detalhesEmpresa.usuarios" size="small">
                <Column field="nome" header="Nome" />
                <Column field="email" header="Email" />
                <Column field="role" header="Função" />
                <Column field="ativo" header="Ativo">
                  <template #body="{ data }">
                    <Tag :severity="data.ativo ? 'success' : 'danger'" :value="data.ativo ? 'SIM' : 'NÃO'" />
                  </template>
                </Column>
              </DataTable>
            </TabPanel>
            <TabPanel value="propostas">
              <DataTable :value="detalhesEmpresa.ultimas_propostas" size="small">
                <Column field="numero" header="#" />
                <Column field="titulo" header="Título" />
                <Column field="status" header="Status" />
                <Column field="valor_total" header="Valor" />
              </DataTable>
            </TabPanel>
            <TabPanel value="logs">
              <div v-if="!detalhesEmpresa.logs?.length" class="empty-state">Nenhum log registrado.</div>
              <div v-else class="logs-list">
                <div v-for="log in detalhesEmpresa.logs" :key="log.id" class="log-item">
                  <span class="log-acao">{{ formatLogAcao(log.acao) }}</span>
                  <span class="log-data">{{ formatDate(log.created_at) }}</span>
                </div>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
      <template #footer>
        <div class="detail-footer">
          <Button label="Resetar Senha Admin" icon="pi pi-key" severity="warning" @click="resetAdminPassword" :loading="resettingPwd" />
          <Button label="Fechar" icon="pi pi-times" text @click="detailModal = false" />
        </div>
      </template>
    </Dialog>

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
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import api from '../../services/api'

const toast = useToast()
const empresas = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filtroPlano = ref(null)
const filtroStatus = ref(null)

const editDialog = ref(false)
const detailModal = ref(false)
const selectedEmpresa = ref(null)
const detalhesEmpresa = ref(null)
const editData = ref({ plano: '', status_pagamento: '', ativo: true })
const saving = ref(false)
const resettingPwd = ref(false)

const planosOptions = [
  { label: 'Todos os Planos', value: null },
  { label: 'Gratuito', value: 'gratuito' },
  { label: 'Básico', value: 'basico' },
  { label: 'Pro', value: 'pro' },
  { label: 'Premium', value: 'premium' },
]

const statusOptions = [
  { label: 'Todos os Status', value: null },
  { label: 'Em Dia', value: 'em_dia' },
  { label: 'Inadimplente', value: 'inadimplente' },
  { label: 'Cancelado', value: 'cancelado' },
]

const planos = [
  { label: 'Gratuito', value: 'gratuito' },
  { label: 'Básico', value: 'basico' },
  { label: 'Pro', value: 'pro' },
  { label: 'Premium', value: 'premium' },
]

const statusPagamento = [
  { label: 'Em Dia', value: 'em_dia' },
  { label: 'Inadimplente', value: 'inadimplente' },
  { label: 'Cancelado', value: 'cancelado' },
]

const empresasFiltradas = computed(() => {
  let list = empresas.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(e => e.razao_social.toLowerCase().includes(q))
  }
  return list
})

function backendUrl(path) {
  if (!path) return ''
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000'
  return `${baseUrl}${path}`
}

function getPlanoSeverity(plano) {
  switch (plano?.toLowerCase()) {
    case 'premium': return 'warning'
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

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

function formatLogAcao(acao) {
  const map = {
    bloquear: 'Bloqueio de acesso',
    desbloquear: 'Desbloqueio de acesso',
    resetar_senha_admin: 'Reset de senha do admin',
    limpar_dados: 'Limpeza de dados',
  }
  return map[acao] || acao
}

async function openDetailModal(empresa) {
  detailModal.value = true
  try {
    const { data } = await api.get(`/api/superadmin/empresas/${empresa.id}/detalhes`)
    detalhesEmpresa.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao carregar detalhes', life: 3000 })
  }
}

async function quickBlock(empresa) {
  try {
    await api.post(`/api/superadmin/empresas/${empresa.id}/acao?acao=bloquear`)
    empresa.ativo = false
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa bloqueada', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao bloquear', life: 3000 })
  }
}

async function quickUnblock(empresa) {
  try {
    await api.post(`/api/superadmin/empresas/${empresa.id}/acao?acao=desbloquear`)
    empresa.ativo = true
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa desbloqueada', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao desbloquear', life: 3000 })
  }
}

async function resetAdminPassword() {
  if (!detalhesEmpresa.value) return
  resettingPwd.value = true
  try {
    const { data } = await api.post(`/api/superadmin/empresas/${detalhesEmpresa.value.empresa.id}/acao?acao=resetar_senha_admin`)
    toast.add({
      severity: 'success',
      summary: 'Senha Resetada',
      detail: `Nova senha: ${data.nova_senha}`,
      life: 10000
    })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao resetar senha', life: 3000 })
  } finally {
    resettingPwd.value = false
  }
}

function openEditDialog(empresa) {
  selectedEmpresa.value = { ...empresa }
  editData.value = {
    plano: empresa.plano || 'gratuito',
    status_pagamento: empresa.status_pagamento || 'em_dia',
    ativo: empresa.ativo !== false
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
    const index = empresas.value.findIndex(e => e.id === selectedEmpresa.value.id)
    if (index !== -1) empresas.value[index] = data
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa atualizada', life: 3000 })
    editDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao atualizar', life: 3000 })
  } finally {
    saving.value = false
  }
}

function onSearch() {}
function onFilter() {}

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
.superadmin-view {
  padding-bottom: 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.page-desc {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: center;
}

.search-input {
  width: 280px;
}

.filter-dropdown {
  width: 200px;
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

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.detail-content {
  min-height: 300px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.detail-item {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.detail-item strong {
  color: var(--text-primary);
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--surface-50);
  border-radius: 6px;
  font-size: 0.85rem;
}

.log-acao {
  font-weight: 500;
  color: var(--text-primary);
}

.log-data {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  width: 100%;
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
