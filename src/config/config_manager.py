<<<<<<< HEAD
import os, tomllib

class ConfigManager:  
    def __init__(self):
        self.data = {  
=======
import os
import tomllib


class ConfigManager:
    def __init__(self):
        self.data = {
>>>>>>> 666dd07 (WIP restructoring and changing API-Endpoints)
            "Watcher": {
                "input_path": None,
                "output_path": None,
                "idle_timeout": None,
<<<<<<< HEAD
                "periodic_checks": None
            },
            "getSongBPM": {
                "API_KEY": None,
                "BACKLINK": None,
                "WEBSITE": None
            }
        }
        self.load_data()  
=======
                "periodic_checks": None,
            },
            "reccobeats": {"song_accuracy": None, "search_limit": None},
            "lastfm": {"API_KEY": None},
        }
        self.load_data()
>>>>>>> 666dd07 (WIP restructoring and changing API-Endpoints)

    def get_data(self):
        return self.data

    def get_watcher(self):
        return self.data["Watcher"]

<<<<<<< HEAD
    def get_song_bpm(self):
        return self.data["getSongBPM"]

    def load_data(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
        with open(config_path, "rb") as file:
            data = tomllib.load(file)

        self.data["Watcher"]["input_path"] = os.path.expanduser(data.get("Watcher", {}).get("input_directory", "~/Musik/input"))
        self.data["Watcher"]["output_path"] = os.path.expanduser(data.get("Watcher", {}).get("output_directory", "~/Musik/output"))
        self.data["Watcher"]["idle_timeout"] = int(data.get("Watcher", {}).get("idle_timeout", 360))
        self.data["Watcher"]["periodic_checks"] = int(data.get("Watcher", {}).get("periodic_checks", 3600))

        self.data["getSongBPM"]["API_KEY"] = data.get("getSongBPM", {}).get("API_KEY")
        self.data["getSongBPM"]["BACKLINK"] = data.get("getSongBPM", {}).get("BACKLINK")
        self.data["getSongBPM"]["WEBSITE"] = data.get("getSongBPM", {}).get("WEBSITE")
        self.data["getSongBPM"]["song_accuracy"] = float(data.get("getSongBPM", {}).get("song_accuracy", "0.75"))
=======
    def get_reccobeats(self):
        return self.data["reccobeats"]

    def get_lastfm(self):
        return self.data["lastfm"]

    def load_data(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.toml")
        with open(config_path, "rb") as file:
            data = tomllib.load(file)

        self.data["Watcher"]["input_path"] = os.path.expanduser(
            data.get("Watcher", {}).get("input_directory", "~/Musik/input")
        )
        self.data["Watcher"]["output_path"] = os.path.expanduser(
            data.get("Watcher", {}).get("output_directory", "~/Musik/output")
        )
        self.data["Watcher"]["idle_timeout"] = int(
            data.get("Watcher", {}).get("idle_timeout", 360)
        )
        self.data["Watcher"]["periodic_checks"] = int(
            data.get("Watcher", {}).get("periodic_checks", 3600)
        )

        self.data["reccobeats"]["song_accuracy"] = float(
            data.get("reccobeats", {}).get("song_accuracy", 0.75)
        )
        self.data["reccobeats"]["search_limit"] = int(
            data.get("reccobeats", {}).get("search_limit", 10)
        )

        self.data["lastfm"]["API_KEY"] = data.get("lastfm", {}).get("API_KEY", "")
>>>>>>> 666dd07 (WIP restructoring and changing API-Endpoints)
