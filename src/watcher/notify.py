class ConsoleNotifier:
    def send(self, subject: str, body: str) -> None:
        print(f"\n=== {subject} ===\n{body}\n")


def make_notifier(cfg):
    return ConsoleNotifier()
