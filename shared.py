class SharedState:
    def __init__(self):
        self.last_signal = None

    def update_last_signal(self, signal):
        self.last_signal = signal

    def get_last_signal(self):
        return self.last_signal
