<template>
  <div class="orcamento-editor fade-in">
    <!-- Header -->
    <div class="editor-header glass mb-4">
      <div class="header-left">
        <Button icon="pi pi-arrow-left" class="p-button-rounded p-button-text p-button-plain" @click="goBack" />
        <div class="header-titles">
          <h2>{{ isEdit ? 'Editar Orcamento' : 'Nova Orcamento' }}</h2>
          <span class="orcamento-id" v-if="isEdit">#{{ orcamento.numero }}</span>
        </div>
      </div>
      <div class="header-actions flex gap-2">
        <Button label="Visualizar Online" icon="pi pi-link" severity="info" text outlined @click="previewOrcamento" />
        <Tag :value="orcamento.status.toUpperCase()" :severity="getStatusSeverity(orcamento.status)" class="status-tag" />
      </div>
    </div>

    <!-- Main Content -->
    <div class="editor-card card mb-4">
      <h3 class="card-title"><i class="pi pi-info-circle mr-2"></i>Informações Gerais</h3>
      <div class="p-fluid grid mt-2">
        <div class="field col-12 md:col-8">
          <label for="titulo" class="font-semibold">Título da Orcamento</label>
          <InputText id="titulo" v-model="orcamento.titulo" placeholder="Ex: Projeto de Consultoria TI" class="w-full" />
        </div>
        <div class="field col-12 md:col-4">
          <label for="status" class="font-semibold">Status</label>
          <Select id="status" v-model="orcamento.status" :options="statusOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="field col-12 md:col-8">
          <label for="cliente" class="font-semibold">Cliente</label>
          <Select id="cliente" v-model="orcamento.cliente_id" :options="clientes" optionLabel="razao_social" optionValue="id" placeholder="Selecione um cliente" filter class="w-full" />
        </div>
        <div class="field col-12 md:col-4">
          <label for="validade" class="font-semibold">Validade (dias)</label>
          <InputNumber id="validade" v-model="orcamento.validade_dias" :min="1" class="w-full" />
        </div>
      </div>
    </div>

    <div class="editor-card card mb-4">
      <div class="flex justify-content-between align-items-center mb-3">
        <h3 class="card-title m-0"><i class="pi pi-list mr-2"></i>Itens da Orcamento</h3>
        <Button label="Adicionar Item" icon="pi pi-plus" class="p-button-text p-button-sm" @click="addItem" />
      </div>
      
      <DataTable :value="orcamento.items" class="p-datatable-sm" responsiveLayout="scroll">
        <Column header="Serviço/Produto">
          <template #body="{ data, index }">
            <Select v-model="data.servico_id" :options="servicos" optionLabel="nome" optionValue="id" placeholder="Selecione..." @change="onServicoChange(index)" filter class="w-full" />
          </template>
        </Column>
        <Column header="Qtd" style="width: 100px">
          <template #body="{ data }">
            <InputNumber v-model="data.quantidade" :min="1" class="w-full" />
          </template>
        </Column>
        <Column header="Preço Unit." style="width: 150px">
          <template #body="{ data }">
            <InputNumber v-model="data.preco_unitario" mode="currency" currency="BRL" locale="pt-BR" class="w-full" />
          </template>
        </Column>
        <Column header="Subtotal" style="width: 140px">
          <template #body="{ data }">
            <div class="subtotal-cell">{{ formatCurrency(data.subtotal) }}</div>
          </template>
        </Column>
        <Column style="width: 50px">
          <template #body="{ index }">
            <Button icon="pi pi-trash" class="p-button-danger p-button-text p-button-rounded" @click="removeItem(index)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Resumo Financeiro at the bottom -->
    <div class="editor-card card resumo-financeiro mb-4">
      <h3 class="card-title"><i class="pi pi-dollar mr-2"></i>Resumo Financeiro</h3>
      <div class="resumo-content mt-3">
        <div class="resumo-row">
          <span>Subtotal</span>
          <span>{{ formatCurrency(orcamento.valor_total) }}</span>
        </div>
        <div class="resumo-row">
          <span>Desconto</span>
          <span class="text-danger-400">R$ 0,00</span>
        </div>
        <div class="resumo-divider"></div>
        <div class="resumo-row total">
          <span>Total Geral</span>
          <span class="total-value">{{ formatCurrency(orcamento.valor_total) }}</span>
        </div>
      </div>
    </div>

    <!-- Actions Below Resumo -->
    <div class="flex flex-column gap-3 mb-6">
      <Button label="Salvar Orcamento" icon="pi pi-check" class="w-full p-button-lg shadow-glow" @click="saveOrcamento" :loading="saving" />
      
      <Button 
        v-if="isEdit && orcamento.token_publico" 
        label="Copiar Link Público" 
        icon="pi pi-share-alt" 
        class="w-full p-button-info p-button-outlined" 
        @click="copyPublicLink" 
      />
      
      <Button label="Cancelar" icon="pi pi-times" class="w-full p-button-secondary p-button-text" @click="goBack" />
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Select from 'primevue/select';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import api from '@/services/api';
import { useOrcamentosStore } from '@/stores/orcamentos';

const router = useRouter();
const route = useRoute();
const toast = useToast();
const orcamentosStore = useOrcamentosStore();

const isEdit = computed(() => !!route.params.id);
const saving = ref(false);

