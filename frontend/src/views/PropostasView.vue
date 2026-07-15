<template>
  <div class="propostas-view fade-in">
    <div class="page-header mb-4">
      <div class="header-info">
        <h2 class="m-0">Propostas Comerciais</h2>
        <p class="text-muted">Gerencie e acompanhe seus orçamentos</p>
      </div>
      <div class="header-actions">
        <Button label="Nova Proposta" icon="pi pi-plus" class="shadow-glow" @click="handleNovoClick" :loading="checkLoading" />
        <Popover ref="reqPopover">
          <div class="p-3" style="max-width: 320px">
            <h3 class="text-sm font-bold mb-2"><i class="pi pi-exclamation-triangle text-orange-500 mr-2"></i>Ação Necessária</h3>
            <p class="text-sm mb-3 text-color-secondary">Para criar uma proposta, você precisa antes:</p>
            <ul class="pl-3 m-0 text-sm mb-3">
              <li v-if="!checks.clientes" class="text-red-500 font-medium mb-1">Cadastrar pelo menos 1 Cliente</li>
              <li v-if="!checks.categorias" class="text-red-500 font-medium mb-1">Cadastrar pelo menos 1 Categoria</li>
              <li v-if="!checks.servicos" class="text-red-500 font-medium mb-1">Cadastrar pelo menos 1 Produto/Serviço</li>
              <li v-if="!checks.modelos" class="text-red-500 font-medium">Criar pelo menos 1 Modelo de Proposta</li>
            </ul>
          </div>
        </Popover>
      </div>
    </div>

    <div class="table-card glass">
      <DataTable 
        :value="propostas" 
        :loading="loading" 
        stripedRows 
        responsiveLayout="stack" 
        breakpoint="960px"
        class="custom-table"
      >
        <template #header>
          <div class="flex justify-content-between align-items-center">
            <div class="table-title">Todas as Propostas</div>
            <span class="p-input-icon-left">
              <i class="pi pi-search" />
              <InputText v-model="filters.search" placeholder="Pesquisar..." @input="fetchPropostas" class="search-input" />
            </span>
          </div>
        </template>

        <Column field="numero" header="Nº" sortable style="width: 100px">
          <template #body="{ data }">
            <span class="numero-badge">#{{ data.numero }}</span>
          </template>
        </Column>
        
        <Column field="titulo" header="Título" sortable>
          <template #body="{ data }">
            <div class="font-bold text-primary">{{ data.titulo }}</div>
          </template>
        </Column>
        
        <Column field="cliente_nome" header="Cliente" sortable></Column>
        
        <Column field="valor_total" header="Valor Total" sortable>
          <template #body="{ data }">
            <span class="font-bold">{{ formatCurrency(data.valor_total) }}</span>
          </template>
        </Column>
        
        <Column field="status" header="Status" sortable>
          <template #body="{ data }">
            <Tag :value="data.status.toUpperCase()" :severity="getStatusSeverity(data.status)" class="status-tag" />
          </template>
        </Column>
        
        <Column field="data_emissao" header="Emissão" sortable>
          <template #body="{ data }">
            <div class="text-xs text-muted">{{ formatDate(data.data_emissao) }}</div>
          </template>
        </Column>

        <Column header="Ações" style="width: 220px">
          <template #body="{ data }">
            <div class="flex gap-2">
              <Button icon="pi pi-eye" severity="info" text rounded @click="previewExistingProposta(data)" v-tooltip="'Visualizar'" />
              <Button icon="pi pi-pencil" severity="secondary" text rounded @click="editProposta(data)" v-tooltip="'Editar'" />
              <Button icon="pi pi-link" severity="success" text rounded @click="copyMagicLink(data)" v-tooltip="'Copiar Link Mágico'" />
              <Button icon="pi pi-envelope" severity="secondary" text rounded @click="sendEmail(data)" v-tooltip="'Enviar via E-mail'" />
              <Button icon="pi pi-whatsapp" severity="success" text rounded @click="sendWhatsapp(data)" v-tooltip="'Enviar via WhatsApp'" />
            </div>
          </template>
        </Column>
        
        <template #empty>
          <div class="empty-state p-5 text-center">
            <i class="pi pi-file-o text-4xl text-muted mb-3"></i>
            <p>Nenhuma proposta encontrada.</p>
            <Button label="Criar Primeira Proposta" icon="pi pi-plus" class="p-button-text" @click="createNew" />
          </div>
        </template>
      </DataTable>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import Popover from 'primevue/popover';
import InputText from 'primevue/inputtext';
import api from '@/services/api';

const router = useRouter();
const toast = useToast();

