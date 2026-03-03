import time, os, threading, queue
from watchdog.observers import Observer
from configManager import ConfigManager
from fileHandler import Handler

class Watcher:
    observer_running = False

    def __init__(self, config):
        self.observer = Observer()
        self.config = config
        self.observer_lock = threading.Lock()  
        self.file_queue = queue.Queue()
        self.queued_files = set()
        self.queued_lock = threading.Lock()
        self.handler = Handler(  
            stop_callback=lambda: None,
            file_queue=self.file_queue,
            config=self.config
        )
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def _process_queue(self):
        while True:
            full_path = self.file_queue.get()
            try:
                self.handler.configureData(full_path)
            except Exception as e:
                print(f"Fehler bei {full_path}: {e}")
            finally:
                with self.queued_lock:
                    self.queued_files.discard(full_path)
                self.file_queue.task_done()

    def check_empty(self):
        for root, dirs, files in os.walk(self.config.get_watcher()["input_path"]):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in files:
                if not filename.startswith(".") and not filename.endswith(".tmp"):
                    return False
        return True

    def pushFileToQueue(self):
        input_path = self.config.get_watcher()["input_path"]
        for root, dirs, files in os.walk(input_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in files:
                if filename.startswith(".") or filename.endswith(".tmp"):
                    continue
                full_path = os.path.join(root, filename) 
                with self.queued_lock:
                    if full_path in self.queued_files:
                        continue
                    self.queued_files.add(full_path)
                self.file_queue.put(full_path)

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
            stop_callback=stop_observer,
            file_queue=self.file_queue,
            config=self.config
        )
        input_path = self.config.get_watcher()["input_path"]
        observer.schedule(event_handler, input_path, recursive=True)  
        observer.start()
        print(f"Observer gestartet für {input_path} (idle timeout: {self.config.get_watcher()['idle_timeout']}s)...")
        threading.Thread(target=event_handler.monitor_idle, daemon=True).start()

    def run(self):
        input_path = self.config.get_watcher()["input_path"]
        print(f"Starte Watcher für {input_path}")
        try:
            while True:
                if not self.check_empty():
                    print("Dateien gefunden, werden in Queue eingereiht...")
                    self.pushFileToQueue()
                    self.start_observer()
                else:
                    print(f"Keine Änderung gefunden, nächster Check in {self.config.get_watcher()['periodic_checks']}s")
                time.sleep(self.config.get_watcher()["periodic_checks"])
        except KeyboardInterrupt:
            print("Watcher beendet")

if __name__ == '__main__':
    config = ConfigManager() 
    watcher = Watcher(config)
    watcher.run()
