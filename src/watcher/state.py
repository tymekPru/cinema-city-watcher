import json
import os


class FileState:
    """Stan w lokalnym pliku JSON (tryb deweloperski)."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, data: dict) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)


class DynamoDbState:
    """Cały stan jako jeden rekord — to góra kilkadziesiąt seansów, po co więcej."""

    def __init__(self, table: str, region: str) -> None:
        import boto3  # dostępne w runtime Lambdy; lokalnie niewymagane

        self.table = boto3.resource("dynamodb", region_name=region).Table(table)

    def load(self) -> dict:
        item = self.table.get_item(Key={"pk": "state"}).get("Item")
        return json.loads(item["data"]) if item else {}

    def save(self, data: dict) -> None:
        self.table.put_item(Item={"pk": "state", "data": json.dumps(data, ensure_ascii=False)})


def make_state(cfg):
    if cfg.state_backend == "dynamodb":
        return DynamoDbState(cfg.ddb_table, cfg.aws_region)
    return FileState(cfg.state_file)
