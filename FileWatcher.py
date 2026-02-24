import time, os, threading, tomllib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def __init__(self, idle_timeout, stop_callback):
        super().__init__()
        self.idle_timeout = idle_timeout
        self.stop_callback = stop_callback
        self.last_event_time = time.time()
        self.lock = threading.Lock()

    def addMetaData(self, event):
        time.sleep(2)
        path = event.src_path if hasattr(event, 'src_path') else event.dest_path
        if path.endswith(".tmp") or path.startswith(".syncthing"):
            return
        print(f"Metadaten hinzufügen für: {path}")

    def on_created(self, event):
        self.addMetaData(event)

    def on_moved(self, event):
        self.addMetaData(event)

    def monitor_idle(self):
        """Stoppt den Observer, wenn idle_timeout ohne Events erreicht ist."""
        while True:
            time.sleep(1)
            with self.lock:
                elapsed = time.time() - self.last_event_time
            if elapsed >= self.idle_timeout:
                print("Keine Änderungen mehr, Observer wird gestoppt")
                self.stop_callback()
                break


def getPath():
    with open("config.toml", "rb") as file:
        data = tomllib.load(file)
    # Default-Pfad, Home ~ expandieren
    path = data.get("Watcher", {"Directory": "~/Musik/input"}).get("Directory")
    return os.path.expanduser(path)

class Watcher:
    observer: Observer
    directory_to_watch: str
    # in seconds
    idle_timeout: int 
    periodic_checks: int 
 
    # limit to 1 observer
    observer_running = False
    observer_lock = threading.Lock()

    def __init__(self, periodic_checks, idle_timeout):
        self.observer = Observer()
        self.directory_to_watch = getPath()
        self.periodic_checks = periodic_checks
        self.idle_timeout = idle_timeout

    def check_empty(self):
        files = os.listdir(self.directory_to_watch)
        return len(files) == 0  

    def start_observer(self):
        with self.observer_lock:
            if self.observer_running:
                # Observer already running
                return
            self.observer_running = True
        
        observer = Observer()

        def stop_observer():
            observer.stop()
            observer.join()
            with self.observer_lock:
                self.observer_running = False
            print("Observer gestoppt")

        event_handler = Handler(idle_timeout=self.idle_timeout, stop_callback=stop_observer)
        observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        observer.start()

        print(f"Observer gestartet für {self.idle_timeout}s...")
        threading.Thread(target=event_handler.monitor_idle, daemon=True).start()         


    def run(self):
        print(f"Starte Watcher für {self.directory_to_watch}")
        try:
            while True:
                if not self.check_empty():
                    print("Änderung gefunden, Observer wird gestartet")
                    self.start_observer()
                else:
                    print("Keine Änderung gefunden, nächster Check in {}s".format(self.periodic_check_seconds))
                time.sleep(self.periodic_checks)
        except KeyboardInterrupt:
            print("Watcher beendet")

if __name__ == '__main__':
    watcher = Watcher(periodic_checks=90, idle_timeout=21)
    watcher.run()
