from automation.api.api_handler import APIHandler
from config.config_manager import ConfigManager


def test_search_artist():
    config = ConfigManager()
    api_handler = APIHandler(config)

    assert api_handler.reccobeats._search_artist("Cavetown") is not None

def test_process():
    config = ConfigManager()
    api_handler = APIHandler(config)

    api_handler.process("/home/wym/music/input/01 - Rock That Body.mp3")
