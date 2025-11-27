# utils/queries.py

MEDIA_QUERY = '''
query ($search: String, $type: MediaType) {
  Page (perPage: 5) {
    media (search: $search, type: $type, sort: [SEARCH_MATCH, POPULARITY_DESC]) {
      siteUrl
      title { romaji english native }
      description
      coverImage { extraLarge color }
      bannerImage
      averageScore
      status
      episodes
      chapters
      volumes
      genres
      externalLinks { site url }
      studios(isMain: true) { nodes { name } }
      startDate { year }
      relations {
        edges {
          relationType(version: 2)
          node { siteUrl title { romaji english } type }
        }
      }
    }
  }
}
'''

CHARACTER_QUERY = '''
query ($search: String) {
  Page (perPage: 5) {
    characters (search: $search, sort: [SEARCH_MATCH, FAVOURITES_DESC]) {
      siteUrl
      name { full native }
      description
      image { large }
      favourites
      media (sort: POPULARITY_DESC, perPage: 6) {
        nodes {
          title { romaji english }
          siteUrl
          type
        }
      }
    }
  }
}
'''

# --- NEW: USER QUERY ---
USER_QUERY = '''
query ($name: String) {
  User (name: $name) {
    name
    siteUrl
    avatar {
      large
    }
    bannerImage
    about(asHtml: false)
    statistics {
      anime {
        count
        episodesWatched
        minutesWatched
        # CHANGED: limit: 4
        genres(limit: 4, sort: COUNT_DESC) {
          genre
          count
        }
      }
      manga {
        count
        chaptersRead
        volumesRead
      }
    }
  }
}
'''