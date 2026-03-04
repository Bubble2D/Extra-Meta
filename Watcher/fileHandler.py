import time, os, threading, shutil
from watchdog.events import FileSystemEventHandler
from API_Handler.getSongAPI import SongBPMHandler

class Handler(FileSystemEventHandler):
    def __init__(self, stop_callback, file_queue, config : dict):
        super().__init__()
        self.stop_callback = stop_callback
        self.last_event_time = time.time()
        self.lock = threading.Lock()
        self.file_queue = file_queue
        self.config = config
        self.SongBPM = SongBPMHandler(config)

    def on_created(self, event):
        with self.lock:
            self.last_event_time = time.time()
        self.file_queue.put(event.src_path)

    def on_moved(self, event):
        with self.lock:
            self.last_event_time = time.time()
        self.file_queue.put(event.dest_path)

    def monitor_idle(self):
        """Stoppt den Observer, wenn idle_timeout ohne Events erreicht ist."""
        while True:
            time.sleep(1)
            with self.lock:
                elapsed = time.time() - self.last_event_time
            if elapsed >= self.config["idle_timeout"]: 
                print("Keine Änderungen mehr, Observer wird gestoppt")
                self.stop_callback()
                break

    def mergeMove(self, src, dst): 
        """Verschiebt src nach dst, bestehende Ordner werden zusammengeführt."""
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                self.mergeMove(os.path.join(src, item), os.path.join(dst, item))  
            shutil.rmtree(src)
        else:
            if os.path.exists(dst):
                print(f"Datei existiert bereits, überspringe: {dst}")
                os.remove(src)
            else:
                shutil.move(src, dst)

