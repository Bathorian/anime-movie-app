<template>
  <div class="movie-page">
    <button class="back" @click="goBack">&larr; Back</button>

    <p v-if="loading" class="status">Loading...</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <div v-else-if="movie" class="content">
      <div class="hero">
        <div class="poster">
          <img
            v-if="movie.posterurl"
            :src="movie.posterurl"
            :alt="`${movie.primarytitle} poster`"
            loading="eager"
          />
          <div v-else class="poster-fallback">No poster</div>
        </div>

        <div class="summary">
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

          <a
            class="imdb-link"
            :href="movie.imdburl || imdbTitleUrl(movie.tconst)"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on IMDb
          </a>

          <div v-if="movie.averagerating" class="rating">
            <span class="score">{{ movie.averagerating }}</span>
            <span class="votes">/ 10 · {{ formatVotes(movie.numvotes) }} votes</span>
          </div>

          <p v-if="movie.description" class="description">
            {{ movie.description }}
          </p>
        </div>
      </div>

      <div class="genres">
        <span v-for="genre in genres" :key="genre" class="genre-tag">{{ genre }}</span>
      </div>

      <section v-if="moviePeople.length" class="cast">
        <h2>People ({{ moviePeople.length }})</h2>
        <div class="cast-grid">
          <article
            v-for="person in moviePeople"
            :key="person.nconst"
            class="person"
          >
            <div class="person-photo">
              <img
                v-if="person.profileurl"
                :src="person.profileurl"
                :alt="`${person.primaryname} photo`"
                loading="lazy"
              />
              <div v-else class="photo-fallback">No image</div>
            </div>
            <p class="name">
              <a
                :href="person.imdburl || imdbNameUrl(person.nconst)"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ person.primaryname }}
              </a>
            </p>
            <ul class="role-list">
              <li v-for="role in person.roles" :key="`${person.nconst}-${role}`" class="role-item">{{ role }}</li>
            </ul>
          </article>
        </div>
      </section>

      <section v-if="movie.akas?.length" class="akas">
        <details class="akas-dropdown">
          <summary>Alternate Titles ({{ movie.akas_count || movie.akas.length }})</summary>
          <div class="akas-list">
            <article
              v-for="aka in movie.akas"
              :key="`${aka.ordering}-${aka.title}-${aka.region || ''}-${aka.language || ''}`"
              class="aka-item"
            >
              <p class="aka-title">{{ aka.title }}</p>
              <p class="aka-meta">{{ formatAkaMeta(aka) }}</p>
            </article>
          </div>
        </details>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { AlternateTitle, CastMember, CrewMember, MovieDetail } from '@/types/movies'

interface MoviePerson {
  imdburl?: string | null
  nconst: string
  primaryname: string
  profileurl?: string | null
  roles: string[]
  sortOrder: number
}

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

