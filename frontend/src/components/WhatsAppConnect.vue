<template>
  <div class="whatsapp-connect">
    <div v-if="!configurado" class="wpp-unconfigured">
      <i class="pi pi-exclamation-triangle"></i>
      <p>WhatsApp ainda não foi configurado pelo administrador do sistema.</p>
    </div>

    <div v-else-if="status === 'connected'" class="wpp-connected">
      <div class="wpp-connected-badge">
        <i class="pi pi-whatsapp"></i>
        <span>WhatsApp Conectado</span>
      </div>
      <p v-if="numero" class="wpp-numero">Número: +{{ numero }}</p>
      <Button label="Desconectar WhatsApp" severity="danger" icon="pi pi-times" @click="handleDisconnect" :loading="disconnecting" />
    </div>

    <div v-else-if="loading" class="wpp-loading">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Verificando conexão...</span>
    </div>

    <div v-else class="wpp-disconnected">
      <div class="wpp-box-icon"><i class="pi pi-whatsapp"></i></div>
      <h3>Conectar WhatsApp</h3>
      <p>Escaneie o QR code com o WhatsApp para conectar sua conta.</p>

      <div v-if="qr" class="wpp-qr-container">
        <img :src="'data:image/png;base64,' + qr" alt="QR Code" class="wpp-qr" />
        <p class="wpp-qr-hint">Abra o WhatsApp no seu celular e escaneie o código</p>
      </div>

      <div v-if="paircode" class="wpp-paircode">
        <p>Código de pareamento:</p>
        <code>{{ paircode }}</code>
      </div>

      <div v-if="error" class="wpp-error">{{ error }}</div>

      <Button label="Conectar WhatsApp" icon="pi pi-qrcode" @click="handleConnect" :loading="connecting" />
      <p class="wpp-privacy">
        <i class="pi pi-shield"></i>
        Sua privacidade está protegida. Não temos acesso às suas mensagens.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import api from '../services/api'

const toast = useToast()

const configurado = ref(true)
const status = ref('disconnected')
const numero = ref(null)
const qr = ref(null)
const paircode = ref(null)
const loading = ref(true)
const connecting = ref(false)
const disconnecting = ref(false)
const error = ref('')
let pollInterval = null

async function checkStatus() {
  try {
    const { data } = await api.get('/api/whatsapp/status')
    status.value = data.status || 'disconnected'
    numero.value = data.numero
    if (status.value === 'connected') {
      clearPoll()
      qr.value = null
      paircode.value = null
    }
  } catch (e) {
    if (e.response?.status === 400) {
      configurado.value = false
    }
  } finally {
    loading.value = false
  }
}

function startPoll() {
  clearPoll()
  pollInterval = setInterval(async () => {
    try {
      const { data } = await api.get('/api/whatsapp/status')
      status.value = data.status || 'disconnected'
      numero.value = data.numero
      if (status.value === 'connected') {
        clearPoll()
        qr.value = null
        paircode.value = null
        toast.add({ severity: 'success', summary: 'WhatsApp Conectado', life: 3000 })
      }
    } catch {
      // ignora erros de polling
    }
  }, 3000)
}

function clearPoll() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onBeforeUnmount(clearPoll)

async function handleConnect() {
  error.value = ''
  connecting.value = true
  try {
    const { data } = await api.post('/api/whatsapp/conectar')
    status.value = data.status
    if (data.qr) {
      qr.value = data.qr
    }
    if (data.paircode) {
      paircode.value = data.paircode
    }
    startPoll()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erro ao conectar WhatsApp'
  } finally {
    connecting.value = false
  }
}

async function handleDisconnect() {
  disconnecting.value = true
  try {
    await api.post('/api/whatsapp/desconectar')
    status.value = 'disconnected'
    numero.value = null
    qr.value = null
    toast.add({ severity: 'info', summary: 'WhatsApp Desconectado', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.response?.data?.detail || 'Erro ao desconectar', life: 3000 })
  } finally {
    disconnecting.value = false
  }
}

onMounted(checkStatus)
</script>

<style scoped>
.whatsapp-connect {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.wpp-unconfigured {
  padding: 2rem;
  color: var(--text-muted);
}

.wpp-unconfigured i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.wpp-connected-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.wpp-numero {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.wpp-box-icon {
  width: 64px;
  height: 64px;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin: 0 auto 1rem;
}

.wpp-qr-container {
  margin: 1.5rem 0;
}

.wpp-qr {
  width: 200px;
  height: 200px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.5rem;
}

.wpp-qr-hint {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.wpp-paircode {
  margin: 1rem 0;
}

.wpp-paircode code {
  font-size: 1.2rem;
  letter-spacing: 2px;
  background: var(--bg-card);
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.wpp-error {
  color: #ef4444;
  font-size: 0.85rem;
  margin: 0.5rem 0;
}

.wpp-privacy {
  color: var(--text-muted);
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
}

.wpp-loading {
  padding: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-muted);
}
</style>
