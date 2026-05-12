<template>
  <div class="card" role="button" tabindex="0">
    <div class="poster">
      <img
        v-if="movie.posterurl"
        :src="movie.posterurl"
        :alt="`${movie.primarytitle} poster`"
        loading="lazy"
      />
      <div v-else class="poster-fallback">No poster</div>
    </div>

    <div class="type-badge">{{ movie.titletype || 'title' }}</div>
    <h3>{{ movie.primarytitle }}</h3>

    <div class="meta">
      <span>{{ movie.startyear || 'Unknown year' }}</span>
      <span v-if="movie.runtimeminutes && movie.runtimeminutes !== '\\N'">
        {{ movie.runtimeminutes }} min
      </span>
    </div>

    <div class="genres">{{ formatGenres(movie.genres) }}</div>

    <div v-if="movie.averagerating" class="rating">
      <span>⭐ {{ movie.averagerating }}</span>
      <span class="votes">({{ formatVotes(movie.numvotes) }})</span>
    </div>

    <a
      class="imdb-link"
      :href="movie.imdburl || imdbLink(movie.tconst)"
      target="_blank"
      rel="noopener noreferrer"
      @click.stop
    >
      Open on IMDb
    </a>
  </div>
</template>

<script setup lang="ts">
import type { MovieSearchResult } from '@/types/movies'

defineProps<{ movie: MovieSearchResult }>()

function formatGenres(genres: string | null): string {
  if (!genres || genres === '\\N') {
    return 'Genre unknown'
  }

  return genres.split(',').join(' · ')
}

function formatVotes(votes: number | string | null): string {
  if (!votes) {
    return 'no votes'
  }

  const parsedVotes = Number(votes)
  if (Number.isNaN(parsedVotes)) {
    return String(votes)
  }

  if (parsedVotes >= 1000) {
    return `${(parsedVotes / 1000).toFixed(1)}k votes`
  }

  return `${parsedVotes} votes`
}

function imdbLink(tconst: string): string {
  return `https://www.imdb.com/title/${tconst}/`
}
</script>

<style scoped>
.card {
  background: linear-gradient(170deg, #1d1d1d, #151515);
  border: 1px solid #333;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #2d2d2d;
  background: #101010;
  margin-bottom: 0.8rem;
}

.poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.poster-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
  font-size: 0.85rem;
}

.card:hover,
.card:focus-visible {
  border-color: #f5c518;
  transform: translateY(-3px);
  outline: none;
}

.type-badge {
  display: inline-block;
  margin-bottom: 0.5rem;
  padding: 2px 8px;
  background: #2f2f2f;
  border-radius: 12px;
  color: #b6b6b6;
  font-size: 0.7rem;
  text-transform: uppercase;
}

h3 {
  margin: 0 0 0.5rem;
  color: #fff;
  font-size: 1rem;
}

.meta {
  display: flex;
  gap: 0.5rem;
  color: #9a9a9a;
  font-size: 0.85rem;
}

.genres {
  margin-top: 0.35rem;
  color: #b5b5b5;
  font-size: 0.82rem;
}

.rating {
  margin-top: 0.6rem;
  color: #f5c518;
  font-size: 0.9rem;
}

.votes {
  color: #919191;
  margin-left: 0.3rem;
}

.imdb-link {
  display: inline-block;
  margin-top: 0.75rem;
  color: #f5c518;
  text-decoration: none;
  font-size: 0.85rem;
}

.imdb-link:hover {
  text-decoration: underline;
}
</style>
