import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { APP_NAME } from '../config/branding'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: 'Entrar', public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { title: 'Criar conta', public: true },
  },
  {
    path: '/esqueci-senha',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPasswordView.vue'),
    meta: { public: true, title: 'Recuperar senha' },
  },
  {
    path: '/redefinir-senha',
    name: 'ResetPassword',
    component: () => import('../views/ResetPasswordView.vue'),
    meta: { public: true, title: 'Nova senha' },
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupView.vue'),
    meta: { requiresAuth: true, title: 'Assistente de configuração' },
  },
  {
    path: '/p/:token',
    name: 'PublicProposta',
    component: () => import('@/views/PublicPropostaView.vue'),
    meta: { title: 'Proposta', public: true },
  },
  {
    path: '/o/:token',
    name: 'PublicOrcamento',
    component: () => import('@/views/PublicOrcamentoView.vue'),
    meta: { title: 'Orçamento', public: true },
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        meta: { title: 'Dashboard' },
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'empresa',
        name: 'Empresa',
        meta: { title: 'Minha Empresa' },
        component: () => import('../views/EmpresaView.vue'),
      },
      {
        path: 'usuarios',
        name: 'Usuarios',
        component: () => import('../views/UsuariosView.vue'),
        meta: { title: 'Usuários', requiresAdmin: true },
      },
      {
        path: 'clientes',
        name: 'Clientes',
        meta: { title: 'Clientes' },
        component: () => import('../views/ClientesView.vue'),
      },
      {
        path: 'categorias',
        name: 'Categorias',
        meta: { title: 'Categorias' },
        component: () => import('../views/CategoriasView.vue'),
      },
      {
        path: 'servicos',
        name: 'Servicos',
        meta: { title: 'Serviços' },
        component: () => import('../views/ServicosView.vue'),
      },
      {
        path: 'propostas',
        name: 'Propostas',
        meta: { title: 'Propostas' },
        component: () => import('../views/PropostasView.vue'),
      },
      {
        path: 'propostas/nova',
        name: 'PropostaCreate',
        meta: { title: 'Nova Proposta' },
        component: () => import('../views/PropostaEditorView.vue'),
      },
      {
        path: 'propostas/:id/edit',
        name: 'PropostaEdit',
        meta: { title: 'Editar Proposta' },
        component: () => import('../views/PropostaEditorView.vue'),
      },
      {
        path: 'orcamentos',
        name: 'Orcamentos',
        meta: { title: 'Orçamentos' },
        component: () => import('../views/OrcamentosView.vue'),
      },
      {
        path: 'orcamentos/novo',
        name: 'OrcamentoCreate',
        meta: { title: 'Novo Orçamento' },
        component: () => import('../views/OrcamentoEditorView.vue'),
      },
      {
        path: 'orcamentos/:id/edit',
        name: 'OrcamentoEdit',
        meta: { title: 'Editar Orçamento' },
        component: () => import('../views/OrcamentoEditorView.vue'),
      },
      {
        path: 'configuracoes',
        name: 'Configuracoes',
        meta: { title: 'Configurações' },
        component: () => import('../views/ConfiguracoesView.vue'),
      },
      {
        path: 'modelos',
        name: 'ModelosProposta',
        meta: { title: 'Modelos de Proposta' },
        component: () => import('../views/ModelosView.vue'),
      },
      {
        path: 'integracoes',
        name: 'Integracoes',
        meta: { title: 'Integrações' },
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
        meta: { title: 'Super Admin' },
        component: () => import('../views/admin/SuperAdminDashboardView.vue'),
      },
      {
        path: 'empresas',
        name: 'SuperAdminEmpresas',
        meta: { title: 'Empresas' },
        component: () => import('../views/admin/SuperAdminEmpresasView.vue'),
      },
      {
        path: 'configuracoes',
        name: 'SuperAdminConfig',
        meta: { title: 'Configurações do Sistema' },
        component: () => import('../views/admin/SuperAdminConfigView.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue'),
    meta: { public: true, title: 'Página não encontrada' },
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

  if (to.meta.public) {
    // If authenticated and going to login or register, redirect to dashboard
    if (['Login', 'Register', 'ForgotPassword'].includes(to.name) && authStore.isAuthenticated) {
      return next({ name: 'Dashboard' })
    }
    return next()
  }

  // Check setup status for authenticated users going to non-setup pages
  if (authStore.isAuthenticated && to.name !== 'Setup' && authStore.setupDone === null) {
    const done = await authStore.checkSetupStatus()
    if (!done) {
      return next({ name: 'Setup' })
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'Login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} })
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next({ name: 'Dashboard' })
  }

  if (to.meta.requiresSuperuser && !authStore.isSuperuser) {
    return next({ name: 'Dashboard' })
  }

  next()
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${APP_NAME}` : APP_NAME
})

export default router
