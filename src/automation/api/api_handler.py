import os
import requests

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TBPM, TCON, TXXX, TLEN, APIC
from mutagen.id3 import ID3NoHeaderError

from automation.api.reccobeats import ReccobeatsHandler
from automation.api.lastfm import LastfmHandler


class APIHandler:
    def __init__(self, config):
        self.reccobeats = ReccobeatsHandler(config.get_reccobeats())
        self.lastfm = LastfmHandler(config.get_lastfm())

    def _download_cover(self, url: str) -> bytes | None:
        """Lädt ein Cover-Bild von einer URL herunter."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
            print(f"Cover-Download fehlgeschlagen ({response.status_code}): {url}")
        except requests.exceptions.RequestException as e:
            print(f"Cover-Download Fehler: {e}")
        return None

    def _read_existing_tags(self, filepath: str) -> dict:
        """Liest vorhandene ID3-Tags aus der MP3-Datei."""
        try:
            tags = ID3(filepath)
            return {
                "title": str(tags.get("TIT2", "")),
                "artist": str(tags.get("TPE1", "")),
                "album": str(tags.get("TALB", "")),
                "date": str(tags.get("TDRC", "")),
                "track": str(tags.get("TRCK", "")),
                "length": str(tags.get("TLEN", "")),
                "cover": next(
                    (tags[key] for key in tags if key.startswith("APIC")), None
                ),
            }
        except ID3NoHeaderError:
            return {}

    def _write_tags(self, filepath: str, data: dict):
        """Löscht alle vorhandenen Tags und schreibt neue Metadaten in die MP3-Datei."""
        try:
            tags = ID3(filepath)
            tags.delete(filepath)
        except ID3NoHeaderError:
            pass
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

        for key in (
            "danceability",
            "acousticness",
            "energy",
            "valence",
            "instrumentalness",
            "liveness",
            "loudness",
            "speechiness",
        ):
            if data.get(key) is not None:
                tags[f"TXXX:{key}"] = TXXX(encoding=3, desc=key, text=str(data[key]))

        if data.get("cover"):
            cover = data["cover"]
            if isinstance(cover, APIC):
                tags[cover.HashKey] = cover
                print("Vorhandenes Cover übernommen.")
            elif isinstance(cover, bytes):
                tags["APIC:"] = APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=cover,
                )
                print("Neues Cover eingebettet.")

        tags.save(filepath)
        print(f"Tags gespeichert: {filepath}")

    def process(self, filepath: str):
        """Hauptmethode: liest Datei, fragt APIs, schreibt Tags."""
        if not filepath.lower().endswith(".mp3"):
            print(f"Kein MP3, überspringe: {filepath}")
            return

        existing = self._read_existing_tags(filepath)
        artist = existing.get("artist") or ""
        title = existing.get("title") or os.path.splitext(os.path.basename(filepath))[0]

        if not artist:
            print(f"Kein Artist-Tag gefunden, überspringe: {filepath}")
            return

        # ReccoBeats — Track suchen + Audio Features
        track = self.reccobeats._search_track(title, artist)
        track_id = track.get("id") if track else None
        features = self.reccobeats._get_audio_features(track_id) if track_id else None

        # last.fm — Genre + Cover-URL
        lastfm_data = self.lastfm._get_data(artist, title)

        # Cover: vorhandenes behalten, sonst von last.fm nachladen
        cover = existing.get("cover")
        if not cover and lastfm_data and lastfm_data.get("cover_url"):
            cover = self._download_cover(lastfm_data["cover_url"])

        merged = {
            # Von ReccoBeats
            "title": track.get("trackTitle") if track else existing.get("title"),
            "artist": ", ".join(a["name"] for a in track.get("artists", [])) if track else existing.get("artist"),

            # ReccoBeats hat kein Album/Datum → immer aus existing
            "album": existing.get("album"),
            "date": existing.get("date"),
            "track": existing.get("track"),
            "length": existing.get("length"),

            # Von ReccoBeats Audio Features
            "bpm": features.get("tempo") if features else None,
            "danceability": features.get("danceability") if features else None,
            "acousticness": features.get("acousticness") if features else None,
            "energy": features.get("energy") if features else None,
            "valence": features.get("valence") if features else None,
            "instrumentalness": features.get("instrumentalness") if features else None,
            "liveness": features.get("liveness") if features else None,
            "loudness": features.get("loudness") if features else None,
            "speechiness": features.get("speechiness") if features else None,

            # Von last.fm
            "genre": lastfm_data.get("genre") if lastfm_data else "",

            # Cover: vorhandenes behalten, sonst last.fm
            "cover": cover,
        }
        

        self._write_tags(filepath, merged)
