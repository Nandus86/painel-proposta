<template>
  <div class="dashboard fade-in">
    <!-- Gamification & Tier System -->
    <GamificationCard
      ref="gamificationRef"
      :metrics="metrics"
      @open-planos="showPlanosModal = true"
    />

    <!-- Filters Bar -->
    <div class="dashboard-filters">
      <div class="filter-quick-actions">
        <router-link to="/propostas/nova" class="action-btn primary">
          <i class="pi pi-plus"></i>
          <span>Nova Proposta</span>
        </router-link>
        <router-link to="/orcamentos/novo" class="action-btn secondary">
          <i class="pi pi-calculator"></i>
          <span>Novo Orçamento</span>
        </router-link>
      </div>

      <div class="filter-actions">
        <select v-model="selectedCurrency" class="custom-select currency-select" @change="fetchDashboardData">
          <option value="BRL">R$ BRL</option>
          <option value="USD">$ USD</option>
          <option value="EUR">€ EUR</option>
        </select>

        <select v-model="selectedPeriod" class="custom-select period-select" @change="fetchDashboardData">
          <option value="tudo">Todo o período</option>
          <option value="hoje">Hoje</option>
          <option value="7dias">Últimos 7 dias</option>
          <option value="30dias">Últimos 30 dias</option>
          <option value="mes_atual">Este mês</option>
          <option value="ano_atual">Este ano</option>
        </select>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Propostas preparadas</span>
          <i class="pi pi-file stat-icon blue"></i>
        </div>
        <div class="stat-value">{{ metrics.total_propostas }}</div>
        <div class="stat-sub">Propostas comerciais geradas</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Orçamentos criados</span>
          <i class="pi pi-calculator stat-icon purple"></i>
        </div>
        <div class="stat-value">{{ metrics.total_orcamentos }}</div>
        <div class="stat-sub">Orçamentos detalhados</div>
      </div>
      
      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Visualizações</span>
          <i class="pi pi-eye stat-icon cyan"></i>
        </div>
        <div class="stat-value">{{ metrics.total_visualizacoes }}</div>
        <div class="stat-sub">Aberturas por clientes</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Negociações pendentes</span>
          <i class="pi pi-clock stat-icon orange"></i>
        </div>
        <div class="stat-value">{{ metrics.pagamentos_pendentes }}</div>
        <div class="stat-sub">
          Total: <strong>{{ formatCurrency(metrics.pagamentos_pendentes_valor) }}</strong>
        </div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Vendas fechadas</span>
          <i class="pi pi-check-circle stat-icon green"></i>
        </div>
        <div class="stat-value">{{ metrics.vendas_fechadas }}</div>
        <div class="stat-sub">
          Conversão: <strong>{{ metrics.taxa_conversao }}%</strong>
        </div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Receita total</span>
          <i class="pi pi-chart-line stat-icon gold"></i>
        </div>
        <div class="stat-value revenue">{{ formatCurrency(metrics.receita_total) }}</div>
        <div class="stat-sub">
          Ticket Médio: <strong>{{ formatCurrency(metrics.ticket_medio) }}</strong>
        </div>
      </div>
    </div>

    <!-- Recent Activity Section -->
    <div class="recent-activity">
      <div class="activity-header">
        <div class="header-title-group">
          <h3>Atividade recente</h3>
          <span v-if="activities.length > 0" class="activity-counter">{{ activities.length }} itens</span>
        </div>

        <div class="activity-actions">
          <div class="filter-tabs">
            <button :class="{ active: !onlyMeFilter }" @click="setOnlyMe(false)">Todos</button>
            <button :class="{ active: onlyMeFilter }" @click="setOnlyMe(true)">Somente os meus</button>
          </div>

          <button class="text-btn" @click="fetchActivities" title="Recarregar atividades">
            <i class="pi pi-refresh"></i> Atualizar
          </button>
          
          <button class="collapse-btn" @click="showActivities = !showActivities">
            <i :class="showActivities ? 'pi pi-angle-up' : 'pi pi-angle-down'"></i>
            <span>{{ showActivities ? 'Ocultar' : 'Exibir' }}</span>
          </button>
        </div>
      </div>

      <!-- Activity Content -->
      <div v-show="showActivities" class="activity-container">
        <div v-if="loadingActivities" class="activity-loading">
          <i class="pi pi-spin pi-spinner"></i>
          <span>Carregando histórico...</span>
        </div>

        <div v-else-if="activities.length > 0" class="activity-list">
          <div
            v-for="item in activities"
            :key="item.tipo + '-' + item.id"
            class="activity-row"
            @click="$router.push(item.link)"
          >
            <div class="activity-left">
              <div class="activity-type-badge" :class="item.tipo">
                <i :class="item.tipo === 'proposta' ? 'pi pi-file' : 'pi pi-calculator'"></i>
              </div>
              <div class="activity-main-info">
                <div class="activity-title-line">
                  <span class="activity-number">#{{ item.numero }}</span>
                  <span class="activity-title">{{ item.titulo }}</span>
                </div>
                <div class="activity-meta">
                  <span><i class="pi pi-user mr-1"></i> {{ item.cliente_nome }}</span>
                  <span class="dot">•</span>
                  <span><i class="pi pi-id-card mr-1"></i> {{ item.usuario_nome }}</span>
                  <span class="dot">•</span>
                  <span><i class="pi pi-clock mr-1"></i> {{ formatRelativeTime(item.data) }}</span>
                </div>
              </div>
            </div>

            <div class="activity-right">
              <span class="status-tag" :class="item.status">{{ formatStatus(item.status) }}</span>
              <span class="activity-price">{{ formatCurrency(item.valor_total) }}</span>
              <i class="pi pi-chevron-right arrow-icon"></i>
            </div>
          </div>
        </div>

        <div v-else class="activity-empty">
          <i class="pi pi-inbox empty-icon"></i>
          <p>Ainda não há atividade no período selecionado.</p>
          <div class="empty-actions">
            <router-link to="/propostas/nova" class="action-btn primary small">
              <i class="pi pi-plus"></i> Criar Proposta
            </router-link>
            <router-link to="/orcamentos/novo" class="action-btn secondary small">
              <i class="pi pi-calculator"></i> Criar Orçamento
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Planos -->
    <PlanosModal
      v-model:visible="showPlanosModal"
      @plano-alterado="onPlanoAlterado"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import GamificationCard from '@/components/GamificationCard.vue';
