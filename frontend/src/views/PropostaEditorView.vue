<template>
  <div class="proposta-editor fade-in">
    <!-- Header -->
    <div class="editor-header glass mb-4">
      <div class="header-left">
        <Button icon="pi pi-arrow-left" class="p-button-rounded p-button-text p-button-plain" @click="goBack" />
        <div class="header-titles">
          <h2>{{ isEdit ? 'Editar Proposta' : 'Nova Proposta' }}</h2>
          <span class="proposta-id" v-if="isEdit">#{{ proposta.numero }}</span>
        </div>
      </div>
      <div class="header-actions flex gap-2">
        <Button label="Visualizar Online" icon="pi pi-link" severity="info" text outlined @click="previewProposta" />
        <Tag :value="proposta.status.toUpperCase()" :severity="getStatusSeverity(proposta.status)" class="status-tag" />
      </div>
    </div>

    <div class="flex flex-column gap-4">
      <!-- Informações Gerais -->
      <div class="editor-card card">
        <div class="flex justify-content-between align-items-center mb-2">
          <h3 class="card-title m-0"><i class="pi pi-info-circle mr-2"></i>Informações Gerais</h3>
          <Button label="Importar Orçamento" icon="pi pi-download" class="p-button-text p-button-sm p-button-success" @click="showImportDialog = true" />
        </div>
        <div class="p-fluid grid mt-2">
          <div class="field col-12 md:col-8">
            <label for="titulo" class="font-semibold">Título da Proposta</label>
            <InputText id="titulo" v-model="proposta.titulo" placeholder="Ex: Projeto de Consultoria TI" class="w-full" />
          </div>
          <div class="field col-12 md:col-4">
            <label for="status" class="font-semibold">Status</label>
            <Select id="status" v-model="proposta.status" :options="statusOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="field col-12 md:col-8">
            <label for="cliente" class="font-semibold">Cliente</label>
            <Select id="cliente" v-model="proposta.cliente_id" :options="clientes" optionLabel="razao_social" optionValue="id" placeholder="Selecione um cliente" filter class="w-full" />
          </div>
          <div class="field col-12 md:col-4">
            <label for="validade" class="font-semibold">Validade (dias)</label>
            <InputNumber id="validade" v-model="proposta.validade_dias" :min="1" class="w-full" />
          </div>
        </div>
      </div>

      <!-- Itens da Proposta -->
      <div class="editor-card card">
        <div class="flex justify-content-between align-items-center mb-3">
          <h3 class="card-title m-0"><i class="pi pi-list mr-2"></i>Itens da Proposta</h3>
          <Button label="Adicionar Item" icon="pi pi-plus" class="p-button-text p-button-sm" @click="addItem" />
        </div>
        
        <DataTable :value="proposta.items" class="p-datatable-sm" responsiveLayout="scroll">
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

      <!-- Resumo Financeiro -->
      <div class="editor-card card resumo-financeiro">
        <h3 class="card-title"><i class="pi pi-dollar mr-2"></i>Resumo Financeiro</h3>
        <div class="resumo-content mt-3">
          <div class="resumo-row">
            <span>Subtotal</span>
            <span>{{ formatCurrency(proposta.valor_total) }}</span>
          </div>
          <div class="resumo-row">
            <span>Desconto</span>
            <span class="text-danger-400">R$ 0,00</span>
          </div>
          <div class="resumo-divider"></div>
          <div class="resumo-row total">
            <span>Total Geral</span>
            <span class="total-value">{{ formatCurrency(proposta.valor_total) }}</span>
          </div>
        </div>
      </div>

      <!-- Texto da Proposta -->
      <div class="editor-card card">
        <div class="flex justify-content-between align-items-center mb-2">
          <h3 class="card-title m-0"><i class="pi pi-sparkles mr-2"></i>Texto da Proposta</h3>
          <div class="flex align-items-center gap-2">
            <span class="text-xs text-muted">IA: {{ propostasStore.aiCredits.remaining }} / {{ propostasStore.aiCredits.limit }}</span>
            <Button 
              label="IA" 
              icon="pi pi-bolt" 
              class="p-button-rounded p-button-help p-button-sm p-button-text ai-btn" 
              @click="generateWithIA" 
              :loading="generatingIA"
              :disabled="propostasStore.aiCredits.remaining <= 0"
            />
          </div>
        </div>
        <div class="p-fluid">
          <!-- Template Selection Dropdown -->
          <div class="field mb-3">
            <label for="modelo-seletor" class="text-xs text-muted mb-1">Modelo de Proposta (Molde IA)</label>
            <Select
              id="modelo-seletor"
              v-model="selectedModelo"
              :options="modelos"
              optionLabel="titulo"
              optionValue="id"
              placeholder="Selecione um molde de proposta (opcional)..."
              showClear
              class="w-full"
            />
          </div>
          <div class="field mb-3">
            <label for="ai-context" class="text-xs text-muted mb-1">Instruções para a IA</label>
            <Textarea id="ai-context" v-model="aiContexto" rows="3" class="w-full" placeholder="Diga à IA o que focar (ex: Dar ênfase no prazo curto)..." />
          </div>
          <div class="field">
            <label for="obs" class="text-xs text-muted mb-1">Descrição/Notas</label>
            <Textarea id="obs" v-model="proposta.observacoes" rows="8" class="w-full" placeholder="Use a IA para gerar um texto persuasivo aqui..." />
          </div>
          <div class="field">
            <label for="condicoes" class="text-xs text-muted mb-1">Condições de Pagamento</label>
            <Textarea id="condicoes" v-model="proposta.condicoes_pagamento" rows="3" class="w-full" />
          </div>
        </div>
      </div>

      <!-- Preview da Proposta -->
      <div class="editor-card card preview-section">
        <div class="preview-section-header">
          <div class="preview-title-group">
            <i class="pi pi-eye"></i>
            <h3 class="card-title m-0">Pré-visualização</h3>
            <span class="preview-badge">Visão do cliente</span>
          </div>
          <Button
            :label="previewOpen ? 'Fechar Preview' : 'Abrir Preview'"
            :icon="previewOpen ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
            class="p-button-text p-button-sm p-button-secondary"
            @click="previewOpen = !previewOpen"
          />
        </div>

        <transition name="preview-slide">
          <div v-if="previewOpen" class="preview-document-wrapper mt-3">
            <div class="preview-document bg-white">
              <!-- Top accent bar -->
              <div class="preview-top-bar" :style="previewTopBarStyle"></div>

              <div class="preview-doc-content">
                <!-- Header empresa + proposta -->
                <div class="preview-header-row">
                  <div class="preview-empresa">
                    <img
                      v-if="empresaData && empresaData.logo_url"
                      :src="backendUrl(empresaData.logo_url)"
                      alt="Logo"
                      class="preview-logo"
                    />
                    <h1 class="preview-empresa-nome">{{ empresaData ? (empresaData.nome_fantasia || empresaData.razao_social) : '—' }}</h1>
                    <p class="preview-empresa-sub">Proposta Comercial</p>
                    <div class="preview-empresa-info" v-if="empresaData">
                      <p v-if="empresaData.cnpj">CNPJ: {{ empresaData.cnpj }}</p>
                      <p v-if="empresaData.email">Email: {{ empresaData.email }}</p>
                      <p v-if="empresaData.telefone">Fone: {{ empresaData.telefone }}</p>
                    </div>
                  </div>
                  <div class="preview-meta">
                    <span class="preview-status-pill" :class="'status-' + proposta.status">{{ proposta.status.toUpperCase() }}</span>
                    <div class="preview-meta-info">
                      <p v-if="proposta.numero"><strong>Proposta</strong> #{{ proposta.numero }}</p>
                      <p><strong>Data:</strong> {{ formatDatePreview(new Date()) }}</p>
                      <p v-if="proposta.validade_dias"><strong>Validade:</strong> {{ proposta.validade_dias }} dias</p>
                    </div>
                  </div>
                </div>

                <hr class="preview-divider" />

                <!-- Cliente -->
                <div class="preview-cliente-box" v-if="clienteAtual">
                  <p class="preview-label">Preparado Para</p>
                  <p class="preview-cliente-nome">{{ clienteAtual.razao_social }}</p>
                  <p class="preview-cliente-cnpj" v-if="clienteAtual.cnpj_cpf">CNPJ/CPF: {{ clienteAtual.cnpj_cpf }}</p>
                </div>

                <!-- Título -->
                <h2 class="preview-titulo" v-if="proposta.titulo">{{ proposta.titulo }}</h2>

                <!-- Observações (markdown renderizado) -->
                <div
                  v-if="proposta.observacoes"
                  class="preview-markdown"
                  v-html="parsedObservacoes"
                ></div>

                <!-- Tabela de itens -->
                <div class="preview-table-section" v-if="proposta.items && proposta.items.length">
                  <h3 class="preview-section-title">Investimento</h3>
                  <table class="preview-table">
                    <thead>
                      <tr>
                        <th>Descrição</th>
                        <th class="text-center">Qtd</th>
                        <th class="text-right">Unitário</th>
                        <th class="text-right">Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, idx) in proposta.items" :key="idx">
                        <td>{{ item.descricao || '—' }}</td>
                        <td class="text-center">{{ item.quantidade }}</td>
                        <td class="text-right">{{ formatCurrency(item.preco_unitario) }}</td>
                        <td class="text-right fw-medium">{{ formatCurrency(item.subtotal) }}</td>
                      </tr>
                      <tr class="preview-total-row">
                        <td colspan="3" class="text-right">Total Geral</td>
                        <td class="text-right preview-total-value">{{ formatCurrency(proposta.valor_total) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- Condições de pagamento -->
                <div class="preview-condicoes" v-if="proposta.condicoes_pagamento">
                  <h3 class="preview-section-title">Condições de Pagamento</h3>
                  <p class="preview-condicoes-text">{{ proposta.condicoes_pagamento }}</p>
                </div>

                <!-- Footer do documento -->
                <div class="preview-doc-footer">
                  <div class="preview-aceite-area">
                    <i class="pi pi-check-circle"></i>
                    <div>
                      <p class="preview-aceite-title">Aceite da Proposta</p>
                      <p class="preview-aceite-desc">Ao aprovar, o cliente concorda formalmente com os termos e valores apresentados.</p>
                    </div>
                  </div>
                  <button class="preview-aceite-btn" disabled>APROVAR PROPOSTA</button>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Actions -->
      <div class="flex justify-content-end gap-3 mt-2 mb-4">
        <Button label="Cancelar" icon="pi pi-times" class="p-button-secondary p-button-text" @click="goBack" />
        
        <Button 
          v-if="isEdit && proposta.token_publico" 
          label="Copiar Link Público" 
          icon="pi pi-share-alt" 
          class="p-button-info p-button-outlined" 
          @click="copyPublicLink" 
        />
        
        <Button label="Salvar Proposta" icon="pi pi-check" class="p-button-lg shadow-glow" @click="saveProposta" :loading="saving" />
      </div>
    </div>

    <!-- Import Orcamento Dialog -->
    <Dialog v-model:visible="showImportDialog" header="Importar de um Orçamento" :style="{ width: '400px' }" modal>
      <div class="p-fluid">
        <p class="text-sm text-muted mb-4">Escolha um orçamento para preencher automaticamente os dados do cliente e os itens desta proposta.</p>
        <div class="field">
          <label class="font-semibold">Selecione o Orçamento</label>
          <Select v-model="selectedOrcamentoId" :options="orcamentosList" optionLabel="titulo" optionValue="id" placeholder="Orçamentos disponíveis..." filter class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" icon="pi pi-times" class="p-button-text" @click="showImportDialog = false" />
        <Button label="Importar" icon="pi pi-check" @click="importOrcamento" :disabled="!selectedOrcamentoId" />
      </template>
    </Dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { marked } from 'marked';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Select from 'primevue/select';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Textarea from 'primevue/textarea';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import Divider from 'primevue/divider';
import api from '@/services/api';
import { usePropostasStore } from '@/stores/propostas';

const router = useRouter();
const route = useRoute();
const toast = useToast();
const propostasStore = usePropostasStore();

const isEdit = computed(() => !!route.params.id);
const saving = ref(false);
const generatingIA = ref(false);
const aiContexto = ref('');
const modelos = ref([]);
const selectedModelo = ref(null);
const previewOpen = ref(false);
const empresaData = ref(null);

const showImportDialog = ref(false);
const orcamentosList = ref([]);
const selectedOrcamentoId = ref(null);

const proposta = ref({
  numero: '',
  titulo: '',
  cliente_id: null,
  status: 'rascunho',
  validade_dias: 15,
  condicoes_pagamento: '50% entrada, 50% na entrega.',
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
    const [cRes, sRes, eRes, mRes, oRes] = await Promise.all([
      api.get('/api/clientes'),
      api.get('/api/servicos'),
      api.get('/api/empresas/me'),
      api.get('/api/modelos').catch(() => ({ data: [] })),
      api.get('/api/orcamentos?limit=50').catch(() => ({ data: { items: [] } }))
    ]);
    clientes.value = cRes.data.items;
    servicos.value = sRes.data.items;
    const empresaConfig = eRes.data;
    empresaData.value = empresaConfig;
    modelos.value = mRes.data || [];
    orcamentosList.value = oRes.data.items || [];

    // Busca os créditos no store
    await propostasStore.fetchAiCredits();

    if (isEdit.value) {
      const pRes = await propostasStore.fetchProposta(route.params.id);
      proposta.value = pRes;
    } else {
      addItem(); 
      
      const aiPrompt = localStorage.getItem('ai_proposal_prompt');
      if (aiPrompt) {
        localStorage.removeItem('ai_proposal_prompt');
        proposta.value.titulo = 'Proposta de Desenvolvimento Web';
        proposta.value.observacoes = aiPrompt;
        
        // Select first client and service if available to facilitate auto-generation
        if (clientes.value.length > 0) {
          proposta.value.cliente_id = clientes.value[0].id;
        }
        if (servicos.value.length > 0 && proposta.value.items.length > 0) {
          proposta.value.items[0].servico_id = servicos.value[0].id;
          proposta.value.items[0].descricao = servicos.value[0].nome;
          proposta.value.items[0].preco_unitario = servicos.value[0].preco_base;
        }
        
        // Automatically run generation after brief timeout
        setTimeout(() => {
          generateWithIA();
        }, 500);
      } else if (empresaConfig.modelo_proposta_padrao) {
        // Apply default proposal template
        proposta.value.observacoes = empresaConfig.modelo_proposta_padrao;
      }
      
      if (empresaConfig.validade_padrao_dias) {
        proposta.value.validade_dias = empresaConfig.validade_padrao_dias;
      }
    }
  } catch (error) {
    console.error('Erro ao carregar dados:', error);
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar dados', life: 3000 });
  }
};

const addItem = () => {
  proposta.value.items.push({
    servico_id: null,
    descricao: '',
    quantidade: 1,
    preco_unitario: 0,
    subtotal: 0,
    ordem: proposta.value.items.length
  });
};

const removeItem = (index) => {
  proposta.value.items.splice(index, 1);
  calculateTotals();
};

const onServicoChange = (index) => {
  const item = proposta.value.items[index];
  const servico = servicos.value.find(s => s.id === item.servico_id);
  if (servico) {
    item.descricao = servico.nome;
    item.preco_unitario = servico.preco_base;
    calculateTotals();
  }
};

const calculateTotals = () => {
  let total = 0;
  proposta.value.items.forEach(item => {
    item.subtotal = (item.quantidade || 0) * (item.preco_unitario || 0);
    total += item.subtotal;
  });
  proposta.value.valor_total = total;
};

// Auto-calculate when items change
watch(() => proposta.value.items, () => {
  calculateTotals();
}, { deep: true });

const generateWithIA = async () => {
  if (!proposta.value.titulo || proposta.value.items.length === 0 || !proposta.value.items[0].descricao) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha os dados básicos primeiro.', life: 3000 });
    return;
  }

  const cliente = clientes.value.find(c => c.id === proposta.value.cliente_id);
  generatingIA.value = true;
  
  // Find selected template if any
  const template = modelos.value.find(m => m.id === selectedModelo.value);

  try {
    const response = await api.post('/api/ai/proposta/gerar-descricao', {
      titulo: proposta.value.titulo,
      cliente_nome: cliente ? cliente.razao_social : 'Cliente',
      itens_detalhes: proposta.value.items.map(i => {
        const servicoOriginal = servicos.value.find(s => s.id === i.servico_id);
        return {
          descricao: i.descricao,
          quantidade: i.quantidade || 1.0,
          preco_unitario: i.preco_unitario || 0.0,
          subtotal: (i.quantidade || 1.0) * (i.preco_unitario || 0.0),
          instrucoes_ia: servicoOriginal ? servicoOriginal.instrucoes_ia : null
        };
      }),
      modelo_conteudo: template ? template.conteudo : null,
      contexto: aiContexto.value
    });
    
    // Typing Effect
    const fullText = response.data.descricao;
    proposta.value.observacoes = '';
    let i = 0;
    const interval = setInterval(() => {
      proposta.value.observacoes += fullText.charAt(i);
      i++;
      if (i >= fullText.length) {
        clearInterval(interval);
      }
    }, 10);
    
    // Atualiza saldo no front
    await propostasStore.fetchAiCredits();
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Texto gerado!', life: 3000 });
  } catch (error) {
    const errorMsg = error.response?.data?.detail || 'Falha na IA.';
    toast.add({ severity: 'error', summary: 'Erro', detail: errorMsg, life: 4000 });
  } finally {
    generatingIA.value = false;
  }
};

const importOrcamento = async () => {
  if (!selectedOrcamentoId.value) return;
  try {
    const res = await api.get(`/api/orcamentos/${selectedOrcamentoId.value}`);
    const orc = res.data;
    proposta.value.cliente_id = orc.cliente_id;
    proposta.value.titulo = `Proposta baseada em: ${orc.titulo}`;
    proposta.value.items = orc.items.map(item => ({
      servico_id: item.servico_id,
      descricao: item.descricao,
      quantidade: item.quantidade,
      preco_unitario: item.preco_unitario,
      desconto: item.desconto || 0,
      subtotal: item.subtotal,
      ordem: item.ordem
    }));
    proposta.value.orcamento_id = orc.id;
    calculateTotals();
    showImportDialog.value = false;
    toast.add({ severity: 'success', summary: 'Importado', detail: 'Orçamento importado com sucesso.', life: 3000 });
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao importar orçamento.', life: 3000 });
  }
};

const copyPublicLink = () => {
  const url = `${window.location.origin}/p/${proposta.value.token_publico}`;
  navigator.clipboard.writeText(url);
  toast.add({ severity: 'info', summary: 'Copiado', detail: 'Link público copiado para a área de transferência', life: 3000 });
};

const saveProposta = async () => {
  if (!proposta.value.cliente_id || !proposta.value.titulo) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha os campos obrigatórios', life: 3000 });
    return;
  }

  saving.value = true;
  try {
    await propostasStore.saveProposta(proposta.value);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Proposta salva!', life: 3000 });
    router.push({ name: 'Propostas' });
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
const formatDatePreview = (d) => new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });

