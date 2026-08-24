<template>
  <div class="gamification-card glass fade-in">
    <div class="gamification-header">
      <div class="tier-badge-container">
        <div class="tier-badge-icon" :class="currentTier.slug">
          <i :class="currentTier.icon"></i>
        </div>
        <div class="tier-info">
          <div class="tier-label-row">
            <span class="tier-title">{{ currentTier.name }}</span>
            <span class="tier-pill" :class="currentTier.slug">Plano {{ currentTier.planName }}</span>
          </div>
          <span class="tier-subtitle">{{ currentTier.description }}</span>
        </div>
      </div>

      <div class="header-actions">
        <Button
          :label="isEnterprise ? 'Gerenciar Plano' : '⚡ Subir de Nível / Upgrade'"
          icon="pi pi-sparkles"
          size="small"
          class="btn-upgrade-gamification"
          @click="$emit('open-planos')"
        />
      </div>
    </div>

    <!-- Progress & XP Bar -->
    <div class="xp-section">
      <div class="xp-header">
        <div class="xp-title">
          <i class="pi pi-trophy xp-icon"></i>
          <span>Progresso da Conta: <strong>{{ totalXP }} / {{ maxXP }} XP</strong></span>
        </div>
        <span class="xp-percentage">{{ progressPercent }}% Concluído</span>
      </div>

      <div class="xp-bar-track">
        <div class="xp-bar-fill" :style="{ width: `${progressPercent}%` }"></div>
      </div>
    </div>

    <!-- Quests / Missions Grid -->
    <div class="missions-grid">
      <div
        v-for="mission in missions"
        :key="mission.id"
        class="mission-item"
        :class="{ completed: mission.done }"
      >
        <div class="mission-status-icon">
          <i :class="mission.done ? 'pi pi-check' : 'pi pi-circle'"></i>
        </div>
        <div class="mission-details">
          <span class="mission-title">{{ mission.title }}</span>
          <span class="mission-reward">+{{ mission.xp }} XP</span>
        </div>
      </div>
    </div>

    <!-- Limits / Resource Perks Meter -->
    <div class="perks-footer">
      <div class="perk-item">
        <i class="pi pi-file perk-icon"></i>
        <div class="perk-text">
          <span class="perk-label">Propostas este mês:</span>
          <span class="perk-val">
            {{ propostasCriadas }} / {{ maxPropostasLabel }}
          </span>
        </div>
      </div>

      <div class="perk-item">
        <i class="pi pi-sparkles perk-icon"></i>
        <div class="perk-text">
          <span class="perk-label">Créditos de IA:</span>
          <span class="perk-val">{{ aiCreditsLimit }} / dia</span>
        </div>
      </div>

      <div class="perk-item">
        <i class="pi pi-globe perk-icon"></i>
        <div class="perk-text">
          <span class="perk-label">Domínio Próprio:</span>
          <span class="perk-val" :class="{ active: permiteDominio }">
            {{ permiteDominio ? 'Liberado' : 'Requer Plano Pro' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import Button from 'primevue/button'
import api from '../services/api'

const props = defineProps({
  metrics: {
    type: Object,
    default: () => ({ total_propostas: 0 }),
  },
})

defineEmits(['open-planos'])

const authStore = useAuthStore()
const planoInfo = ref(null)
const empresaData = ref(null)
const totalServicos = ref(0)
const totalModelos = ref(0)

const tiers = {
  gratuito: {
    slug: 'gratuito',
    name: '🥉 Nível Bronze',
    planName: 'Gratuito',
    icon: 'pi pi-shield',
    description: 'Iniciando sua jornada no fechamento de propostas',
  },
  inicial: {
    slug: 'inicial',
    name: '🥈 Nível Prata',
    planName: 'Inicial',
    icon: 'pi pi-compass',
    description: 'Empresa em aceleração com mais capacidade comercial',
  },
  pro: {
    slug: 'pro',
    name: '🥇 Nível Ouro (PRO)',
    planName: 'Pro',
    icon: 'pi pi-bolt',
    description: 'Alta conversão com domínio próprio e limites ampliados',
  },
  empresarial: {
    slug: 'empresarial',
    name: '💎 Nível Diamante (Black)',
    planName: 'Empresarial',
    icon: 'pi pi-crown',
    description: 'Operação ilimitada de máxima escala e potência comercial',
  },
}

const currentTier = computed(() => {
  const slug = (authStore.empresaPlano || planoInfo.value?.plano || 'gratuito').toLowerCase()
  return tiers[slug] || tiers.gratuito
})

const isEnterprise = computed(() => currentTier.value.slug === 'empresarial')

const propostasCriadas = computed(() => props.metrics?.total_propostas || 0)

const maxPropostasLabel = computed(() => {
  const max = planoInfo.value?.detalhes?.max_propostas_mes
  return max ? `${max}` : 'Ilimitado'
})

const aiCreditsLimit = computed(() => {
  return planoInfo.value?.detalhes?.ai_credits_limit || (currentTier.value.slug === 'gratuito' ? 20 : 100)
})

const permiteDominio = computed(() => {
  return !!planoInfo.value?.detalhes?.permite_dominio_proprio || ['pro', 'empresarial'].includes(currentTier.value.slug)
})

// Missions
const missions = computed(() => {
  const isUpgraded = currentTier.value.slug !== 'gratuito'
  const hasEmpresaInfo = !!(empresaData.value?.telefone || empresaData.value?.cnpj)
  const hasServicos = totalServicos.value > 0
  const hasModelos = totalModelos.value > 0
  const hasPropostas = propostasCriadas.value > 0

  return [
    { id: 'empresa', title: 'Completar dados da empresa', xp: 20, done: hasEmpresaInfo },
    { id: 'servicos', title: 'Cadastrar produtos ou serviços', xp: 20, done: hasServicos },
    { id: 'modelos', title: 'Personalizar modelo de proposta', xp: 20, done: hasModelos },
    { id: 'proposta', title: 'Criar e enviar 1ª proposta', xp: 20, done: hasPropostas },
    { id: 'upgrade', title: 'Desbloquear plano superior', xp: 50, done: isUpgraded },
  ]
})

const maxXP = computed(() => {
  return missions.value.reduce((acc, m) => acc + m.xp, 0)
})

const totalXP = computed(() => {
  return missions.value.filter((m) => m.done).reduce((acc, m) => acc + m.xp, 0)
})

const progressPercent = computed(() => {
  if (!maxXP.value) return 0
  return Math.min(100, Math.round((totalXP.value / maxXP.value) * 100))
})

async function fetchGamificationData() {
  try {
    const [pRes, empRes, sRes, mRes] = await Promise.allSettled([
      api.get('/api/planos/me/atual'),
      api.get('/api/empresas/me'),
      api.get('/api/servicos?limit=1'),
      api.get('/api/modelos?limit=1'),
    ])

    if (pRes.status === 'fulfilled') planoInfo.value = pRes.value.data
    if (empRes.status === 'fulfilled') empresaData.value = empRes.value.data
    if (sRes.status === 'fulfilled') totalServicos.value = sRes.value.data?.total || sRes.value.data?.length || 0
    if (mRes.status === 'fulfilled') totalModelos.value = mRes.value.data?.total || mRes.value.data?.length || 0
  } catch (e) {
    console.error('Erro ao carregar dados de gamificação:', e)
  }
}

watch(
  () => authStore.empresaPlano,
  () => {
    fetchGamificationData()
  }
)

onMounted(() => {
  fetchGamificationData()
})

defineExpose({
  refresh: fetchGamificationData,
})
</script>

<style scoped>
.gamification-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  position: relative;
  overflow: hidden;
  box-shadow: var(--glass-shadow);
}

.gamification-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #10b981, var(--primary-500), #a855f7);
}