import PlanosModal from '@/components/PlanosModal.vue';

const gamificationRef = ref(null);
const showPlanosModal = ref(false);

const selectedPeriod = ref('tudo');
const selectedCurrency = ref('BRL');
const onlyMeFilter = ref(false);
const showActivities = ref(true);
const loadingActivities = ref(false);
const activities = ref([]);

const metrics = ref({
  total_propostas: 0,
  total_orcamentos: 0,
  total_visualizacoes: 0,
  pagamentos_pendentes: 0,
  pagamentos_pendentes_valor: 0,
  solicitacoes_retorno: 0,
  vendas_fechadas: 0,
  receita_total: 0,
  taxa_conversao: 0,
  ticket_medio: 0,
});

const formatCurrency = (val) => {
  const num = Number(val) || 0;
  const curr = selectedCurrency.value || 'BRL';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: curr }).format(num);
};

const formatStatus = (st) => {
  const map = {
    rascunho: 'Rascunho',
    enviada: 'Enviada',
    enviado: 'Enviado',
    em_analise: 'Em Análise',
    aceita: 'Aceita',
    aprovado: 'Aprovado',
    rejeitada: 'Rejeitada',
    rejeitado: 'Rejeitado',
    vencida: 'Vencida',
    vencido: 'Vencido',
  };
  return map[st] || (st ? st.toUpperCase() : 'Pendente');
};

const formatRelativeTime = (dateStr) => {
  if (!dateStr) return 'Recente';
  const date = new Date(dateStr);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return 'Agora mesmo';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min atrás`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h atrás`;
  if (diffSec < 172800) return 'Ontem';
  return date.toLocaleDateString('pt-BR');
};

const fetchMetrics = async () => {
  try {
    const res = await api.get(`/api/dashboard/metrics?periodo=${selectedPeriod.value}`);
    if (res.data) {
      metrics.value = res.data;
    }
  } catch (error) {
    console.error('Erro ao carregar métricas do dashboard:', error);
  }
};

const fetchActivities = async () => {
  loadingActivities.value = true;
  try {
    const res = await api.get(`/api/dashboard/activities?only_me=${onlyMeFilter.value}&limit=15`);
    if (res.data) {
      activities.value = res.data;
    }
  } catch (error) {
    console.error('Erro ao carregar atividades recentes:', error);
    activities.value = [];
  } finally {
    loadingActivities.value = false;
  }
};