const orcamento = ref({
  numero: '',
  titulo: '',
  cliente_id: null,
  status: 'rascunho',
  validade_dias: 15,
  condicoes_pagamento: '',
  observacoes: '',
  valor_total: 0,
  items: []
});

const statusOptions = [
  { label: 'Rascunho', value: 'rascunho' },
  { label: 'Enviada', value: 'enviada' },
  { label: 'Aceita', value: 'aceita' },
  { label: 'Recusada', value: 'recusada' },
  { label: 'Expirada', value: 'expirada' }
];

const clientes = ref([]);
const servicos = ref([]);

const fetchData = async () => {
  try {
    const [cRes, sRes, eRes] = await Promise.all([
      api.get('/api/clientes'),
      api.get('/api/servicos'),
      api.get('/api/empresas/me')
    ]);
    clientes.value = cRes.data.items;
    servicos.value = sRes.data.items;
    const empresaConfig = eRes.data;

    if (isEdit.value) {
      const pRes = await orcamentosStore.fetchOrcamento(route.params.id);
      orcamento.value = pRes;
    } else {
      addItem(); 
      
      if (empresaConfig.validade_padrao_dias) {
        orcamento.value.validade_dias = empresaConfig.validade_padrao_dias;
      }
    }
  } catch (error) {
    console.error('Erro ao carregar dados:', error);
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar dados', life: 3000 });
  }
};

const addItem = () => {
  orcamento.value.items.push({
    servico_id: null,
    descricao: '',
    quantidade: 1,
    preco_unitario: 0,
    subtotal: 0,
    ordem: orcamento.value.items.length
  });
};

const removeItem = (index) => {
  orcamento.value.items.splice(index, 1);
  calculateTotals();
};

const onServicoChange = (index) => {
  const item = orcamento.value.items[index];
  const servico = servicos.value.find(s => s.id === item.servico_id);
  if (servico) {
    item.descricao = servico.nome;
    item.preco_unitario = servico.preco_base;
    calculateTotals();
  }
};

const calculateTotals = () => {
  let total = 0;
  orcamento.value.items.forEach(item => {
    item.subtotal = (item.quantidade || 0) * (item.preco_unitario || 0);
    total += item.subtotal;
  });
  orcamento.value.valor_total = total;
};

// Auto-calculate when items change
watch(() => orcamento.value.items, () => {
  calculateTotals();
}, { deep: true });

const copyPublicLink = () => {
  const url = `${window.location.origin}/o/${orcamento.value.token_publico}`;
  navigator.clipboard.writeText(url);
  toast.add({ severity: 'info', summary: 'Copiado', detail: 'Link público copiado para a área de transferência', life: 3000 });
};

const saveOrcamento = async () => {
  if (!orcamento.value.cliente_id || !orcamento.value.titulo) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha os campos obrigatórios', life: 3000 });
    return;
  }

  // Fallbacks para campos numéricos que podem vir nulos do InputNumber
  if (orcamento.value.validade_dias === null || orcamento.value.validade_dias === '') {
    orcamento.value.validade_dias = 15;
  }

  orcamento.value.items.forEach(item => {
    if (item.quantidade === null || item.quantidade === '') item.quantidade = 1;
    if (item.preco_unitario === null || item.preco_unitario === '') item.preco_unitario = 0;
    item.subtotal = (item.quantidade * item.preco_unitario) || 0;
  });

  saving.value = true;
  try {
    await orcamentosStore.saveOrcamento(orcamento.value);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Orcamento salva!', life: 3000 });
    router.push({ name: 'Orcamentos' });
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao salvar.', life: 3000 });
  } finally {
    saving.value = false;
  }
};

const goBack = () => router.back();

const getStatusSeverity = (status) => {
  switch (status) {
    case 'rascunho': return 'info';
    case 'enviada': return 'warning';
    case 'aceita': return 'success';
    case 'recusada': return 'danger';
    default: return 'info';
  }
};

const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);

const previewOrcamento = () => {
  if (!orcamento.value.token_publico) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Salve o orçamento primeiro para conseguir visualizar o link online.', life: 3000 });
    return;
  }
  const url = `${window.location.origin}/o/${orcamento.value.token_publico}`;
  window.open(url, '_blank');
};

onMounted(fetchData);
</script>

<style scoped>
.orcamento-editor {
  max-width: 900px;
  margin: 0 auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-radius: var(--border-radius-lg);
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-titles h2 {
  font-size: 1.25rem;
  font-weight: 590; /* Linear strong weight */
  margin: 0;
  letter-spacing: -0.02em;
}

.orcamento-id {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.editor-card {
  padding: 1.5rem;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 590; /* Linear strong weight */
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  letter-spacing: -0.01em;
}

.subtotal-cell {
  font-weight: 590;
  color: var(--text-primary);
}

/* Resumo Financeiro */
.resumo-financeiro {
  background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.05), rgba(var(--accent-rgb), 0.05)) !important;
  border: 1px solid rgba(var(--primary-rgb), 0.2) !important;
}

.resumo-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.resumo-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.resumo-divider {
  height: 1px;
  background: var(--border-color);
  margin: 0.5rem 0;
}

.resumo-row.total {
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 590;
}

.total-value {
  color: var(--primary-600) !important;
}

.shadow-glow {
  box-shadow: var(--shadow-glow-primary);
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
  background: transparent;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 510;
  color: var(--text-muted);
}

:deep(.p-panel-header) {
  background: transparent;
  border: none;
  padding-bottom: 0;
}
</style>
