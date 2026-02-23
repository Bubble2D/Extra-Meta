PLUGIN_NAME = "Extra Metadata"
PLUGIN_AUTHOR = "Bubble2D"
PLUGIN_DESCRIPTION = "Fetch BPM, Key, Danceability, Acousticness, Energy from GetSongBPM"
PLUGIN_VERSION = "1.0.6"
PLUGIN_API_VERSIONS = ["2.2"]

from picard.metadata import register_track_metadata_processor
from picard.plugin import PluginPriority
from picard import log, config
import json
import re

CACHE = {}

if not hasattr(config.setting, "getsongbpm_api_key"):
    config.setting.getsongbpm_api_key = ""
if not hasattr(config.setting, "getsongbpm_backlink"):
    config.setting.getsongbpm_backlink = ""

def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()

def similarity(a, b):
    a, b = normalize(a), normalize(b)
    matches = sum(1 for x, y in zip(a, b) if x == y)
    max_len = max(len(a), len(b))
    return matches / max_len if max_len > 0 else 0

def find_best_match(songs, artist, title):
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
    return best_song if best_score >= 0.75 else None

def apply_features(song, metadata, track):
    if not song:
        return
    if song.get("tempo"):
        metadata["bpm"] = str(song["tempo"])
    if song.get("key"):
        metadata["initialkey"] = song["key"]
    if song.get("danceability") is not None:
        metadata["danceability"] = str(song["danceability"])
    if song.get("acousticness") is not None:
        metadata["acousticness"] = str(song["acousticness"])
    if song.get("energy") is not None:
        metadata["energy"] = str(song["energy"])
    if track:
        track.update()
    log.info(f"GetSongBPM: Applied features to {metadata.get('artist')} - {metadata.get('title')}")

def process_track(album, metadata, track, release):
    artist = metadata.get("artist")
    title = metadata.get("title")
    api_key = config.setting.getsongbpm_api_key
    backlink = config.setting.getsongbpm_backlink

    if not artist or not title or not api_key or not backlink:
        log.debug("Skipping GetSongBPM: missing artist, title, API key or backlink")
        return

    cache_key = f"{artist.strip().lower()}::{title.strip().lower()}"
    if cache_key in CACHE:
        apply_features(CACHE[cache_key], metadata, track)
        return

    from picard.webservice import WebService
    ws = WebService()

    queryargs = {"api_key": api_key, "type": "song", "lookup": f"{artist} {title}"}

    def handle_response(data, reply, error):
        if error:
            log.error(f"GetSongBPM API error: {error}")
            return
        try:
            result = json.loads(data)
            songs = result.get("search", [])
            if not songs:
                log.debug(f"No songs found for {artist} - {title}")
                return
            song = find_best_match(songs, artist, title)
            if song:
                CACHE[cache_key] = song
                apply_features(song, metadata, track)
            else:
                log.debug(f"No suitable match for {artist} - {title}")
        except Exception as e:
            log.error(f"Error parsing GetSongBPM response: {e}")

    ws.get(
        host="api.getsongbpm.com",
        port=443,
        path="/search/",
        handler=handle_response,
        parse_response_type=None,
        queryargs=queryargs,
        use_ssl=True
    )

register_track_metadata_processor(
    process_track,
    priority=PluginPriority.HIGH
)