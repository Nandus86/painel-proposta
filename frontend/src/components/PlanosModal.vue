<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    modal
    :dismissableMask="true"
    :style="{ width: '92vw', maxWidth: '1050px' }"
    header=" "
    class="planos-modal"
  >
    <div class="modal-body">
      <div class="modal-header-custom">
        <div class="header-badge">
          <i class="pi pi-sparkles"></i> PLANOS & ASSINATURA
        </div>
        <h2>Escolha o Plano Ideal para seu Negócio</h2>
        <p class="subtitle">
          Altere ou faça upgrade do seu plano a qualquer momento. Novos recursos e limites são liberados instantaneamente.
        </p>

        <!-- Toggle Mensal / Anual -->
        <div class="billing-toggle-container">
          <div class="billing-toggle">
            <button
              type="button"
              :class="{ active: billingCycle === 'mensal' }"
              @click="billingCycle = 'mensal'"
            >
              Faturamento Mensal
            </button>
            <button
              type="button"
              :class="{ active: billingCycle === 'anual' }"
              @click="billingCycle = 'anual'"
            >
              Faturamento Anual
              <span class="discount-badge">-15% OFF</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <span>Carregando planos disponíveis...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <i class="pi pi-exclamation-circle"></i>
        <span>{{ error }}</span>
        <Button label="Tentar novamente" size="small" text @click="fetchPlanos" />
      </div>

      <!-- Plan Cards Grid -->
      <div v-else class="plans-grid">
        <div
          v-for="plano in planos"
          :key="plano.slug"
          class="plan-card"
          :class="{
            'is-current': isCurrentPlan(plano.slug),
            'is-featured': plano.destaque,
          }"
        >
          <div v-if="plano.destaque" class="popular-tag">
            <i class="pi pi-bolt"></i> MAIS POPULAR
          </div>

          <div class="plan-card-header">
            <div class="plan-badge-icon" :class="plano.slug">
              <i :class="getPlanIcon(plano.slug)"></i>
            </div>
            <h3 class="plan-name">{{ plano.nome }}</h3>
            <p class="plan-desc">{{ plano.descricao || 'Perfeito para acelerar suas vendas' }}</p>
          </div>

          <div class="plan-pricing">
            <template v-if="plano.preco_mensal && plano.preco_mensal > 0">
              <div class="price-val">
                <span class="currency">R$</span>
                <span class="amount">
                  {{ billingCycle === 'anual' ? formatPrice(plano.preco_anual / 12) : formatPrice(plano.preco_mensal) }}
                </span>
                <span class="period">/mês</span>
              </div>
              <small v-if="billingCycle === 'anual'" class="annual-note">
                Faturado R$ {{ formatPrice(plano.preco_anual) }} ao ano
              </small>
            </template>
            <template v-else>
              <div class="price-val">
                <span class="amount free">Grátis</span>
              </div>
              <small class="annual-note">Para sempre sem custos</small>
            </template>
          </div>

          <ul class="plan-features">
            <li>
              <i class="pi pi-check-circle check-icon"></i>
              <span>
                <strong>{{ plano.max_propostas_mes ? `${plano.max_propostas_mes} propostas & ${plano.max_propostas_mes} orçamentos` : 'Propostas e Orçamentos Ilimitados' }}</strong> /mês
              </span>
            </li>
            <li>
              <i class="pi pi-check-circle check-icon"></i>
              <span>
                <strong>{{ plano.max_usuarios ? `${plano.max_usuarios} ${plano.max_usuarios === 1 ? 'usuário' : 'usuários'}` : 'Usuários Ilimitados' }}</strong>
              </span>
            </li>
            <li>
              <i class="pi pi-check-circle check-icon"></i>
              <span>
                <strong>{{ plano.ai_credits_limit || 20 }} créditos</strong> de IA por dia
              </span>
            </li>
            <li>
              <i
                class="pi"
                :class="plano.permite_dominio_proprio ? 'pi-check-circle check-icon' : 'pi-times-circle times-icon'"
              ></i>
              <span :class="{ 'disabled-feature': !plano.permite_dominio_proprio }">
                Domínio personalizado (DNS)
              </span>
            </li>
            <li>
              <i class="pi pi-check-circle check-icon"></i>
              <span>Envio por WhatsApp & E-mail</span>
            </li>
            <li>
              <i class="pi pi-check-circle check-icon"></i>
              <span>PDF interativo e visualização online</span>
            </li>
          </ul>

          <div class="plan-action">
            <Button
              v-if="isCurrentPlan(plano.slug)"
              label="Plano Ativo"
              icon="pi pi-check"
              class="w-full btn-current"
              disabled
            />
            <Button
              v-else
              :label="getButtonLabel(plano)"
              :icon="changingSlug === plano.slug ? 'pi pi-spin pi-spinner' : 'pi pi-arrow-right'"
              :loading="changingSlug === plano.slug"
              :class="['w-full', plano.destaque ? 'btn-featured' : 'btn-select']"
              @click="handleSelectPlan(plano)"
            />
          </div>
        </div>
      </div>

      <div class="modal-footer-info">
        <div class="info-item">
          <i class="pi pi-shield"></i>
          <span>Ativação imediata de todos os recursos ao trocar de plano</span>
        </div>
        <div class="info-item">
          <i class="pi pi-sync"></i>
          <span>Cancele ou mude de plano a qualquer momento</span>
        </div>
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import api from '../services/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:visible', 'plano-alterado'])

