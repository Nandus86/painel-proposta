import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupView.vue'),
    meta: { public: true },
  },
  {
    path: '/p/:token',
    name: 'PublicProposta',
    component: () => import('@/views/PublicPropostaView.vue'),
    meta: { public: true },
  },
  {
    path: '/o/:token',
    name: 'PublicOrcamento',
    component: () => import('@/views/PublicOrcamentoView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'empresa',
        name: 'Empresa',
        component: () => import('../views/EmpresaView.vue'),
      },
      {
        path: 'usuarios',
        name: 'Usuarios',
        component: () => import('../views/UsuariosView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'clientes',
        name: 'Clientes',
        component: () => import('../views/ClientesView.vue'),
      },
      {
        path: 'categorias',
        name: 'Categorias',
        component: () => import('../views/CategoriasView.vue'),
      },
      {
        path: 'servicos',
        name: 'Servicos',
        component: () => import('../views/ServicosView.vue'),
      },
      {
        path: 'propostas',
        name: 'Propostas',
        component: () => import('../views/PropostasView.vue'),
      },
      {
        path: 'propostas/nova',
        name: 'PropostaCreate',
        component: () => import('../views/PropostaEditorView.vue'),
      },
      {
        path: 'propostas/:id/edit',
        name: 'PropostaEdit',
        component: () => import('../views/PropostaEditorView.vue'),
      },
      {
        path: 'orcamentos',
        name: 'Orcamentos',
        component: () => import('../views/OrcamentosView.vue'),
      },
      {
        path: 'orcamentos/novo',
        name: 'OrcamentoCreate',
        component: () => import('../views/OrcamentoEditorView.vue'),
      },
      {
        path: 'orcamentos/:id/edit',
        name: 'OrcamentoEdit',
        component: () => import('../views/OrcamentoEditorView.vue'),
      },
      {
        path: 'configuracoes',
        name: 'Configuracoes',
        component: () => import('../views/ConfiguracoesView.vue'),
      },
      {
        path: 'modelos',
        name: 'ModelosProposta',
        component: () => import('../views/ModelosView.vue'),
      },
      {
        path: 'integracoes',
        name: 'Integracoes',
        component: () => import('../views/IntegracoesView.vue'),
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('../components/layout/SuperAdminLayout.vue'),
    meta: { requiresAuth: true, requiresSuperuser: true },
    children: [
      {
        path: '',
        name: 'SuperAdminDashboard',
        component: () => import('../views/admin/SuperAdminDashboardView.vue'),
      },
      {
        path: 'empresas',
        name: 'SuperAdminEmpresas',
        component: () => import('../views/admin/SuperAdminEmpresasView.vue'),
      },
      {
        path: 'configuracoes',
        name: 'SuperAdminConfig',
        component: () => import('../views/admin/SuperAdminConfigView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth on first load
  if (!authStore.user && localStorage.getItem('access_token')) {
    await authStore.initAuth()
  }

  // Check setup status for authenticated users going to non-setup pages
  if (authStore.isAuthenticated && to.name !== 'Setup' && authStore.setupDone === null) {
    const done = await authStore.checkSetupStatus()
    if (!done) {
      return next({ name: 'Setup' })
    }
  }

  if (to.meta.public) {
    // If authenticated and going to login or register, redirect to dashboard
    if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
      return next({ name: 'Dashboard' })
    }
    return next()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'Login' })
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next({ name: 'Dashboard' })
  }

  if (to.meta.requiresSuperuser && !authStore.isSuperuser) {
    return next({ name: 'Dashboard' })
  }

  next()
})

export default router
