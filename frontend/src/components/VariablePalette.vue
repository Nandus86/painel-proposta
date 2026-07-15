<template>
  <div class="variable-palette">
    <h4>Variáveis Dinâmicas</h4>
    <p class="palette-desc">Arraste para o editor ou clique para inserir no final do texto.</p>

    <div class="palette-search">
      <InputText v-model="search" placeholder="Filtrar variáveis..." size="small" class="w-full" />
    </div>

    <div v-for="cat in categoriasFiltradas" :key="cat.nome" class="palette-category">
      <div class="category-header" @click="toggleCategory(cat.key, cat.defaultExpanded)">
        <i :class="isExpanded(cat.key, cat.defaultExpanded) ? 'pi pi-chevron-down' : 'pi pi-chevron-right'" class="text-xs"></i>
        <span class="category-name">{{ cat.nome }}</span>
        <span class="category-count">{{ cat.vars.length }}</span>
      </div>

      <div v-show="isExpanded(cat.key, cat.defaultExpanded)" class="category-vars">
        <div
          v-for="v in cat.vars"
          :key="v.tag"
          class="var-chip"
          :style="{ borderColor: v.cor, color: v.cor, background: v.cor + '15' }"
          draggable="true"
          @dragstart="onDragStart($event, v)"
          @click="$emit('insert-var', v.tag)"
        >
          <span class="var-tag">{{ v.tag }}</span>
          <span class="var-name">{{ v.nome }}</span>
        </div>
        <div v-if="cat.vars.length === 0" class="empty-cat">Nenhuma variável encontrada</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, shallowRef } from 'vue'
import InputText from 'primevue/inputtext'
import api from '../services/api'

const emit = defineEmits(['insert-var'])

const search = ref('')
const sistemaVars = shallowRef([])
const customVars = shallowRef([])
const expandedState = ref({})

function isExpanded(key, defaultState) {
  if (expandedState.value[key] !== undefined) {
    return expandedState.value[key]
  }
  return defaultState
}

function toggleCategory(key, defaultState) {
  if (expandedState.value[key] === undefined) {
    expandedState.value[key] = !defaultState
  } else {
    expandedState.value[key] = !expandedState.value[key]
  }
}

const categoriasFiltradas = computed(() => {
  const cats = []

  const catNames = {
    cliente: 'Cliente',
    empresa: 'Empresa',
    proposta: 'Proposta',
    itens: 'Itens e Serviços',
    vendedor: 'Vendedor',
    datas: 'Datas',
  }

  Object.entries(catNames).forEach(([key, nome]) => {
    const sistema = sistemaVars.value.filter(v =>
      v.categoria === key &&
      (search.value === '' ||
       v.tag.toLowerCase().includes(search.value.toLowerCase()) ||
       v.nome.toLowerCase().includes(search.value.toLowerCase()))
    )
    const custom = customVars.value.filter(v =>
      key === 'itens' &&
      (search.value === '' ||
       v.tag.toLowerCase().includes(search.value.toLowerCase()) ||
       v.nome.toLowerCase().includes(search.value.toLowerCase()))
    )

    const all = [...sistema, ...custom.map(c => ({ ...c, categoria: key }))]

    if (all.length > 0 || search.value === '') {
      cats.push({ key, nome, vars: all, defaultExpanded: search.value !== '' || all.length <= 5 })
    }
  })

  if (customVars.value.length > 0 && search.value === '') {
    cats.push({
      key: 'custom',
      nome: 'Customizadas',
      vars: customVars.value.map(c => ({ ...c, categoria: 'custom' })),
      defaultExpanded: true
    })
  }

  return cats
})

function onDragStart(event, v) {
  event.dataTransfer.setData('text/plain', v.tag)
  event.dataTransfer.effectAllowed = 'move'
}

onMounted(async () => {
  try {
    const { data } = await api.get('/api/modelos/variaveis')
    sistemaVars.value = data.sistema
    customVars.value = data.customizadas
  } catch (e) {
    console.error('Erro ao carregar variáveis:', e)
  }
})
</script>

<style scoped>
.variable-palette {
  background: var(--surface-50);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 1rem;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.variable-palette h4 {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.palette-desc {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.palette-search {
  margin-bottom: 0.25rem;
}

.palette-category {
  display: flex;
  flex-direction: column;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0;
  cursor: pointer;
  user-select: none;
}

.category-header:hover .category-name {
  color: var(--text-primary);
}

.category-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.category-count {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-left: auto;
}

.category-vars {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding-left: 0.85rem;
  margin-top: 0.2rem;
}

.var-chip {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  padding: 0.4rem 0.55rem;
  border-radius: 6px;
  border: 1px solid;
  cursor: grab;
  transition: all var(--transition-fast);
  user-select: none;
}

.var-chip:hover {
  transform: translateX(2px);
  filter: brightness(1.05);
}

.var-chip:active {
  cursor: grabbing;
}

.var-tag {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  font-weight: 700;
}

.var-name {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.empty-cat {
  font-size: 0.7rem;
  color: var(--text-muted);
  padding: 0.25rem 0;
}

.text-xs {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.w-full {
  width: 100%;
}
</style>
