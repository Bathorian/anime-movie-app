<template>
  <div class="search-page">
    <header>
      <h1>CineSearch</h1>
      <p class="subtitle">Search millions of titles</p>
    </header>

    <div class="search-bar">
      <input
        v-model="query"
        @keyup.enter="startSearch"
        placeholder="Search movies, series..."
        autofocus
      />
      <button @click="startSearch" :disabled="loading">
        {{ loading ? '...' : 'Search' }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="results.length" class="results-grid">
      <MovieCard
        v-for="movie in results"
        :key="movie.tconst"
        :movie="movie"
        @click="goToMovie(movie.tconst)"
      />
    </div>

    <div v-if="results.length" class="pagination">
      <button @click="changePage(-1)" :disabled="page === 1">&larr; Prev</button>
      <span>Page {{ page }}</span>
      <button @click="changePage(1)" :disabled="!hasMore || loading">Next &rarr;</button>
    </div>

    <p v-if="!loading && searched && !results.length" class="no-results">
      No results for "{{ query }}"
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MovieCard from '@/components/MovieCard.vue'
import type { MovieSearchResult } from '@/types/movies'

const route = useRoute()
const router = useRouter()

const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const page = ref(getInitialPage(route.query.page))
const results = ref<MovieSearchResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searched = ref(false)
const hasMore = ref(false)

const PAGE_SIZE = 50

function getInitialPage(routePage: unknown): number {
  const parsed = Number(routePage)
  if (!Number.isInteger(parsed) || parsed < 1) {
    return 1
  }

  return parsed
}

function syncRoute(): void {
  router.replace({
    path: '/',
    query: {
      q: query.value || undefined,
      page: page.value > 1 ? String(page.value) : undefined,
    },
  })
}

function goToMovie(tconst: string): void {
  router.push(`/movie/${tconst}`)
}

function startSearch(): void {
  page.value = 1
  void search()
}

function changePage(direction: number): void {
  page.value = Math.max(1, page.value + direction)
  void search()
}

async function search(): Promise<void> {
  const trimmedQuery = query.value.trim()
  syncRoute()

  if (!trimmedQuery) {
    results.value = []
    searched.value = false
    error.value = null
    hasMore.value = false
    return
  }

  loading.value = true
  error.value = null
  searched.value = true

  try {
    const response = await fetch(
      `/api/movies/search?q=${encodeURIComponent(trimmedQuery)}&page=${page.value}&limit=${PAGE_SIZE}`,
    )

    if (!response.ok) {
      throw new Error('Search request failed')
    }

    const data = (await response.json()) as {
      has_more?: boolean
      results?: MovieSearchResult[]
    }
    results.value = Array.isArray(data.results) ? data.results : []
    hasMore.value = Boolean(data.has_more)
  } catch {
    error.value = 'Something went wrong. Is the backend running?'
    results.value = []
    hasMore.value = false
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (query.value.trim()) {
    void search()
  }
})
</script>

<style scoped>
.search-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
  color: #eee;
}

header {
  text-align: center;
  margin-bottom: 2rem;
}

h1 {
  margin: 0;
  font-size: 3rem;
  color: #f5c518;
  letter-spacing: 0.02em;
}

.subtitle {
  margin-top: 0.45rem;
  color: #aaa;
}

.search-bar {
  display: flex;
  gap: 0.5rem;
  max-width: 620px;
  margin: 0 auto 2rem;
}

input {
  flex: 1;
  padding: 0.8rem 1rem;
  background: #191919;
  border: 1px solid #444;
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
}

input:focus {
  border-color: #f5c518;
  outline: none;
}

button {
  padding: 0.8rem 1.4rem;
  border: none;
  border-radius: 8px;
  background: #f5c518;
  color: #101010;
  cursor: pointer;
  font-weight: 700;
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.error {
  text-align: center;
  color: #ff7f78;
  margin-bottom: 1rem;
}

.no-results {
  margin-top: 2rem;
  text-align: center;
  color: #adadad;
}

@media (max-width: 640px) {
  h1 {
    font-size: 2.2rem;
  }

  .search-bar {
    flex-direction: column;
  }
}
</style>
