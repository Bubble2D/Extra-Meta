import requests

from rapidfuzz import fuzz, process


def find_best_match(tracks, artist, title, accuracy):
    query = f"{artist} {title}".lower().strip()
    choices = {
        i: f"{' '.join(a['name'] for a in t.get('artists', []))} {t.get('trackTitle', '')}".lower().strip()
        for i, t in enumerate(tracks)
    }
    result = process.extractOne(query, choices, scorer=fuzz.token_sort_ratio)
    if result and result[1] / 100 >= accuracy:
        best = tracks[result[2]]
        print(f"Bester Match: '{best.get('trackTitle')}' (Score: {result[1]:.0f})")
        return best
    return None


class ReccobeatsHandler:
    def __init__(self, config):
        self.BASE_URL = "https://api.reccobeats.com"
        self.accuracy = float(config["song_accuracy"])
        self.search_limit = config["search_limit"]

    def _get_audio_features(self, track_id: str) -> dict | None:
        """Holt Audio Features für eine Track-ID von ReccoBeats."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/v1/track/{track_id}/audio-features", timeout=10
            )
            if response.status_code == 404:
                print(f"Keine Audio Features für Track-ID: {track_id}")
                return None
            if response.status_code == 429:
                print("ReccoBeats Rate Limit erreicht (429)")
                return None
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"ReccoBeats Audio Features Fehler: {e}")
            return None

    def _search_artist(self, artist: str) -> str | None:
        """Sucht einen Künstler und gibt die ReccoBeats Artist-ID zurück."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/v1/artist/search", params={"searchText": artist}, timeout=10
            )
            response.raise_for_status()
            results = response.json().get("content", [])
            if not results:
                return None
            # Ersten Treffer nehmen — Künstlername ist eindeutiger als Songtitel
            return results[0].get("id")
        except requests.exceptions.RequestException as e:
            print(f"ReccoBeats Artist-Suche Fehler: {e}")
            return None        

    def _search_track(self, title: str, artist: str) -> dict | None:
        """Sucht einen Track über Artist-ID + vollständige Trackliste."""
        artist_id = self._search_artist(artist)
        if not artist_id:
            print(f"ReccoBeats: Künstler nicht gefunden: {artist}")
            return None
        try:
            all_tracks = []
            page = 0
            while True:
                response = requests.get(
                    f"{self.BASE_URL}/v1/artist/{artist_id}/track",
                    params={"page": page, "size": 50},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                all_tracks.extend(data.get("content", []))

                if page >= data.get("totalPages", 1) - 1:
                    break
                page += 1

            if not all_tracks:
                print(f"ReccoBeats: keine Tracks für {artist}")
                return None

            return find_best_match(all_tracks, artist, title, self.accuracy)

        except requests.exceptions.RequestException as e:
            print(f"ReccoBeats Track-Suche Fehler: {e}")
            return None
