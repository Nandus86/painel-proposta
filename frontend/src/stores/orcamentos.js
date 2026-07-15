import { defineStore } from 'pinia';
import api from '@/services/api';

export const useOrcamentosStore = defineStore('orcamentos', {
  state: () => ({
    orcamentos: [],
    currentOrcamento: null,
    loading: false,
    error: null,
    aiCredits: {
      used: 0,
      limit: 20,
      remaining: 20
    }
  }),
  actions: {
    async fetchOrcamentos() {
      this.loading = true;
      try {
        const response = await api.get('/api/orcamentos');
        this.orcamentos = response.data.items || [];
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchOrcamento(id) {
      this.loading = true;
      try {
        const response = await api.get(`/api/orcamentos/${id}`);
        this.currentOrcamento = response.data;
        return response.data;
      } catch (err) {
        this.error = err.message;
        throw err;
      } finally {
        this.loading = false;
      }
    },
    async fetchAiCredits() {
      try {
        const response = await api.get('/api/ai/credits');
        this.aiCredits = response.data;
      } catch (err) {
        console.error('Erro ao buscar créditos de IA:', err);
      }
    },
    async saveOrcamento(orcamento) {
      this.loading = true;
      try {
        let response;
        if (orcamento.id) {
          response = await api.put(`/api/orcamentos/${orcamento.id}`, orcamento);
        } else {
          response = await api.post('/api/orcamentos', orcamento);
        }
        return response.data;
      } catch (err) {
        this.error = err.message;
        throw err;
      } finally {
        this.loading = false;
      }
    }
  }
});