const propostas = ref([]);
const loading = ref(false);
const totalRecords = ref(0);
const filters = ref({
  search: '',
  status: null
});

const checks = ref({
  clientes: false,
  categorias: false,
  servicos: false,
  modelos: false
});
const checkLoading = ref(false);
const reqPopover = ref(null);

async function checkRequirements() {
  checkLoading.value = true;
  try {
    const [cRes, catRes, sRes, mRes] = await Promise.all([
      api.get('/api/clientes', { params: { limit: 1 } }),
      api.get('/api/categorias', { params: { limit: 1 } }),
      api.get('/api/servicos', { params: { limit: 1 } }),
      api.get('/api/modelos', { params: { limit: 1 } })
    ]);
    checks.value.clientes = cRes.data.total > 0;
    checks.value.categorias = catRes.data.total > 0;
    checks.value.servicos = sRes.data.total > 0;
    checks.value.modelos = mRes.data.length > 0;
  } catch (e) {
    console.error('Erro ao verificar requisitos:', e);
  } finally {
    checkLoading.value = false;
  }
}

const handleNovoClick = (event) => {
  if (!checks.value.clientes || !checks.value.categorias || !checks.value.servicos || !checks.value.modelos) {
    reqPopover.value.toggle(event);
  } else {
    createNew();
  }
};

const fetchPropostas = async () => {
  loading.value = true;
  try {
    const params = {
      skip: 0,
      limit: 100,
      search: filters.value.search
    };
    const response = await api.get('/api/propostas', { params });
    propostas.value = response.data.items;
    totalRecords.value = response.data.total;
  } catch (error) {
    console.error('Erro ao buscar propostas:', error);
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar propostas', life: 3000 });
  } finally {
    loading.value = false;
  }
};

const createNew = () => {
  router.push({ name: 'PropostaCreate' });
};

const editProposta = (proposta) => {
  router.push({ name: 'PropostaEdit', params: { id: proposta.id } });
};

const copyMagicLink = (proposta) => {
  const url = `${window.location.origin}/p/${proposta.token_publico}`;
  navigator.clipboard.writeText(url)
    .then(() => {
      toast.add({ severity: 'success', summary: 'Copiado', detail: 'Link mágico copiado para a área de transferência!', life: 3000 });
    })
    .catch(err => {
      console.error('Erro ao copiar', err);
      toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao copiar o link', life: 3000 });
    });
};

const previewExistingProposta = (proposta) => {
  const url = `${window.location.origin}/p/${proposta.token_publico}`;
  window.open(url, '_blank');
};

const sendProposta = (proposta) => {
  toast.add({ severity: 'success', summary: 'Enviado', detail: 'Proposta enviada para o cliente!', life: 2000 });
};

const sendEmail = async (proposta) => {
  try {
    toast.add({ severity: 'info', summary: 'Enviando...', detail: 'Processando o envio do e-mail.', life: 2000 });
    await api.post(`/api/propostas/${proposta.id}/enviar-email`);
    toast.add({ severity: 'success', summary: 'E-mail', detail: 'E-mail enviado com sucesso para o cliente.', life: 3000 });
  } catch (error) {
    console.error('Erro ao enviar e-mail:', error);
    const msg = error.response?.data?.detail || 'Falha ao enviar o e-mail.';
    toast.add({ severity: 'error', summary: 'Erro', detail: msg, life: 4000 });
  }
};

const sendWhatsapp = (proposta) => {
  const msg = encodeURIComponent(`Olá! Segue o link para a proposta #${proposta.numero} - ${proposta.titulo}: ${window.location.origin}/p/${proposta.token_publico}`);
  window.open(`https://api.whatsapp.com/send?text=${msg}`, '_blank');
};

const getStatusSeverity = (status) => {
  switch (status) {
    case 'rascunho': return 'info';
    case 'enviada': return 'warning';
    case 'aceita': return 'success';
    case 'recusada': return 'danger';
    case 'expirada': return 'secondary';
    default: return 'info';
  }
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
};

onMounted(() => {
  fetchPropostas();
  checkRequirements();
});
</script>

<style scoped>
.propostas-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h2 {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-300), var(--accent-400));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.table-card {
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  padding: 0;
}

.custom-table :deep(.p-datatable-header) {
  background: transparent;
  border: none;
  padding: 1.5rem;
}

.table-title {
  font-weight: 600;
  color: var(--text-secondary);
}

.search-input {
  width: 300px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
}

.numero-badge {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-400);
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-family: monospace;
  font-weight: 700;
}

.status-tag {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.shadow-glow {
  box-shadow: var(--shadow-glow-primary);
}

.text-primary {
  color: var(--primary-400);
}

.pdf-container {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
</style>
