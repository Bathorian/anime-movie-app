import { createRouter, createWebHistory } from 'vue-router'

import MovieView from '@/views/MovieView.vue'
import SearchView from '@/views/SearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: SearchView },
    { path: '/movie/:tconst', component: MovieView },
  ],
})

export default router