const authStore = useAuthStore()
const toast = useToast()

const billingCycle = ref('mensal')
const loading = ref(false)
const changingSlug = ref(null)
const error = ref('')
const planos = ref([])
const planoAtualSlug = ref('gratuito')

const fallbackPlanos = [
  {
    slug: 'gratuito',
    nome: 'Gratuito',
    descricao: 'Ideal para começar a enviar propostas',
    preco_mensal: 0,
    preco_anual: 0,
    max_usuarios: 1,
    max_propostas_mes: 3,
    ai_credits_limit: 20,
    permite_dominio_proprio: false,
    destaque: false,
  },
  {
    slug: 'inicial',
    nome: 'Inicial',
    descricao: 'Para pequenas empresas e profissionais autônomos',
    preco_mensal: 39,
    preco_anual: 429,
    max_usuarios: 2,
    max_propostas_mes: 20,
    ai_credits_limit: 50,
    permite_dominio_proprio: false,
    destaque: false,
  },
  {
    slug: 'pro',
    nome: 'Pro',
    descricao: 'Para empresas em crescimento que buscam escala',
    preco_mensal: 69,
    preco_anual: 759,
    max_usuarios: 5,
    max_propostas_mes: 50,
    ai_credits_limit: 100,
    permite_dominio_proprio: true,
    destaque: true,
  },
  {
    slug: 'empresarial',
    nome: 'Empresarial',
    descricao: 'Para grandes operações sem limites',
    preco_mensal: 129,
    preco_anual: 1419,
    max_usuarios: null,
    max_propostas_mes: null,
    ai_credits_limit: 200,
    permite_dominio_proprio: true,
    destaque: false,
  },
]

function formatPrice(val) {
  if (!val) return '0,00'
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)
}

function isCurrentPlan(slug) {
  const current = authStore.empresaPlano || planoAtualSlug.value || 'gratuito'
  return current.toLowerCase() === slug.toLowerCase()
}

function getPlanIcon(slug) {
  const icons = {
    gratuito: 'pi pi-seedling',
    inicial: 'pi pi-compass',
    pro: 'pi pi-bolt',
    empresarial: 'pi pi-crown',
  }
  return icons[slug] || 'pi pi-sparkles'
}

function getButtonLabel(plano) {
  if (isCurrentPlan(plano.slug)) return 'Plano Ativo'
  if (plano.slug === 'gratuito') return 'Mudar para Gratuito'
  return `Escolher ${plano.nome}`
}

async function fetchPlanos() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/api/planos')
    if (data && data.length > 0) {
      planos.value = data
    } else {
      planos.value = fallbackPlanos
    }

    const { data: atual } = await api.get('/api/planos/me/atual')
    if (atual && atual.plano) {
      planoAtualSlug.value = atual.plano
    }
  } catch (e) {
    console.error('Erro ao buscar planos:', e)
    planos.value = fallbackPlanos
  } finally {
    loading.value = false
  }
}

async function handleSelectPlan(plano) {
  if (isCurrentPlan(plano.slug)) return

  changingSlug.value = plano.slug
  try {
    const { data } = await api.post('/api/planos/me/alterar', { slug: plano.slug })
    planoAtualSlug.value = plano.slug
    
    // Atualizar store do usuário
    await authStore.fetchUser()

    toast.add({
      severity: 'success',
      summary: 'Plano Atualizado com Sucesso!',
      detail: data.message || `Você agora está no plano ${plano.nome}. Seus limites foram atualizados!`,
      life: 5000,
    })

    emit('plano-alterado', plano)
    emit('update:visible', false)
  } catch (e) {
    const msg = e.response?.data?.detail || 'Erro ao alterar plano'
    toast.add({
      severity: 'error',
      summary: 'Erro na Troca de Plano',
      detail: msg,
      life: 5000,
    })
  } finally {
    changingSlug.value = null
  }
}

watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      fetchPlanos()
    }
  }
)

onMounted(() => {
  if (props.visible) {
    fetchPlanos()
  }
})
</script>

<style scoped>
.modal-body {
  padding: 0.5rem 1rem 1.5rem 1rem;
}

.modal-header-custom {
  text-align: center;
  margin-bottom: 2rem;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(var(--primary-rgb), 0.1);
  color: var(--primary-600);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(var(--primary-rgb), 0.2);
}

.modal-header-custom h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
  max-width: 600px;
  margin: 0 auto 1.5rem auto;
  line-height: 1.4;
}

/* Toggle Billing */
.billing-toggle-container {
  display: flex;
  justify-content: center;
}

.billing-toggle {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 4px;
  border-radius: 30px;
}

.billing-toggle button {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.5rem 1.25rem;
  border-radius: 24px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.billing-toggle button.active {
  background: var(--primary-500);
  color: white;
  box-shadow: var(--shadow-glow-primary);
}

.discount-badge {
  background: #10b981;
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.15rem 0.4rem;
  border-radius: 10px;
}

/* Plans Grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.plan-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.plan-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary-400);
  box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.3);
}

.plan-card.is-featured {
  border-color: var(--primary-500);
  background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.06) 0%, var(--bg-card) 100%);
  box-shadow: var(--shadow-glow-primary);
}

.plan-card.is-current {
  border-color: #10b981;
}

.popular-tag {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  box-shadow: 0 4px 10px rgba(var(--primary-rgb), 0.4);
}

.plan-card-header {
  margin-bottom: 1.25rem;
}

.plan-badge-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-bottom: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.plan-badge-icon.gratuito { color: #94a3b8; }
.plan-badge-icon.inicial { color: #38bdf8; background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.2); }
.plan-badge-icon.pro { color: var(--primary-500); background: rgba(var(--primary-rgb), 0.12); border-color: rgba(var(--primary-rgb), 0.3); }
.plan-badge-icon.empresarial { color: #f59e0b; background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.2); }

.plan-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.plan-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.35;
  min-height: 38px;
}

/* Pricing */
.plan-pricing {
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.25rem;
}

.price-val {
  display: flex;
  align-items: baseline;
  gap: 0.2rem;
}

.currency {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.amount {
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.amount.free {
  font-size: 1.6rem;
  color: #10b981;
}

.period {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.annual-note {
  display: block;
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.2rem;
}

/* Features */
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.plan-features li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

.check-icon {
  color: #10b981;
  font-size: 0.85rem;
  margin-top: 2px;
  flex-shrink: 0;
}

.times-icon {
  color: var(--text-muted);
  opacity: 0.4;
  font-size: 0.85rem;
  margin-top: 2px;
  flex-shrink: 0;
}

.disabled-feature {
  color: var(--text-muted);
  opacity: 0.6;
}

/* Actions */
.plan-action {
  margin-top: auto;
}

.btn-current {
  background: rgba(16, 185, 129, 0.12) !important;
  color: #10b981 !important;
  border: 1px solid rgba(16, 185, 129, 0.3) !important;
  cursor: default !important;
  opacity: 1 !important;
  font-weight: 600;
}

.btn-featured {
  background: var(--primary-500) !important;
  border-color: var(--primary-500) !important;
  color: white !important;
  font-weight: 600;
  box-shadow: var(--shadow-glow-primary);
}

.btn-select {
  background: var(--bg-card-hover) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
  font-weight: 500;
}

.btn-select:hover {
  background: var(--primary-500) !important;
  border-color: var(--primary-500) !important;
  color: white !important;
}

/* Footer Info */
.modal-footer-info {
  display: flex;
  justify-content: center;
  gap: 2.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.info-item i {
  color: var(--primary-500);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem;
  color: var(--text-muted);
}

@media (max-width: 1024px) {
  .plans-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
  .modal-footer-info {
    flex-direction: column;
    gap: 0.75rem;
    align-items: center;
  }
}
</style>
