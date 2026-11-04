<template>
  <div class="orcamentos-view fade-in">
    <div class="page-header mb-4">
      <div class="header-info">
        <h2 class="m-0">Orcamentos Comerciais</h2>
        <p class="text-muted">Gerencie e acompanhe seus orçamentos</p>
      </div>
      <div class="header-actions">
        <Button label="Novo Orçamento" icon="pi pi-plus" class="shadow-glow" @click="handleNovoClick" :loading="checkLoading" />
        <Popover ref="reqPopover">
          <div class="p-3" style="max-width: 300px">
            <h3 class="text-sm font-bold mb-2"><i class="pi pi-exclamation-triangle text-orange-500 mr-2"></i>Ação Necessária</h3>
            <p class="text-sm mb-3 text-color-secondary">Para criar um orçamento, você precisa antes:</p>
            <ul class="pl-3 m-0 text-sm mb-3">
              <li v-if="!checks.clientes" class="text-red-500 font-medium mb-1">Cadastrar pelo menos 1 Cliente</li>
              <li v-if="!checks.categorias" class="text-red-500 font-medium mb-1">Cadastrar pelo menos 1 Categoria</li>
              <li v-if="!checks.servicos" class="text-red-500 font-medium">Cadastrar pelo menos 1 Produto/Serviço</li>
            </ul>
          </div>
        </Popover>
      </div>
    </div>

    <!-- Desktop Table View -->
    <div class="desktop-table-container">
      <div class="table-card glass">
        <DataTable 
          :value="orcamentos" 
          :loading="loading" 
          stripedRows 
          responsiveLayout="scroll" 
          class="custom-table"
        >
          <template #header>
            <div class="flex justify-content-between align-items-center table-header-wrapper">
              <div class="table-title">Todos os Orçamentos</div>
              <span class="p-input-icon-left search-icon-wrapper">
                <i class="pi pi-search" />
                <InputText v-model="filters.search" placeholder="Pesquisar..." @input="fetchOrcamentos" class="search-input" />
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
              <Tag :value="statusLabel('orcamento', data.status)" :severity="statusSeverity('orcamento', data.status)" class="status-tag" />
            </template>
          </Column>
          
          <Column field="data_emissao" header="Emissão" sortable>
            <template #body="{ data }">
              <div class="text-xs text-muted">{{ formatDate(data.data_emissao) }}</div>
            </template>
          </Column>

          <Column header="Ações" style="width: 240px; min-width: 220px">
            <template #body="{ data }">
              <div class="action-buttons flex gap-1">
                <Button icon="pi pi-eye" severity="info" text rounded @click="previewExistingOrcamento(data)" v-tooltip="'Visualizar'" />
                <Button icon="pi pi-pencil" severity="secondary" text rounded @click="editOrcamento(data)" v-tooltip="'Editar'" />
                <Button icon="pi pi-file-pdf" severity="help" text rounded @click="downloadPdf(data)" v-tooltip="'Baixar PDF'" />
                <Button icon="pi pi-link" severity="success" text rounded @click="copyMagicLink(data)" v-tooltip="'Copiar Link Mágico'" />
                <Button icon="pi pi-envelope" severity="secondary" text rounded @click="sendEmail(data)" v-tooltip="'Enviar via E-mail'" />
                <Button 
                  icon="pi pi-whatsapp" 
                  :severity="whatsappConectado ? 'success' : 'secondary'" 
                  text 
                  rounded 
                  :disabled="!whatsappConectado || sendingWhatsappId === data.id"
                  :loading="sendingWhatsappId === data.id"
                  @click="sendWhatsapp(data)" 
                  v-tooltip="whatsappConectado ? 'Enviar via WhatsApp' : 'WhatsApp não conectado (conecte em Integrações)'" 
                />
                <Button icon="pi pi-trash" severity="danger" text rounded @click="confirmDelete(data)" v-tooltip="'Excluir'" />
              </div>
            </template>
          </Column>
          
          <template #empty>
            <div class="empty-state p-5 text-center">
              <i class="pi pi-file-o text-4xl text-muted mb-3"></i>
              <p>Nenhum orçamento encontrado.</p>
              <Button label="Criar Primeiro Orçamento" icon="pi pi-plus" class="p-button-text" @click="createNew" />
            </div>
          </template>
        </DataTable>
      </div>
    </div>

    <!-- Mobile Cards View -->
    <div class="mobile-cards-container">
      <div class="mobile-search-bar">
        <span class="p-input-icon-left w-full">
          <i class="pi pi-search" />
          <InputText v-model="filters.search" placeholder="Pesquisar orçamento..." @input="fetchOrcamentos" class="w-full search-input" />
        </span>
      </div>

      <div v-if="loading" class="mobile-loading-state glass">
        <i class="pi pi-spin pi-spinner text-2xl text-primary mb-2"></i>
        <span>Carregando orçamentos...</span>
      </div>

      <div v-else-if="!orcamentos || orcamentos.length === 0" class="mobile-empty-state glass">
        <i class="pi pi-file-o text-4xl text-muted mb-2"></i>
        <p>Nenhum orçamento encontrado.</p>
        <Button label="Criar Primeiro Orçamento" icon="pi pi-plus" size="small" @click="createNew" />
      </div>

      <div v-else class="mobile-card glass" v-for="data in orcamentos" :key="data.id">
        <div class="mobile-card-header">
          <div class="mobile-card-num-title">
            <span class="numero-badge">#{{ data.numero }}</span>
            <span class="mobile-card-title">{{ data.titulo }}</span>
          </div>
          <Tag :value="statusLabel('orcamento', data.status)" :severity="statusSeverity('orcamento', data.status)" class="status-tag" />
        </div>

        <div class="mobile-card-body">
          <div class="mobile-card-info-row">
            <span class="mobile-card-label"><i class="pi pi-user"></i> Cliente</span>
            <span class="mobile-card-value font-medium">{{ data.cliente_nome || '—' }}</span>
          </div>
          <div class="mobile-card-info-row">
            <span class="mobile-card-label"><i class="pi pi-dollar"></i> Valor</span>
            <span class="mobile-card-value font-bold text-primary">{{ formatCurrency(data.valor_total) }}</span>
          </div>
          <div class="mobile-card-info-row">
            <span class="mobile-card-label"><i class="pi pi-calendar"></i> Emissão</span>
            <span class="mobile-card-value text-muted text-xs">{{ formatDate(data.data_emissao) }}</span>
          </div>
        </div>

        <div class="mobile-card-actions">
          <Button icon="pi pi-eye" severity="info" text rounded size="small" @click="previewExistingOrcamento(data)" v-tooltip="'Visualizar'" />
          <Button icon="pi pi-pencil" severity="secondary" text rounded size="small" @click="editOrcamento(data)" v-tooltip="'Editar'" />
          <Button icon="pi pi-file-pdf" severity="help" text rounded size="small" @click="downloadPdf(data)" v-tooltip="'Baixar PDF'" />
          <Button icon="pi pi-link" severity="success" text rounded size="small" @click="copyMagicLink(data)" v-tooltip="'Copiar Link'" />
          <Button icon="pi pi-envelope" severity="secondary" text rounded size="small" @click="sendEmail(data)" v-tooltip="'Enviar E-mail'" />
          <Button 
            icon="pi pi-whatsapp" 
            :severity="whatsappConectado ? 'success' : 'secondary'" 
            text 
            rounded 
            size="small"
            :disabled="!whatsappConectado || sendingWhatsappId === data.id"
            :loading="sendingWhatsappId === data.id"
            @click="sendWhatsapp(data)" 
            v-tooltip="whatsappConectado ? 'WhatsApp' : 'WhatsApp não conectado'" 
          />
          <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="confirmDelete(data)" v-tooltip="'Excluir'" />
        </div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { errorMessage } from '@/utils/errors'
