export interface MovieSearchResult {
  tconst: string
  primarytitle: string
  startyear: string | null
  genres: string | null
  runtimeminutes: number | string | null
  titletype: string | null
  averagerating: number | string | null
  numvotes: number | string | null
}

export interface CastMember {
  category: string | null
  characters: string | null
  primaryname: string
}

export interface MovieDetail extends MovieSearchResult {
  originaltitle: string | null
  endyear: string | null
  isadult: number | string | null
  cast: CastMember[]
}
