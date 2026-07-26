import json
from pathlib import Path

from scripts.chain import append_day, load_records, verify


def test_chain_verifies_current_canonical_json(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    source = data / "sample.json"
    source.write_text('{"b":2,"a":1}\n', encoding="utf-8")
    chain_path = data / "hash_chain.jsonl"

    append_day(chain_path, data)
    assert verify(chain_path, data)

    source.write_text('{\n  "a": 1,\n  "b": 2\n}\n', encoding="utf-8")
    assert verify(chain_path, data)

    source.write_text('{"a":1,"b":3}\n', encoding="utf-8")
    assert not verify(chain_path, data)


def test_chain_detects_record_tampering(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.json").write_text('{"value":1}\n', encoding="utf-8")
    chain_path = data / "hash_chain.jsonl"
    append_day(chain_path, data)

    record = load_records(chain_path)[0]
    record["timestamp"] = "2000-01-01T00:00:00Z"
    chain_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    assert not verify(chain_path, data)