const setOnlyMe = (val) => {
  onlyMeFilter.value = val;
  fetchActivities();
};

const fetchDashboardData = () => {
  fetchMetrics();
  fetchActivities();
};

const onPlanoAlterado = () => {
  fetchDashboardData();
  if (gamificationRef.value?.refresh) {
    gamificationRef.value.refresh();
  }
};

onMounted(() => {
  fetchDashboardData();
});
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding-bottom: 2.5rem;
}

/* Filters Bar */
.dashboard-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.filter-quick-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.9rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  box-shadow: var(--shadow-glow-primary);
}

.action-btn.primary:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.action-btn.secondary {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.action-btn.secondary:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-400);
}

.action-btn.small {
  padding: 0.35rem 0.75rem;
  font-size: 0.78rem;
}

.filter-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.custom-select {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 0.45rem 0.85rem;
  border-radius: var(--border-radius-sm);
  outline: none;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.custom-select:hover,
.custom-select:focus {
  border-color: var(--primary-400);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  transition: all var(--transition-fast);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--glass-shadow);
}

.stat-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-400);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  color: var(--text-secondary);
}

.stat-label {
  font-size: 0.85rem;
  font-weight: 600;
}

.stat-icon {
  font-size: 1.1rem;
  padding: 0.4rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
}

.stat-icon.blue { color: #38bdf8; background: rgba(56, 189, 248, 0.1); }
.stat-icon.purple { color: #a855f7; background: rgba(168, 85, 247, 0.1); }
.stat-icon.cyan { color: #06b6d4; background: rgba(6, 182, 212, 0.1); }
.stat-icon.orange { color: #f97316; background: rgba(249, 115, 22, 0.1); }
.stat-icon.green { color: #10b981; background: rgba(16, 185, 129, 0.1); }
.stat-icon.gold { color: #f59e0b; background: rgba(245, 158, 11, 0.1); }

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
  letter-spacing: -0.02em;
}

.stat-value.revenue {
  color: #10b981;
}

.stat-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Recent Activity */
.recent-activity {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--glass-shadow);
  overflow: hidden;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  gap: 1rem;
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.header-title-group h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.activity-counter {
  font-size: 0.7rem;
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.activity-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-tabs {
  display: flex;
  background: var(--bg-card-hover);
  border-radius: var(--border-radius-sm);
  padding: 3px;
  border: 1px solid var(--border-color);
}

.filter-tabs button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.filter-tabs button.active {
  background: var(--primary-500);
  color: white;
}

.text-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
}

.text-btn:hover {
  color: var(--text-primary);
  background: var(--bg-card-hover);
}

.collapse-btn {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.35rem 0.75rem;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  border-color: var(--primary-400);
}

.activity-container {
  padding: 0.5rem 0;
}

.activity-list {
  display: flex;
  flex-direction: column;
}

.activity-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.activity-row:last-child {
  border-bottom: none;
}

.activity-row:hover {
  background: var(--bg-card-hover);
}

.activity-left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
}

.activity-type-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.activity-type-badge.proposta {
  background: rgba(var(--primary-rgb), 0.12);
  color: var(--primary-600);
  border: 1px solid rgba(var(--primary-rgb), 0.25);
}

.activity-type-badge.orcamento {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.activity-main-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.activity-title-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.activity-number {
  font-family: monospace;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--primary-500);
  background: rgba(var(--primary-rgb), 0.08);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.activity-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.dot {
  opacity: 0.5;
}

.activity-right {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-shrink: 0;
}

.status-tag {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.status-tag.rascunho { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid var(--border-color); }
.status-tag.enviada,
.status-tag.enviado { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
.status-tag.em_analise { background: rgba(245, 158, 11, 0.12); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
.status-tag.aceita,
.status-tag.aprovado { background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.status-tag.rejeitada,
.status-tag.rejeitado { background: rgba(239, 68, 68, 0.12); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
.status-tag.vencida,
.status-tag.vencido { background: rgba(148, 163, 184, 0.12); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

.activity-price {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 90px;
  text-align: right;
}

.arrow-icon {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.activity-empty {
  padding: 3.5rem 1.5rem;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--text-muted);
  opacity: 0.4;
}

.empty-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.activity-loading {
  padding: 3rem;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .dashboard-filters {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-quick-actions,
  .filter-actions {
    width: 100%;
    justify-content: space-between;
  }
  .action-btn {
    flex: 1;
    justify-content: center;
  }
  .activity-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .activity-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