/* Header */
.gamification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.tier-badge-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.tier-badge-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.tier-badge-icon.gratuito {
  background: linear-gradient(135deg, #78716c, #a8a29e);
  color: white;
}
.tier-badge-icon.inicial {
  background: linear-gradient(135deg, #0284c7, #38bdf8);
  color: white;
}
.tier-badge-icon.pro {
  background: linear-gradient(135deg, #d97706, #fbbf24);
  color: #1e1b4b;
}
.tier-badge-icon.empresarial {
  background: linear-gradient(135deg, #9333ea, #c084fc);
  color: white;
}

.tier-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.tier-label-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.tier-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.tier-pill {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.tier-pill.pro {
  background: rgba(var(--primary-rgb), 0.15);
  color: var(--primary-600);
  border-color: rgba(var(--primary-rgb), 0.3);
}

.tier-pill.empresarial {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border-color: rgba(168, 85, 247, 0.3);
}

.tier-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.btn-upgrade-gamification {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600)) !important;
  border: none !important;
  color: white !important;
  font-weight: 600 !important;
  padding: 0.5rem 1rem !important;
  border-radius: 8px !important;
  box-shadow: var(--shadow-glow-primary) !important;
  transition: all 0.2s ease !important;
}

.btn-upgrade-gamification:hover {
  transform: translateY(-2px);
  filter: brightness(1.08);
}

/* XP Section */
.xp-section {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.xp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
}

.xp-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-secondary);
}

.xp-icon {
  color: #f59e0b;
}

.xp-percentage {
  font-weight: 600;
  color: var(--primary-500);
}

.xp-bar-track {
  width: 100%;
  height: 8px;
  background: var(--bg-card-hover);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.xp-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #10b981, var(--primary-500));
  border-radius: 10px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Missions Grid */
.missions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.mission-item {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  transition: all 0.2s ease;
}

.mission-item.completed {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.05);
}

.mission-status-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}

.mission-item.completed .mission-status-icon {
  background: #10b981;
  color: white;
}

.mission-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mission-title {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mission-item.completed .mission-title {
  color: var(--text-primary);
  font-weight: 500;
}

.mission-reward {
  font-size: 0.65rem;
  color: #f59e0b;
  font-weight: 600;
}

/* Perks Footer */
.perks-footer {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.perk-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.perk-icon {
  color: var(--primary-400);
  font-size: 0.95rem;
}

.perk-text {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
}

.perk-label {
  color: var(--text-muted);
}

.perk-val {
  font-weight: 600;
  color: var(--text-primary);
}

.perk-val.active {
  color: #10b981;
}

@media (max-width: 768px) {
  .gamification-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .btn-upgrade-gamification {
    width: 100%;
  }
  .perks-footer {
    gap: 0.75rem;
  }
}
</style>
