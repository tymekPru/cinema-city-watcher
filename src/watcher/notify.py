class ConsoleNotifier:
    def send(self, subject: str, body: str) -> None:
        print(f"\n=== {subject} ===\n{body}\n")


class SesNotifier:
    def __init__(self, cfg) -> None:
        import boto3  # dostępne w runtime Lambdy

        self.client = boto3.client("ses", region_name=cfg.aws_region)
        self.source = cfg.ses_from
        self.to = cfg.ses_to

    def send(self, subject: str, body: str) -> None:
        self.client.send_email(
            Source=self.source,
            Destination={"ToAddresses": self.to},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )


def make_notifier(cfg):
    if cfg.notify_backend == "ses":
        if not (cfg.ses_from and cfg.ses_to):
            raise ValueError("NOTIFY_BACKEND=ses wymaga ustawienia SES_FROM i SES_TO")
        return SesNotifier(cfg)
    return ConsoleNotifier()