import { statusLabel, statusSeverity } from '@/utils/status';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import { downloadFile } from '@/utils/download';
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
const confirm = useConfirm();

const orcamentos = ref([]);
const loading = ref(false);
const totalRecords = ref(0);
const filters = ref({
  search: '',
  status: null
});
const checks = ref({
  clientes: false,
  categorias: false,
  servicos: false
});
const whatsappConectado = ref(false);
const sendingWhatsappId = ref(null);

async function checkWhatsappStatus() {
  try {
    const { data } = await api.get('/api/empresas/me');
    whatsappConectado.value = Boolean(data.whatsapp_conectado || data.whatsapp_status === 'connected');
  } catch (e) {
    whatsappConectado.value = false;
  }
}
const checkLoading = ref(false);
const reqPopover = ref(null);

async function checkRequirements() {
  checkLoading.value = true;
  try {
    const [cRes, catRes, sRes] = await Promise.all([
      api.get('/api/clientes', { params: { limit: 1 } }),
      api.get('/api/categorias', { params: { limit: 1 } }),
      api.get('/api/servicos', { params: { limit: 1 } })
    ]);
    checks.value.clientes = cRes.data.total > 0;
    checks.value.categorias = catRes.data.total > 0;
    checks.value.servicos = sRes.data.total > 0;
  } catch (e) {
    console.error('Erro ao verificar requisitos:', e);
  } finally {
    checkLoading.value = false;
  }
}