const clienteAtual = computed(() => clientes.value.find(c => c.id === proposta.value.cliente_id) || null);

const parsedObservacoes = computed(() => {
  if (!proposta.value.observacoes) return '';
  return marked(proposta.value.observacoes);
});

const backendUrl = (path) => {
  if (!path) return '';
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000';
  return `${baseUrl}${path}`;
};

const previewTopBarStyle = computed(() => {
  const cor = empresaData.value?.cor_marca || '#6366f1';
  return { background: `linear-gradient(90deg, ${cor}, ${cor}cc)` };
});

const previewProposta = () => {
  if (!proposta.value.token_publico) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Salve a proposta primeiro para conseguir visualizar o link online.', life: 3000 });
    return;
  }
  const url = `${window.location.origin}/p/${proposta.value.token_publico}`;
  window.open(url, '_blank');
};

onMounted(fetchData);

</script>

<style scoped>
.proposta-editor {
  max-width: 1200px;
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

.proposta-id {
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

.sticky-actions {
  position: sticky;
  top: 2rem;
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

.pdf-container {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* ===== PREVIEW SECTION ===== */
.preview-section {
  border: 1px solid rgba(var(--primary-rgb), 0.25) !important;
  background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.03), transparent) !important;
}

.preview-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-title-group {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.preview-title-group i {
  color: var(--primary-500);
  font-size: 1rem;
}

.preview-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  background: rgba(var(--primary-rgb), 0.12);
  color: var(--primary-500);
  letter-spacing: 0.4px;
  text-transform: uppercase;
}

/* Slide transition */
.preview-slide-enter-active,
.preview-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.preview-slide-enter-from,
.preview-slide-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
.preview-slide-enter-to,
.preview-slide-leave-from {
  opacity: 1;
  max-height: 5000px;
  transform: translateY(0);
}

/* A4 Document */
.preview-document-wrapper {
  background: #e8eaed;
  border-radius: 10px;
  padding: 2rem;
}

.preview-document {
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #1a1a2e;
}

.preview-top-bar {
  height: 6px;
  width: 100%;
}

.preview-doc-content {
  padding: 40px 48px;
}

/* Header */
.preview-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1.5rem;
}

.preview-empresa {
  flex: 1;
}

.preview-logo {
  max-height: 52px;
  max-width: 160px;
  object-fit: contain;
  margin-bottom: 0.75rem;
  display: block;
}

.preview-empresa-nome {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 0.2rem;
  line-height: 1.1;
}

.preview-empresa-sub {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #888;
  margin: 0 0 0.75rem;
}

.preview-empresa-info {
  font-size: 0.82rem;
  color: #666;
  line-height: 1.7;
}
.preview-empresa-info p { margin: 0; }

.preview-meta {
  text-align: right;
  flex-shrink: 0;
}

.preview-meta-info {
  font-size: 0.82rem;
  color: #555;
  line-height: 1.8;
  margin-top: 0.5rem;
}
.preview-meta-info p { margin: 0; }

/* Status Pill */
.preview-status-pill {
  display: inline-block;
  padding: 0.3rem 0.8rem;
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.preview-status-pill.status-rascunho { background: #e0f0ff; color: #1d6fa4; }
.preview-status-pill.status-enviada  { background: #fff3cd; color: #856404; }
.preview-status-pill.status-aceita   { background: #d1fae5; color: #065f46; }
.preview-status-pill.status-recusada { background: #fee2e2; color: #991b1b; }
.preview-status-pill.status-expirada { background: #f3f4f6; color: #6b7280; }

/* Divider */
.preview-divider {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 1.5rem 0;
}

/* Cliente */
.preview-cliente-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}
.preview-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #888;
  margin: 0 0 0.25rem;
}
.preview-cliente-nome {
  font-size: 1.1rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 0.15rem;
}
.preview-cliente-cnpj {
  font-size: 0.82rem;
  color: #666;
  margin: 0;
}

/* Título */
.preview-titulo {
  font-size: 1.4rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 1.25rem;
}

/* Section Titles */
.preview-section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #222;
  margin: 0 0 0.75rem;
}

/* Markdown */
.preview-markdown {
  font-size: 0.95rem;
  line-height: 1.7;
  color: #374151;
  margin-bottom: 2rem;
}
.preview-markdown :deep(h1) { font-size: 1.5rem; margin: 1.25rem 0 0.75rem; color: #111; font-weight: 700; }
.preview-markdown :deep(h2) { font-size: 1.25rem; margin: 1.25rem 0 0.5rem; color: #111; font-weight: 700; }
.preview-markdown :deep(h3) { font-size: 1.1rem; margin: 1rem 0 0.5rem; color: #333; font-weight: 600; }
.preview-markdown :deep(p)  { margin-bottom: 0.85rem; }
.preview-markdown :deep(ul) { padding-left: 1.5rem; margin-bottom: 0.85rem; }
.preview-markdown :deep(li) { margin-bottom: 0.4rem; }
.preview-markdown :deep(strong) { font-weight: 700; color: #111; }

/* Table */
.preview-table-section { margin-bottom: 2rem; }
.preview-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}
.preview-table th {
  background: #f3f4f6;
  color: #555;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 12px 14px;
  border-bottom: 1px solid #e5e7eb;
}
.preview-table td {
  padding: 11px 14px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.9rem;
  color: #374151;
}
.preview-table tbody tr:last-child td { border-bottom: none; }
.preview-total-row td {
  background: #f0f9ff;
  border-top: 2px solid #6366f1 !important;
  font-weight: 700;
  color: #333;
  font-size: 0.95rem;
  padding-top: 14px;
  padding-bottom: 14px;
}
.preview-total-value { color: #6366f1 !important; font-size: 1.1rem; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.fw-medium   { font-weight: 600; }

/* Condições */
.preview-condicoes { margin-bottom: 2rem; }
.preview-condicoes-text {
  font-size: 0.9rem;
  color: #555;
  line-height: 1.7;
  white-space: pre-wrap;
  margin: 0;
}

/* Footer Aceite */
.preview-doc-footer {
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  padding: 2rem 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
}
.preview-aceite-area {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  color: #555;
}
.preview-aceite-area i {
  font-size: 1.5rem;
  color: #22c55e;
  margin-top: 0.2rem;
  flex-shrink: 0;
}
.preview-aceite-title {
  font-size: 1rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 0.25rem;
}
.preview-aceite-desc {
  font-size: 0.82rem;
  color: #888;
  margin: 0;
}
.preview-aceite-btn {
  background: #22c55e;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 2.5rem;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

@media (max-width: 768px) {
  .preview-document-wrapper { padding: 0.75rem; }
  .preview-doc-content { padding: 24px 20px; }
  .preview-header-row { flex-direction: column; }
  .preview-meta { text-align: left; }
  .preview-doc-footer { padding: 1.5rem 1.25rem; }
}
</style>
