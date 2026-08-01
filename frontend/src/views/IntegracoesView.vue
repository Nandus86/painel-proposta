<template>
  <div class="integracoes-view fade-in">
    <div class="page-header">
      <h2>Integrações</h2>
      <p class="page-desc">Conecte sua conta a outros serviços e plataformas.</p>
    </div>

    <div class="content-card glass">
      <h3 class="section-title"><i class="pi pi-whatsapp" style="color:#22c55e;"></i> WhatsApp</h3>
      <p class="section-desc">Envie propostas e orçamentos pelo WhatsApp dos seus clientes.</p>
      <WhatsAppConnect />
    </div>
  </div>
</template>

<script setup>
import WhatsAppConnect from '../components/WhatsAppConnect.vue'
</script>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}
.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
}
.page-desc {
  color: var(--text-muted);
  font-size: 0.95rem;
}
.content-card {
  padding: 2rem;
  border-radius: 12px;
}
.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.section-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}
</style>