const handleNovoClick = (event) => {
  if (!checks.value.clientes || !checks.value.categorias || !checks.value.servicos) {
    reqPopover.value.toggle(event);
  } else {
    createNew();
  }
};

const fetchOrcamentos = async () => {
  loading.value = true;
  try {
    const params = {
      skip: 0,
      limit: 100,
      search: filters.value.search
    };
    const response = await api.get('/api/orcamentos', { params });
    orcamentos.value = response.data.items;
    totalRecords.value = response.data.total;
  } catch (error) {
    console.error('Erro ao buscar orcamentos:', error);
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar orcamentos', life: 3000 });
  } finally {
    loading.value = false;
  }
};

const createNew = () => {
  router.push({ name: 'OrcamentoCreate' });
};

const editOrcamento = (orcamento) => {
  router.push({ name: 'OrcamentoEdit', params: { id: orcamento.id } });
};

const copyMagicLink = (orcamento) => {
  const url = `${window.location.origin}/o/${orcamento.token_publico}`;
  navigator.clipboard.writeText(url)
    .then(() => {
      toast.add({ severity: 'success', summary: 'Copiado', detail: 'Link mágico copiado para a área de transferência!', life: 3000 });
    })
    .catch(err => {
      console.error('Erro ao copiar', err);
      toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao copiar o link', life: 3000 });
    });
};

const previewExistingOrcamento = (orcamento) => {
  const url = `${window.location.origin}/o/${orcamento.token_publico}`;
  window.open(url, '_blank');
};


const downloadPdf = async (orcamento) => {
  try {
    await downloadFile(`/api/orcamentos/${orcamento.id}/pdf`, `orcamento_${orcamento.numero}.pdf`);
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível gerar o PDF.', life: 4000 });
  }
};

const confirmDelete = (orcamento) => {
  confirm.require({
    message: `Excluir o orçamento #${orcamento.numero} - ${orcamento.titulo}? Esta ação não pode ser desfeita.`,
    header: 'Excluir Orçamento',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancelar',
    acceptLabel: 'Excluir',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/api/orcamentos/${orcamento.id}`);
        toast.add({ severity: 'success', summary: 'Excluído', detail: 'Orçamento excluído com sucesso.', life: 3000 });
        fetchOrcamentos();
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Erro', detail: errorMessage(error, 'Não foi possível excluir.'), life: 5000 });
      }
    },
  });
};

const sendEmail = async (orcamento) => {
  try {
    toast.add({ severity: 'info', summary: 'Enviando...', detail: 'Processando o envio do e-mail.', life: 2000 });
    await api.post(`/api/orcamentos/${orcamento.id}/enviar-email`);
    toast.add({ severity: 'success', summary: 'E-mail', detail: 'E-mail enviado com sucesso para o cliente.', life: 3000 });
  } catch (error) {
    console.error('Erro ao enviar e-mail:', error);
    const msg = errorMessage(error, 'Falha ao enviar o e-mail.');
    toast.add({ severity: 'error', summary: 'Erro', detail: msg, life: 4000 });
  }
};

const sendWhatsapp = async (orcamento) => {
  if (!whatsappConectado.value) {
    toast.add({
      severity: 'warn',
      summary: 'WhatsApp Desconectado',
      detail: 'Conecte seu WhatsApp no menu Integrações antes de enviar.',
      life: 4000
    });
    return;
  }

  sendingWhatsappId.value = orcamento.id;
  try {
    toast.add({ severity: 'info', summary: 'Enviando...', detail: 'Disparando orçamento via WhatsApp...', life: 2500 });
    await api.post(`/api/orcamentos/${orcamento.id}/enviar-whatsapp`);
    toast.add({ severity: 'success', summary: 'WhatsApp Enviado', detail: 'Orçamento enviado com sucesso para o cliente!', life: 3500 });
    if (orcamento.status === 'rascunho') {
      orcamento.status = 'enviado';
    }
  } catch (error) {
    console.error('Erro ao enviar WhatsApp:', error);
    const msg = errorMessage(error, 'Falha ao enviar via WhatsApp.');
    toast.add({ severity: 'error', summary: 'Erro no WhatsApp', detail: msg, life: 5000 });
  } finally {
    sendingWhatsappId.value = null;
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
  fetchOrcamentos();
  checkRequirements();
  checkWhatsappStatus();
});
</script>

<style scoped>
.orcamentos-view {
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
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
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
  max-width: 100%;
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
