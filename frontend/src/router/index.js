import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',                       component: () => import('../views/Dashboard.vue') },
  { path: '/project/new',            component: () => import('../views/BriefView.vue') },
  { path: '/project/:id',            component: () => import('../views/SwarmView.vue') },
  { path: '/project/:id/vision',     component: () => import('../views/VisionView.vue') },
  { path: '/project/:id/chat/:domain', component: () => import('../views/AgentChatView.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
