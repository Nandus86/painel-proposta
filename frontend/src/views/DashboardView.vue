<template>
  <div class="dashboard fade-in">
    <!-- Filters / Top Actions -->
    <div class="dashboard-filters">
      <div class="filter-group"></div>
      <div class="filter-actions">
        <select class="custom-select currency-select">
          <option value="BRL">R$ BRL</option>
          <option value="EUR">€ EUR</option>
          <option value="GBP">£ GBP</option>
        </select>
        <div class="date-picker-mock">
          <i class="pi pi-calendar"></i> Todo o período <i class="pi pi-angle-down"></i>
        </div>
      </div>
    </div>

    <!-- Stats Grid (6 cards) -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Propostas preparadas</span>
          <i class="pi pi-file"></i>
        </div>
        <div class="stat-value">{{ metrics.total_propostas }}</div>
        <div class="stat-sub">Total de propostas criadas</div>
      </div>
      
      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Visualizações</span>
          <i class="pi pi-eye"></i>
        </div>
        <div class="stat-value">{{ metrics.total_visualizacoes }}</div>
        <div class="stat-sub">Quantas vezes suas propostas foram abertas</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Pagamentos pendentes</span>
          <i class="pi pi-credit-card"></i>
        </div>
        <div class="stat-value">0</div>
        <div class="stat-sub">Aceitas, mas ainda não pagas</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Solicitações de retorno</span>
          <i class="pi pi-phone"></i>
        </div>
        <div class="stat-value">0</div>
        <div class="stat-sub">Solicitações de retorno pendentes</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Vendas fechadas</span>
          <span class="currency-symbol">$</span>
        </div>
        <div class="stat-value">{{ metrics.vendas_fechadas }}</div>
        <div class="stat-sub">Propostas com pagamentos concluídos</div>
      </div>

      <div class="stat-card">
        <div class="card-header">
          <span class="stat-label">Receita total</span>
          <i class="pi pi-chart-line"></i>
        </div>
        <div class="stat-value">{{ formatCurrency(metrics.receita_total) }}</div>
        <div class="stat-sub">Valor total das vendas fechadas</div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="recent-activity">
      <div class="activity-header">
        <h3>Atividade recente</h3>
        <div class="activity-actions">
          <div class="filter-tabs">
            <button class="active">Todos</button>
            <button>Somente os meus</button>
          </div>
          <button class="text-btn">Limpar</button>
          <button class="collapse-btn"><i class="pi pi-angle-up"></i> Ocultar</button>
        </div>
      </div>
      <div class="activity-content">
        <p>Ainda não há atividade. <router-link to="/propostas/nova"><strong>Crie sua primeira proposta!</strong></router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/services/api';

const metrics = ref({
  total_propostas: 0,
  total_visualizacoes: 0,
  vendas_fechadas: 0,
  receita_total: 0
});

const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);

const fetchMetrics = async () => {
  try {
    const res = await api.get('/api/dashboard/metrics');
    metrics.value = res.data;
  } catch (error) {
    console.error("Erro ao carregar métricas do dashboard:", error);
  }
};

onMounted(() => {
  fetchMetrics();
});
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding-bottom: 2rem;
}

/* Filters */
.dashboard-filters {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.filter-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.custom-select {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border: 1px solid var(--border-color-hover);
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius-sm);
  outline: none;
  cursor: pointer;
}

.date-picker-mock {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color-hover);
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius-sm);
  color: var(--text-primary);
  font-size: 0.9rem;
  cursor: pointer;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  transition: all var(--transition-fast);
}

.stat-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-color-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
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

.currency-symbol {
  font-weight: 700;
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

/* Recent Activity */
.recent-activity {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  margin-top: 1rem;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.activity-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.activity-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.filter-tabs {
  display: flex;
  background: var(--bg-card-hover);
  border-radius: var(--border-radius-sm);
  padding: 2px;
}

.filter-tabs button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.filter-tabs button.active {
  background: var(--border-color-hover);
  color: var(--text-primary);
}

.text-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.85rem;
}
.text-btn:hover {
  color: var(--text-primary);
}

.collapse-btn {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color-hover);
  color: var(--text-primary);
  padding: 0.4rem 0.8rem;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
}

.activity-content {
  padding: 3rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.activity-content a {
  color: var(--primary-500);
  text-decoration: none;
}
.activity-content a:hover {
  text-decoration: underline;
}
</style>
