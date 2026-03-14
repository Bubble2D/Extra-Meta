import os, re, requests
from difflib import SequenceMatcher
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TBPM, TCON, TXXX, TLEN
from mutagen.id3 import ID3NoHeaderError

BASE_URL = "https://api.getsong.co"

def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()

def similarity(a, b):
    a, b = normalize(a), normalize(b)
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(songs, artist, title, accuracy):
    artist_norm = normalize(artist)
    title_norm = normalize(title)
    best_score = 0
    best_song = None
    for song in songs:
        artist_data = song.get("artist", {})
        if isinstance(artist_data, str):
            artist_data = {}
        api_artist = normalize(artist_data.get("name", ""))
        api_title = normalize(song.get("title", ""))
        score = (similarity(artist_norm, api_artist) + similarity(title_norm, api_title)) / 2
        if score > best_score:
            best_score = score
            best_song = song
    if best_song:
        print(f"DEBUG song keys: {best_song.keys()}")  # ← neu
        print(f"DEBUG artist raw: {best_song.get('artist')}")  # ← neu
        artist_data = best_song.get("artist", {})
        if isinstance(artist_data, str):
            artist_data = {}
        print(f"Bester Match: '{best_song.get('title')}' von '{artist_data.get('name')}' (Score: {best_score:.2f})")
    return best_song if best_score >= accuracy else None

class SongBPMHandler:
    def __init__(self, config):
        self.cfg = config.get_song_bpm()
        self.api_key = self.cfg["API_KEY"]

    def _search_song(self, title: str, artist: str) -> dict | None:
        params = {
            "api_key": self.api_key,
            "type": "both",
            "lookup": f"song:{title} artist:{artist}"
        }
        try:
            response = requests.get(f"{BASE_URL}/search/", params=params)
            if response.status_code == 403:
                print("API-Zugriff verweigert (403) – Rate Limit oder ungültiger Key")
                return None
            if response.status_code == 429:
                print("Rate Limit erreicht (429) – zu viele Anfragen")
                return None
            response.raise_for_status()
            data = response.json()
            print(f"DEBUG API response: {data}")  # ← neu
            results = data.get("search", [])
            if not results:
                print(f"Kein Ergebnis für: {artist} - {title}")
                return None
            return find_best_match(results, artist, title, self.cfg["song_accuracy"])
        except requests.exceptions.RequestException as e:
            print(f"API-Fehler für '{artist} - {title}': {e}")
            return None   
     
        def _read_existing_tags(self, filepath: str) -> dict:
            """Liest vorhandene ID3-Tags aus der MP3-Datei."""
            try:
                tags = ID3(filepath)
                return {
                    "title":  str(tags.get("TIT2", "")),
                    "artist": str(tags.get("TPE1", "")),
                    "album":  str(tags.get("TALB", "")),
                    "date":   str(tags.get("TDRC", "")),
                    "track":  str(tags.get("TRCK", "")),
                    "length": str(tags.get("TLEN", "")),
                }
            except ID3NoHeaderError:
                return {}

    def _write_tags(self, filepath: str, data: dict):
        """Schreibt alle Metadaten in die MP3-Datei."""
        try:
            tags = ID3(filepath)
        except ID3NoHeaderError:
            tags = ID3()

        if data.get("title"):
            tags["TIT2"] = TIT2(encoding=3, text=data["title"])
        if data.get("artist"):
            tags["TPE1"] = TPE1(encoding=3, text=data["artist"])
        if data.get("album"):
            tags["TALB"] = TALB(encoding=3, text=data["album"])
        if data.get("date"):
            tags["TDRC"] = TDRC(encoding=3, text=data["date"])
        if data.get("track"):
            tags["TRCK"] = TRCK(encoding=3, text=data["track"])
        if data.get("length"):
            tags["TLEN"] = TLEN(encoding=3, text=data["length"])
        if data.get("bpm"):
            tags["TBPM"] = TBPM(encoding=3, text=str(data["bpm"]))
        if data.get("genre"):
            tags["TCON"] = TCON(encoding=3, text=data["genre"])

        for key in ("danceability", "acousticness"):
            if data.get(key) is not None:
                tags[f"TXXX:{key}"] = TXXX(encoding=3, desc=key, text=str(data[key]))

        tags.save(filepath)
        print(f"Tags gespeichert: {filepath}")

    def process(self, filepath: str):
        """Hauptmethode: liest Datei, fragt API, schreibt Tags."""
        if not filepath.lower().endswith(".mp3"):
            print(f"Kein MP3, überspringe: {filepath}")
            return

        existing = self._read_existing_tags(filepath)
        artist = existing.get("artist") or ""
        title  = existing.get("title") or os.path.splitext(os.path.basename(filepath))[0]

        if not artist:
            print(f"Kein Artist-Tag gefunden, überspringe API: {filepath}")
            return

        match = self._search_song(title, artist)
        if not match:
            print(f"Kein passender Match gefunden für: {artist} - {title}")
            return

        artist_data = match.get("artist", {})
        if isinstance(artist_data, str):
            artist_data = {}

        album_data = match.get("album", {})
        if isinstance(album_data, str):
            album_data = {}

        genres = artist_data.get("genres", [])
        album  = album_data.get("title", "") or existing.get("album")
        date   = str(album_data.get("year", "")) or existing.get("date")

        merged = {
            "title":        match.get("title")      or existing.get("title"),
            "artist":       artist_data.get("name") or existing.get("artist"),
            "album":        album,
            "date":         date,
            "track":        existing.get("track"),
            "length":       existing.get("length"),
            "bpm":          match.get("tempo"),
            "genre":        ", ".join(genres) if genres else "",
            "danceability": match.get("danceability"),
            "acousticness": match.get("acousticness"),
        }

        self._write_tags(filepath, merged)
