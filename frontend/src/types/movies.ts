export interface MovieSearchResult {
  tconst: string
  primarytitle: string
  imdburl?: string | null
  posterurl?: string | null
  startyear: string | null
  genres: string | null
  runtimeminutes: number | string | null
  titletype: string | null
  averagerating: number | string | null
  numvotes: number | string | null
}

export interface CastMember {
  nconst: string
  ordering?: number | null
  category: string | null
  job?: string | null
  characters: string | null
  imdburl?: string | null
  profileurl?: string | null
  primaryname: string
}

export interface CrewMember {
  nconst: string
  ordering?: number | null
  imdburl?: string | null
  primaryname: string
  profileurl?: string | null
}

export interface AlternateTitle {
  ordering: number | null
  title: string
  region: string | null
  language: string | null
  types: string | null
  attributes: string | null
  isoriginaltitle: number | null
}

export interface MovieDetail extends MovieSearchResult {
  akas: AlternateTitle[]
  akas_count: number
  cast_count: number
  crew: {
    directors: CrewMember[]
    writers: CrewMember[]
  }
  description?: string | null
  description_source?: string | null
  originaltitle: string | null
  endyear: string | null
  isadult: number | string | null
  cast: CastMember[]
}
