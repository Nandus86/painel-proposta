<template>
  <div class="public-view surface-200 min-h-screen py-4 md:py-8 flex justify-content-center">
    
    <div v-if="loading" class="flex justify-content-center align-items-center h-screen w-full">
      <i class="pi pi-spin pi-spinner text-primary text-5xl"></i>
    </div>
    
    <div v-else-if="error" class="flex justify-content-center align-items-center h-screen w-full">
      <div class="text-center p-6 card shadow-4 bg-white border-round-xl">
        <i class="pi pi-exclamation-triangle text-red-500 text-6xl mb-4"></i>
        <h2 class="text-900 font-bold text-2xl mb-2">Ops! Tivemos um problema.</h2>
        <p class="text-600 m-0 text-lg">{{ error }}</p>
      </div>
    </div>
    
    <div v-else class="a4-document bg-white w-full shadow-4 flex flex-column">
      
      <!-- Top Decorative Border -->
      <div class="doc-top-border"></div>

      <div class="doc-content">
        <!-- Header Section -->
        <div class="flex flex-column md:flex-row justify-content-between align-items-start mb-6">
          <div class="header-left max-w-20rem">
            <img v-if="proposta.empresa.logo_url" :src="backendUrl(proposta.empresa.logo_url)" alt="Logo" class="max-h-4rem mb-3 object-contain" />
            <h1 class="text-3xl font-bold text-primary m-0 mb-1 line-height-1">{{ proposta.empresa.nome_fantasia || proposta.empresa.razao_social }}</h1>
            <p class="text-500 text-xs font-semibold tracking-wide uppercase m-0 mb-3">Proposta Comercial</p>
            
            <div class="text-600 text-sm line-height-3">
              <p class="m-0">CNPJ: {{ proposta.empresa.cnpj }}</p>
              <p v-if="proposta.empresa.email" class="m-0">Email: {{ proposta.empresa.email }}</p>
              <p v-if="proposta.empresa.telefone" class="m-0">Fone: {{ proposta.empresa.telefone }}</p>
            </div>
          </div>
          
          <div class="header-right text-right">
            <Tag :value="proposta.status.toUpperCase()" :severity="getStatusSeverity(proposta.status)" class="mb-3 px-3 py-1 font-bold shadow-1" />
            <div class="text-700 text-sm line-height-3">
              <p class="m-0"><strong>Proposta </strong>#{{ proposta.numero }}</p>
              <p class="m-0"><strong>Data: </strong>{{ formatDate(proposta.data_emissao) }}</p>
              <p class="m-0" v-if="proposta.data_validade"><strong>Validade: </strong>{{ formatDate(proposta.data_validade) }}</p>
            </div>
          </div>
        </div>

        <hr class="doc-divider mb-6">

        <!-- Informações do Cliente -->
        <div class="mb-6 p-4 surface-50 border-1 surface-border border-round">
          <h3 class="text-600 font-semibold uppercase text-xs m-0 mb-2 tracking-wide">Preparado Para</h3>
          <p class="text-900 font-bold text-lg m-0 mb-1">{{ proposta.cliente.razao_social }}</p>
          <p class="text-700 m-0 text-sm">CNPJ/CPF: {{ proposta.cliente.cnpj_cpf }}</p>
        </div>

        <!-- Título da Proposta -->
        <h2 class="text-2xl font-bold text-800 mb-4">{{ proposta.titulo }}</h2>

        <!-- Apresentação (Markdown renderizado) -->
        <div v-if="proposta.observacoes" class="markdown-content text-800 line-height-3 mb-6" v-html="parsedObservacoes"></div>

        <!-- Tabela de Investimento -->
        <div class="mb-6">
          <h3 class="text-xl font-bold text-800 mb-3">Investimento</h3>
          <table class="doc-table w-full text-left border-collapse">
            <thead>
              <tr>
                <th>Descrição</th>
                <th class="text-center">Qtd</th>
                <th class="text-right">Unitário</th>
                <th class="text-right">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in proposta.items" :key="index">
                <td>{{ item.descricao }}</td>
                <td class="text-center">{{ item.quantidade }}</td>
                <td class="text-right">{{ formatCurrency(item.preco_unitario) }}</td>
                <td class="text-right font-medium">{{ formatCurrency(item.subtotal) }}</td>
              </tr>
              <tr class="total-row">
                <td colspan="3" class="text-right font-bold text-700 uppercase">Total Geral</td>
                <td class="text-right font-bold text-xl text-primary">{{ formatCurrency(proposta.valor_total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Condições de Pagamento -->
        <div v-if="proposta.condicoes_pagamento" class="mb-6">
          <h3 class="text-lg font-bold text-800 mb-2">Condições de Pagamento</h3>
          <div class="text-700 line-height-3 white-space-pre-wrap">{{ proposta.condicoes_pagamento }}</div>
        </div>
      </div>

      <!-- Footer Action Area -->
      <div class="doc-footer surface-50 border-top-1 surface-border">
        
        <div v-if="proposta.status === 'rascunho' || proposta.status === 'enviada'" class="text-center">
          <h3 class="text-900 font-bold mb-2">Aceite da Proposta</h3>
          <p class="text-600 text-sm mb-4">Ao aprovar, você concorda formalmente com os termos e valores apresentados neste documento.</p>
          <Button label="APROVAR PROPOSTA" icon="pi pi-check-circle" size="large" class="p-button-success shadow-glow px-6 py-3 font-bold" @click="aceitarProposta" :loading="saving" />
        </div>

        <div v-else-if="proposta.status === 'aceita'" class="text-center">
          <i class="pi pi-check-circle text-green-500 text-4xl mb-2"></i>
          <h3 class="text-green-800 font-bold mb-1">Proposta Aprovada</h3>
          <p class="text-green-700 text-sm m-0">Assinatura digital registrada em {{ formatDate(proposta.assinatura_data, true) }}</p>
        </div>

        <div v-else class="text-center">
          <i class="pi pi-lock text-500 text-4xl mb-2"></i>
          <h3 class="text-700 font-bold mb-1">Proposta Fechada</h3>
          <p class="text-600 text-sm m-0">Este documento não pode mais ser alterado ou aprovado.</p>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import api from '@/services/api';
import { marked } from 'marked';

const route = useRoute();
const toast = useToast();

const loading = ref(true);
const saving = ref(false);
const error = ref(null);
const proposta = ref(null);

const token = route.params.token;

const backendUrl = (path) => {
  if (!path) return '';
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000';
  return `${baseUrl}${path}`;
};

const loadProposta = async () => {
  try {
    const response = await api.get(`/api/public/propostas/${token}`);
    proposta.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.detail || "Não foi possível carregar a proposta.";
  } finally {
    loading.value = false;
  }
};

const aceitarProposta = async () => {
  saving.value = true;
  try {
    const response = await api.post(`/api/public/propostas/${token}/aceitar`, { aceite: true });
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Proposta aprovada com sucesso!', life: 4000 });
    proposta.value.status = 'aceita';
    proposta.value.assinatura_data = response.data.assinatura_data;
  } catch (err) {
    const msg = err.response?.data?.detail || "Erro ao aprovar proposta.";
    toast.add({ severity: 'error', summary: 'Erro', detail: msg, life: 4000 });
  } finally {
    saving.value = false;
  }
};

const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
const formatDate = (dateStr, includeTime = false) => {
  if (!dateStr) return '';
  const opts = { day: '2-digit', month: '2-digit', year: 'numeric' };
  if (includeTime) {
    opts.hour = '2-digit';
    opts.minute = '2-digit';
  }
  return new Date(dateStr).toLocaleDateString('pt-BR', opts);
};

const getStatusSeverity = (status) => {
  switch (status) {
    case 'rascunho': return 'info';
    case 'enviada': return 'warning';
    case 'aceita': return 'success';
    case 'recusada': return 'danger';
    case 'expirada': return 'danger';
    default: return 'info';
  }
};

const parsedObservacoes = computed(() => {
  if (!proposta.value || !proposta.value.observacoes) return '';
  return marked(proposta.value.observacoes);
});

onMounted(() => {
  loadProposta();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.public-view {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.a4-document {
  max-width: 210mm; /* A4 width */
  min-height: 297mm; /* A4 height */
  margin: 0 auto;
  border-radius: 8px;
  overflow: hidden;
}

.doc-top-border {
  height: 6px;
  width: 100%;
}

.doc-content {
  padding: 40px 50px;
  flex: 1;
}

.doc-divider {
  border: 0;
  border-top: 1px solid var(--surface-300);
}

.doc-table {
  border: 1px solid var(--surface-300);
}
.doc-table th {
  background-color: var(--surface-100);
  color: var(--surface-700);
  font-size: 0.85rem;
  text-transform: uppercase;
  padding: 12px;
  border-bottom: 1px solid var(--surface-300);
}
.doc-table td {
  padding: 12px;
  border-bottom: 1px solid var(--surface-200);
  font-size: 0.95rem;
  color: var(--surface-800);
}
.doc-table tr:last-child td {
  border-bottom: none;
}
.total-row {
  background-color: var(--primary-50);
}
.total-row td {
  border-top: 2px solid var(--primary-color) !important;
  padding-top: 16px;
  padding-bottom: 16px;
}

.doc-footer {
  padding: 40px 50px;
  margin-top: auto;
}

.shadow-glow {
  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
  transition: all 0.3s ease;
}
.shadow-glow:hover {
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.6);
  transform: translateY(-2px);
}

/* Markdown Rendering Styles */
.markdown-content :deep(h1) { font-size: 1.75rem; margin-top: 1.5rem; margin-bottom: 1rem; color: var(--surface-900); }
.markdown-content :deep(h2) { font-size: 1.5rem; margin-top: 1.5rem; margin-bottom: 0.75rem; color: var(--surface-900); }
.markdown-content :deep(h3) { font-size: 1.25rem; margin-top: 1.25rem; margin-bottom: 0.5rem; color: var(--surface-900); }
.markdown-content :deep(p) { margin-bottom: 1rem; line-height: 1.6; }
.markdown-content :deep(ul) { margin-bottom: 1rem; padding-left: 2rem; }
.markdown-content :deep(li) { margin-bottom: 0.5rem; line-height: 1.6; }
.markdown-content :deep(strong) { font-weight: 700; color: var(--surface-900); }

@media (max-width: 768px) {
  .a4-document {
    border-radius: 0;
    min-height: 100vh;
  }
  .doc-content, .doc-footer {
    padding: 24px 20px;
  }
}
</style>
