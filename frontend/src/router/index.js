import { createRouter, createWebHistory } from 'vue-router'
import JsonDataManagement from '../views/JsonDataManagement.vue'
import OutputResults from '../views/OutputResults.vue'

const routes = [
  {
    path: '/',
    redirect: '/jsondata'
  },
  {
    path: '/jsondata',
    name: 'JsonDataManagement',
    component: JsonDataManagement,
    meta: { title: '数据管理' }
  },
  {
    path: '/output',
    name: 'OutputResults',
    component: OutputResults,
    meta: { title: '计算结果' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

