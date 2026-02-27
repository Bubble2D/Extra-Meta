import time, os, threading, tomllib, queue, shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def mergeMove(src, dst):
    """Verschiebt src nach dst, bestehende Ordner werden zusammengeführt."""
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            mergeMove(os.path.join(src, item), os.path.join(dst, item))
        # Ordner leeren und löschen (übrig gebliebene Duplikate entfernen)
        shutil.rmtree(src)
    else:
        if os.path.exists(dst):
            print(f"Datei existiert bereits, überspringe: {dst}")
            os.remove(src)  # Duplikat aus Input löschen
        else:
            shutil.move(src, dst)

def configuerData(filepath):
    output_dir = getOutputPath()
    time.sleep(1)

    if not os.path.exists(filepath):
        print(f"Datei nicht mehr vorhanden, überspringe: {filepath}")
        return

    basename = os.path.basename(filepath)
    if basename.endswith(".tmp") or basename.startswith(".syncthing"):
        return

    output = os.path.join(output_dir, basename)
    print(f"Verarbeite: {filepath}")
    mergeMove(filepath, output)

def getInputPath():
    with open("config.toml", "rb") as file:
        data = tomllib.load(file)
    path = data.get("Watcher", {}).get("input_directory", "~/Musik/input")
    return os.path.expanduser(path)


def getOutputPath():
    with open("config.toml", "rb") as file:
        data = tomllib.load(file)
    path = data.get("Watcher", {}).get("output_directory", "~/Musik/output")
    return os.path.expanduser(path)


class Handler(FileSystemEventHandler):
    def __init__(self, idle_timeout, stop_callback, file_queue):
        super().__init__()
        self.idle_timeout = idle_timeout
        self.stop_callback = stop_callback
        self.last_event_time = time.time()
        self.lock = threading.Lock()
        self.file_queue = file_queue

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
            if elapsed >= self.idle_timeout:
                print("Keine Änderungen mehr, Observer wird gestoppt")
                self.stop_callback()
                break


class Watcher:
    observer: Observer
    directory_to_watch: str
    idle_timeout: int      # in seconds
    periodic_checks: int   # in seconds

    observer_running = False
    observer_lock = threading.Lock()

    def __init__(self, periodic_checks, idle_timeout):
        self.observer = Observer()
        self.directory_to_watch = getInputPath()
        self.periodic_checks = periodic_checks
        self.idle_timeout = idle_timeout

        self.file_queue = queue.Queue()
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def _process_queue(self):
        """Worker-Thread: verarbeitet Dateien sequenziell aus der Queue."""
        while True:
            filepath = self.file_queue.get()
            try:
                configuerData(filepath)
            except Exception as e:
                print(f"Fehler bei {filepath}: {e}")
            finally:
                self.file_queue.task_done()

    def check_empty(self):
        files = os.listdir(self.directory_to_watch)
        return len(files) == 1  # .stfolder wird mitgezählt

    def pushFileToQueue(self):
        """Bestehende Dateien in die Queue einreihen."""
        files = os.listdir(self.directory_to_watch)
        for file in files:
            if file == ".stfolder":
                continue
            self.file_queue.put(os.path.join(self.directory_to_watch, file))

    def start_observer(self):
        with self.observer_lock:
            if self.observer_running:
                return
            self.observer_running = True

        observer = Observer()

        def stop_observer():
            observer.stop()
            observer.join()
            with self.observer_lock:
                self.observer_running = False
            print("Observer gestoppt")

        event_handler = Handler(
            idle_timeout=self.idle_timeout,
            stop_callback=stop_observer,
            file_queue=self.file_queue
        )
        observer.schedule(event_handler, self.directory_to_watch, recursive=False)
        observer.start()

        print(f"Observer gestartet für {self.directory_to_watch} (idle timeout: {self.idle_timeout}s)...")
        threading.Thread(target=event_handler.monitor_idle, daemon=True).start()

    def run(self):
        print(f"Starte Watcher für {self.directory_to_watch}")
        try:
            while True:
                if not self.check_empty():
                    print("Dateien gefunden, werden in Queue eingereiht...")
                    self.pushFileToQueue()
                    self.start_observer()
                else:
                    print(f"Keine Änderung gefunden, nächster Check in {self.periodic_checks}s")
                time.sleep(self.periodic_checks)
        except KeyboardInterrupt:
            print("Watcher beendet")


if __name__ == '__main__':
    watcher = Watcher(periodic_checks=10, idle_timeout=21)
    watcher.run()
