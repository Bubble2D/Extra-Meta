import os, tomllib

class ConfigManager:  
    def __init__(self):
        self.data = {  
            "Watcher": {
                "input_path": None,
                "output_path": None,
                "idle_timeout": None,
                "periodic_checks": None
            },
            "getSongBPM": {
                "API_KEY": None,
                "BACKLINK": None,
                "WEBSITE": None
            }
        }
        self.load_data()  

    def get_data(self):
        return self.data

    def get_watcher(self):
        return self.data["Watcher"]

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
