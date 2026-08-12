class ProgressTracker:
    def __init__(self, filename="mangas.progress", enabled=False):
        self.filename = filename
        self.enabled = enabled
        self.completed = set()
        if self.enabled:
            self._load()

    def _load(self):
        print("Loading list of successfully updated mangas")
        try:
            with open(self.filename) as progress_file:
                self.completed = {line.rstrip() for line in progress_file}
        except FileNotFoundError:
            print("Failed to load list of mangas")

    def is_done(self, series_id):
        return str(series_id) in self.completed

    def mark_done(self, series_id):
        if not self.enabled:
            return
        key = str(series_id)
        if key in self.completed:
            return
        with open(self.filename, "a+") as progress_file:
            progress_file.write(key + "\n")
        self.completed.add(key)
