import time, queue
from configManager import ConfigManager
from fileWatcher import Watcher

def main():
	config = configManager()

	filequeue = queue.Queue()
	watcher = Watcher(config.get_watcher())

	worker = threading.Thread(target=_process_queue(), daemon=True)
	worker.start()

	print("Starte Watcher")
	try:
		while True:
			if not watcher.check_empty():
				print("Dateien gefunden, werden in Queue eingereiht...")
				watcher.pushFileToQueue()
				watcher.start_observer()
			else:
				print(f"Keine Änderung gefunden, nächster Check in {self.config.get_watcher()['periodic_checks']}s")
			time.sleep(config.get_watcher()["periodic_checks"])
	except KeyboardInterrupt:
		print("Watcher beendet")



        def configureData(self, filepath):
        time.sleep(1)
        if not os.path.exists(filepath):
            print(f"Datei nicht mehr vorhanden, überspringe: {filepath}")
            return
        basename = os.path.basename(filepath)
        if basename.endswith(".tmp") or basename.startswith(".syncthing"):
            return
        output = os.path.join(self.config.get_watcher()["output_path"], basename)
        self.mergeMove(filepath, output)

        print(f"Verarbeite: {filepath}")
        self.SongBPM.process(output)

    def _process_queue(self):
        while True:
            full_path = file_queue.get()
            try:
                configureData(full_path)
            except Exception as e:
                print(f"Fehler bei {full_path}: {e}")
            finally:
                with queued_lock:
                    queued_files.discard(full_path)
                file_queue.task_done()




if __name__ == "__main__":
    main()
