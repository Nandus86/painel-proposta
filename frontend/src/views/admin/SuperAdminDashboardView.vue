<template>
  <div class="superadmin-dashboard fade-in">
    <div class="page-header">
      <h2>Painel do Super Administrador</h2>
      <p class="page-desc">Visão geral do SaaS: métricas, empresas e status do sistema.</p>
    </div>

    <div class="stats-grid" v-if="dashboard">
      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Total de Empresas</span>
          <i class="pi pi-globe"></i>
        </div>
        <div class="stat-value">{{ dashboard.empresas.total }}</div>
        <div class="stat-sub">{{ dashboard.empresas.ativas }} ativas · {{ dashboard.empresas.inativas }} inativas</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Novas Empresas (30d)</span>
          <i class="pi pi-plus-circle"></i>
        </div>
        <div class="stat-value">{{ dashboard.empresas.novas_30d }}</div>
        <div class="stat-sub">Últimos 30 dias</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Total de Usuários</span>
          <i class="pi pi-users"></i>
        </div>
        <div class="stat-value">{{ dashboard.usuarios.total }}</div>
        <div class="stat-sub">Em todas as empresas</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Propostas (Mês)</span>
          <i class="pi pi-file"></i>
        </div>
        <div class="stat-value">{{ dashboard.propostas.mes }}</div>
        <div class="stat-sub">Total: {{ dashboard.propostas.total }}</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Orçamentos (Mês)</span>
          <i class="pi pi-calculator"></i>
        </div>
        <div class="stat-value">{{ dashboard.orcamentos.mes }}</div>
        <div class="stat-sub">Total: {{ dashboard.orcamentos.total }}</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Créditos IA Consumidos</span>
          <i class="pi pi-sparkles"></i>
        </div>
        <div class="stat-value">{{ dashboard.ia.creditos_consumidos_total }}</div>
        <div class="stat-sub">Total acumulado</div>
      </div>
    </div>

    <div class="charts-grid" v-if="dashboard">
      <div class="chart-card">
        <h3>Empresas por Plano</h3>
        <canvas ref="planoChartRef"></canvas>
      </div>
      <div class="chart-card">
        <h3>Status de Pagamento</h3>
        <canvas ref="pagamentoChartRef"></canvas>
      </div>
    </div>

    <div class="table-card" v-if="dashboard">
      <div class="table-header">
        <h3>Últimas Empresas Criadas</h3>
        <router-link to="/admin/empresas" class="view-all">Ver todas <i class="pi pi-arrow-right"></i></router-link>
      </div>
      <DataTable :value="dashboard.ultimas_empresas" stripedRows class="custom-datatable">
        <Column field="razao_social" header="Empresa" sortable />
        <Column field="plano" header="Plano" sortable>
          <template #body="{ data }">
            <Tag :severity="planoSeverity(data.plano)" :value="data.plano.toUpperCase()" />
          </template>
        </Column>
        <Column field="status_pagamento" header="Pagamento" sortable>
          <template #body="{ data }">
            <Tag :severity="pagamentoSeverity(data.status_pagamento)" :value="formatStatus(data.status_pagamento)" />
          </template>
        </Column>
        <Column field="ativo" header="Acesso">
          <template #body="{ data }">
            <Tag :severity="data.ativo ? 'success' : 'danger'" :value="data.ativo ? 'ATIVO' : 'BLOQUEADO'" />
          </template>
        </Column>
      </DataTable>
    </div>

    <div v-if="!dashboard" class="loading-state">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Carregando dashboard...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import api from '../../services/api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const router = useRouter()
const dashboard = ref(null)
const planoChartRef = ref(null)
const pagamentoChartRef = ref(null)
let planoChart = null
let pagamentoChart = null

const PLANO_COLORS = {
  gratuito: '#6c757d',
  basico: '#16a34a',
  pro: '#2563eb',
  premium: '#f39c12'
}

const PAGAMENTO_COLORS = {
  em_dia: '#16a34a',
  inadimplente: '#dc2626',
  cancelado: '#6c757d'
}

function planoSeverity(plano) {
  const map = { gratuito: 'secondary', basico: 'success', pro: 'info', premium: 'warning' }
  return map[plano] || 'secondary'
}

function pagamentoSeverity(status) {
  const map = { em_dia: 'success', inadimplente: 'danger', cancelado: 'secondary' }
  return map[status] || 'info'
}

function formatStatus(status) {
  if (!status) return ''
  return status.replace('_', ' ').toUpperCase()
}

function renderCharts() {
  if (!dashboard.value) return

  const planoData = dashboard.value.empresas_por_plano || []
  const pagamentoData = dashboard.value.empresas_por_pagamento || []

  if (planoChartRef.value) {
    if (planoChart) planoChart.destroy()
    planoChart = new Chart(planoChartRef.value, {
      type: 'doughnut',
      data: {
        labels: planoData.map(p => p.plano.toUpperCase()),
        datasets: [{
          data: planoData.map(p => p.total),
          backgroundColor: planoData.map(p => PLANO_COLORS[p.plano] || '#6c757d'),
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    })
  }

  if (pagamentoChartRef.value) {
    if (pagamentoChart) pagamentoChart.destroy()
    pagamentoChart = new Chart(pagamentoChartRef.value, {
      type: 'doughnut',
      data: {
        labels: pagamentoData.map(p => formatStatus(p.status)),
        datasets: [{
          data: pagamentoData.map(p => p.total),
          backgroundColor: pagamentoData.map(p => PAGAMENTO_COLORS[p.status] || '#6c757d'),
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    })
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/api/superadmin/dashboard')
    dashboard.value = data
    await nextTick()
    renderCharts()
  } catch (e) {
    console.error('Erro ao carregar dashboard superadmin:', e)
  }
})
</script>

<style scoped>
.superadmin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  margin-bottom: 0.5rem;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  transition: all var(--transition-fast);
  box-shadow: var(--glass-shadow);
}

.stat-card:hover {
  border-color: var(--primary-400);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.stat-label {
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-value {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.stat-sub {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  box-shadow: var(--glass-shadow);
}

.chart-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-card canvas {
  max-height: 260px;
}

.table-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  box-shadow: var(--glass-shadow);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.table-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.view-all {
  color: var(--primary-400);
  font-size: 0.85rem;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.view-all:hover {
  color: var(--primary-300);
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
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