const moviePeople = computed<MoviePerson[]>(() => {
  const currentMovie = movie.value
  if (!currentMovie) {
    return []
  }

  const peopleMap = new Map<string, MoviePerson>()
  const roleMap = new Map<string, Set<string>>()

  const ensurePerson = (
    nconst: string,
    name: string,
    imdburl: string | null | undefined,
    profileurl: string | null | undefined,
    ordering: number | null | undefined,
  ): MoviePerson => {
    const existing = peopleMap.get(nconst)
    if (existing) {
      if (!existing.profileurl && profileurl) {
        existing.profileurl = profileurl
      }
      if (!existing.imdburl && imdburl) {
        existing.imdburl = imdburl
      }
      if (Number.isFinite(ordering) && Number(ordering) < existing.sortOrder) {
        existing.sortOrder = Number(ordering)
      }
      return existing
    }

    const person: MoviePerson = {
      imdburl,
      nconst,
      primaryname: name,
      profileurl,
      roles: [],
      sortOrder: Number.isFinite(ordering) ? Number(ordering) : Number.MAX_SAFE_INTEGER,
    }
    peopleMap.set(nconst, person)
    roleMap.set(nconst, new Set<string>())
    return person
  }

  const addRole = (nconst: string, role: string): void => {
    const roleSet = roleMap.get(nconst)
    if (!roleSet || !role) {
      return
    }
    roleSet.add(role)
  }

  for (const castMember of currentMovie.cast ?? []) {
    if (!castMember.nconst) {
      continue
    }

    const person = ensurePerson(
      castMember.nconst,
      castMember.primaryname,
      castMember.imdburl,
      castMember.profileurl,
      castMember.ordering,
    )

    const category = normalizeRole(castMember.category)
    const characters = castMember.characters?.trim()

    if (category && characters) {
      if (isActorCategory(castMember.category)) {
        addRole(person.nconst, `${category} as ${characters}`)
      } else {
        addRole(person.nconst, `${category}: ${characters}`)
      }
    } else if (category) {
      addRole(person.nconst, category)
    }

    const job = castMember.job?.trim()
    if (job) {
      addRole(person.nconst, normalizeRole(job))
    }
  }

  const addCrewRole = (member: CrewMember, role: string): void => {
    if (!member.nconst) {
      return
    }
    const person = ensurePerson(
      member.nconst,
      member.primaryname,
      member.imdburl,
      member.profileurl,
      member.ordering,
    )
    addRole(person.nconst, role)
  }

  for (const director of currentMovie.crew?.directors ?? []) {
    addCrewRole(director, 'Director')
  }

  for (const writer of currentMovie.crew?.writers ?? []) {
    addCrewRole(writer, 'Writer')
  }

  const people = Array.from(peopleMap.values()).map((person) => {
    const roles = Array.from(roleMap.get(person.nconst) ?? [])
    return {
      ...person,
      roles,
    }
  })

  return people.sort((a, b) => {
    const priorityDiff = rolePriority(a.roles) - rolePriority(b.roles)
    if (priorityDiff !== 0) {
      return priorityDiff
    }

    if (a.sortOrder !== b.sortOrder) {
      return a.sortOrder - b.sortOrder
    }

    return a.primaryname.localeCompare(b.primaryname)
  })
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

function imdbTitleUrl(tconst: string): string {
  return `https://www.imdb.com/title/${tconst}/`
}

function imdbNameUrl(nconst: string): string {
  return `https://www.imdb.com/name/${nconst}/`
}

function normalizeRole(value: string | null | undefined): string {
  if (!value) {
    return ''
  }

  return value
    .split(/[\s_-]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function isActorCategory(category: string | null): boolean {
  if (!category) {
    return false
  }

  return ['actor', 'actress', 'self'].includes(category.toLowerCase())
}

function rolePriority(roles: string[]): number {
  const normalized = roles.map((role) => role.toLowerCase())
  if (normalized.some((role) => role.startsWith('actor') || role.startsWith('actress') || role.startsWith('self'))) {
    return 0
  }
  if (normalized.some((role) => role === 'director')) {
    return 1
  }
  return 2
}

function formatAkaMeta(aka: AlternateTitle): string {
  const parts = [aka.region, aka.language, aka.types, aka.attributes].filter(Boolean)
  if (parts.length === 0) {
    return 'No extra metadata'
  }

  return parts.join(' · ')
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

.hero {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 1.2rem;
  margin-bottom: 1.2rem;
}

.summary {
  min-width: 0;
}

.poster {
  border: 1px solid #343434;
  border-radius: 10px;
  overflow: hidden;
  background: #111;
  aspect-ratio: 2 / 3;
}

.poster img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8f8f8f;
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

.imdb-link {
  display: inline-block;
  margin-top: 0.6rem;
  color: #f5c518;
  text-decoration: none;
}

.imdb-link:hover {
  text-decoration: underline;
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

.description {
  margin-top: 0.6rem;
  color: #c7c7c7;
  line-height: 1.5;
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

.person-photo {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #2c2c2c;
  background: #101010;
  margin-bottom: 0.55rem;
}

.person-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.photo-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #757575;
  font-size: 0.8rem;
}

.name {
  font-weight: 700;
  margin-bottom: 0.45rem;
}

.name a {
  color: inherit;
  text-decoration: none;
}

.name a:hover {
  color: #f5c518;
}

.role-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

.role-item {
  color: #a9a9a9;
  font-size: 0.82rem;
  line-height: 1.25;
}

.akas {
  margin-top: 2rem;
}

.akas-dropdown {
  border: 1px solid #313131;
  border-radius: 8px;
  background: #121212;
  padding: 0.75rem;
}

.akas-dropdown summary {
  cursor: pointer;
  color: #f5c518;
  font-weight: 700;
  list-style: none;
}

.akas-dropdown summary::-webkit-details-marker {
  display: none;
}

.akas-dropdown summary::before {
  content: '▸';
  display: inline-block;
  margin-right: 0.5rem;
  transition: transform 0.2s ease;
}

.akas-dropdown[open] summary::before {
  transform: rotate(90deg);
}

.akas-list {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.aka-item {
  background: #161616;
  border: 1px solid #313131;
  border-radius: 8px;
  padding: 0.7rem 0.8rem;
}

.aka-title {
  margin: 0;
  color: #ededed;
}

.aka-meta {
  margin: 0.25rem 0 0;
  color: #a3a3a3;
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
  .hero {
    grid-template-columns: 1fr;
  }

  .poster {
    max-width: 260px;
    margin: 0 auto;
  }

  .header h1 {
    font-size: 2rem;
  }
}
</style>
