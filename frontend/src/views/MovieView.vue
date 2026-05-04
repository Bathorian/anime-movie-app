<template>
  <div class="movie-page">
    <button class="back" @click="goBack">&larr; Back</button>

    <p v-if="loading" class="status">Loading...</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <div v-else-if="movie" class="content">
      <header class="header">
        <h1>{{ movie.primarytitle }}</h1>
        <p v-if="movie.originaltitle && movie.originaltitle !== movie.primarytitle" class="original-title">
          {{ movie.originaltitle }}
        </p>

        <div class="meta">
          <span>{{ movie.startyear || 'Unknown year' }}</span>
          <span v-if="movie.endyear && movie.endyear !== '\\N'">- {{ movie.endyear }}</span>
          <span v-if="movie.runtimeminutes && movie.runtimeminutes !== '\\N'">
            {{ movie.runtimeminutes }} min
          </span>
          <span class="type">{{ movie.titletype }}</span>
        </div>
      </header>

      <div v-if="movie.averagerating" class="rating">
        <span class="score">{{ movie.averagerating }}</span>
        <span class="votes">/ 10 · {{ formatVotes(movie.numvotes) }} votes</span>
      </div>

      <div class="genres">
        <span v-for="genre in genres" :key="genre" class="genre-tag">{{ genre }}</span>
      </div>

      <section v-if="movie.cast?.length" class="cast">
        <h2>Cast & Crew</h2>
        <div class="cast-grid">
          <article v-for="person in movie.cast" :key="`${person.primaryname}-${person.category}`" class="person">
            <p class="name">{{ person.primaryname }}</p>
            <p v-if="person.category" class="role">{{ person.category }}</p>
            <p v-if="person.characters && person.characters !== '\\N'" class="character">
              as {{ person.characters }}
            </p>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { MovieDetail } from '@/types/movies'

const route = useRoute()
const router = useRouter()

const movie = ref<MovieDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const genres = computed(() => {
  if (!movie.value?.genres || movie.value.genres === '\\N') {
    return []
  }

  return movie.value.genres.split(',')
})

function goBack(): void {
  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push('/')
}

function formatVotes(votes: number | string | null): string {
  if (!votes) {
    return '0'
  }

  const parsedVotes = Number(votes)
  if (Number.isNaN(parsedVotes)) {
    return String(votes)
  }

  return parsedVotes.toLocaleString()
}

async function loadMovie(tconst: string): Promise<void> {
  loading.value = true
  error.value = null
  movie.value = null

  try {
    const response = await fetch(`/api/movies/${encodeURIComponent(tconst)}`)
    if (!response.ok) {
      throw new Error('Not found')
    }

    movie.value = (await response.json()) as MovieDetail
  } catch {
    error.value = 'Movie not found.'
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.tconst,
  (tconst) => {
    if (typeof tconst !== 'string' || !tconst.trim()) {
      error.value = 'Invalid movie id.'
      return
    }

    void loadMovie(tconst)
  },
  { immediate: true },
)
</script>

<style scoped>
.movie-page {
  max-width: 920px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  color: #ececec;
}

.back {
  margin-bottom: 2rem;
  padding: 0.45rem 1rem;
  border: 1px solid #474747;
  border-radius: 6px;
  background: transparent;
  color: #afafaf;
  cursor: pointer;
}

.back:hover {
  color: #f5c518;
  border-color: #f5c518;
}

.header h1 {
  font-size: 2.6rem;
}

.original-title {
  margin-top: 0.35rem;
  color: #989898;
  font-style: italic;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.6rem;
  color: #aaa;
}

.type {
  border-radius: 999px;
  background: #2f2f2f;
  padding: 0.1rem 0.7rem;
  text-transform: capitalize;
}

.rating {
  margin: 1.5rem 0;
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.score {
  font-size: 2.3rem;
  color: #f5c518;
  font-weight: 700;
}

.votes {
  color: #999;
}

.genres {
  margin-bottom: 2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.genre-tag {
  border: 1px solid #454545;
  border-radius: 999px;
  background: #191919;
  color: #c8c8c8;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

h2 {
  margin-bottom: 1rem;
  color: #f5c518;
}

.cast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 0.9rem;
}

.person {
  background: #171717;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.8rem;
}

.name {
  font-weight: 700;
}

.role {
  margin-top: 0.1rem;
  color: #f5c518;
  text-transform: capitalize;
  font-size: 0.85rem;
}

.character {
  margin-top: 0.25rem;
  color: #9f9f9f;
  font-style: italic;
  font-size: 0.85rem;
}

.status {
  text-align: center;
  color: #b0b0b0;
  padding: 2rem 0;
}

.status.error {
  color: #ff8e88;
}

@media (max-width: 640px) {
  .header h1 {
    font-size: 2rem;
  }
}
</style>
