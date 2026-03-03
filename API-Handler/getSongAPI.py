import os
import re
import requests
from difflib import SequenceMatcher
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TBPM, TCON, TXXX, TLEN
from mutagen.id3 import ID3NoHeaderError


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
        api_artist = normalize(song.get("artist", {}).get("name", ""))
        api_title = normalize(song.get("song_title", ""))
        score = (similarity(artist_norm, api_artist) + similarity(title_norm, api_title)) / 2
        if score > best_score:
            best_score = score
            best_song = song
    print(f"Bester Match: '{best_song.get('song_title')}' von '{best_song.get('artist', {}).get('name')}' (Score: {best_score:.2f})")
    return best_song if best_score >= accuracy else None


class SongBPMHandler:
    BASE_URL = "https://api.getsongbpm.com"

    def __init__(self, config):
        cfg = config.get_song_bpm()
        self.api_key = cfg["API_KEY"]

    def _search_song(self, title: str, artist: str) -> dict | None:
        """Sucht einen Song und gibt den besten Match zurück."""
        params = {
            "api_key": self.api_key,
            "type": "both",
            "lookup": title,
            "artist": artist
        }
        response = requests.get(f"{self.BASE_URL}/search/", params=params)
        response.raise_for_status()
        results = response.json().get("search", [])
        if not results:
            print(f"Kein Ergebnis für: {artist} - {title}")
            return None
        return find_best_match(results, artist, title, cfg["song_accuracy"])

    def _get_song_details(self, song_id: str) -> dict | None:
        """Holt die Detaildaten eines Songs anhand der ID."""
        params = {
            "api_key": self.api_key,
            "id": song_id
        }
        response = requests.get(f"{self.BASE_URL}/song/", params=params)
        response.raise_for_status()
        return response.json().get("song")

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
        title  = existing.get("title")  or os.path.splitext(os.path.basename(filepath))[0]

        if not artist:
            print(f"Kein Artist-Tag gefunden, überspringe API: {filepath}")
            return

        # Besten Match direkt aus search holen
        best_match = self._search_song(title, artist)
        if not best_match:
            print(f"Kein passender Match gefunden für: {artist} - {title}")
            return

        # Detail-Endpunkt mit ID aus dem Match aufrufen
        details = self._get_song_details(best_match["id"])
        if not details:
            print(f"Keine Details gefunden für Song-ID: {best_match['id']}")
            return

        genres = details.get("artist", {}).get("genres", [])
        genre_str = ", ".join(genres) if genres else ""

        merged = {
            "title":        details.get("title")                   or existing.get("title"),
            "artist":       details.get("artist", {}).get("name")  or existing.get("artist"),
            "album":        existing.get("album"),
            "date":         existing.get("date"),
            "track":        existing.get("track"),
            "length":       existing.get("length"),
            "bpm":          details.get("tempo"),
            "genre":        genre_str,
            "danceability": details.get("danceability"),
            "acousticness": details.get("acousticness"),
        }

        self._write_tags(filepath, merged)
