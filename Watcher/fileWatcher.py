import time, os, threading, queue
from watchdog.observers import Observer
from fileHandler import Handler
from API_Handler.getSongAPI import SongBPMHandler

class Watcher:
    observer_running = False

    def __init__(self, config, file_queue, queued_files):
        self.config = config
        self.observer_lock = threading.Lock()
        self.file_queue = file_queue
        #self.queued_files = set()
        #self.queued_lock = threading.Lock()
        #self.handler = Handler(
            #stop_callback=lambda: None,
            #file_queue=self.file_queue,
            #config=self.config
        #)

    def check_empty(self) : bool:
        for root, dirs, files in os.walk(self.config["input_path"]):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in files:
                if not filename.startswith(".") and not filename.endswith(".tmp"):
                    return False
        return True

    def pushFileToQueue(self):
        input_path = self.config["input_path"]
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
        input_path = self.config["input_path"]
        observer.schedule(event_handler, input_path, recursive=True)  
        observer.start()
        print(f"Observer gestartet für {input_path} (idle timeout: {self.config['idle_timeout']}s)...")
        threading.Thread(target=event_handler.monitor_idle, daemon=True).start()
