import requests


class LastfmHandler:
    def __init__(self, config):
        self.BASE_URL = "https://ws.audioscrobbler.com/2.0/"
        self.API_KEY = config["API_KEY"]

    def _get_data(self, artist: str, title: str) -> dict | None:
        """Holt Genre-Tags und Cover-URL von last.fm."""
        params = {
            "method": "track.getInfo",
            "api_key": self.API_KEY,
            "artist": artist,
            "track": title,
            "autocorrect": 1,
            "format": "json",
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                print(f"last.fm: kein Treffer für {artist} - {title}")
                return None

            track = data.get("track", {})

            tags = track.get("toptags", {}).get("tag", [])
            genres = ", ".join(t["name"] for t in tags[:3])

            images = track.get("album", {}).get("image", [])
            cover_url = next(
                (img["#text"] for img in reversed(images) if img["#text"]), None
            )

            return {
                "genre": genres,
                "cover_url": cover_url,
            }

        except requests.exceptions.RequestException as e:
            print(f"last.fm Fehler: {e}")
            return None
