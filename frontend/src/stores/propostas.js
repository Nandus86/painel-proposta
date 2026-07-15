import { defineStore } from 'pinia';
import api from '@/services/api';

export const usePropostasStore = defineStore('propostas', {
  state: () => ({
    propostas: [],
    currentProposta: null,
    loading: false,
    error: null,
    aiCredits: {
      used: 0,
      limit: 20,
      remaining: 20
    }
  }),
  actions: {
    async fetchPropostas() {
      this.loading = true;
      try {
        const response = await api.get('/api/propostas');
        this.propostas = response.data.items || [];
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async fetchProposta(id) {
      this.loading = true;
      try {
        const response = await api.get(`/api/propostas/${id}`);
        this.currentProposta = response.data;
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
    async saveProposta(proposta) {
      this.loading = true;
      try {
        let response;
        if (proposta.id) {
          response = await api.put(`/api/propostas/${proposta.id}`, proposta);
        } else {
          response = await api.post('/api/propostas', proposta);
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
