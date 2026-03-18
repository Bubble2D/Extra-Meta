from config.config_manager import ConfigManager


def test_read():
    data = {
        "Watcher": {
            "input_path": None,
            "output_path": None,
            "idle_timeout": None,
            "periodic_checks": None,
        },
        "getSongBPM": {
            "API_KEY": None,
            "BACKLINK": None,
            "WEBSITE": None,
            "song_accuracy": 0.75,
        },
    }

    config_manager = ConfigManager()
    assert config_manager.data == data
