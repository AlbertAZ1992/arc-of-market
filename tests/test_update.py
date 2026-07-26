from pathlib import Path

from scripts import update


def test_failed_harvest_restores_data_directory(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "data"
    data.mkdir()
    original = data / "existing.json"
    original.write_text('{"value":"before"}\n', encoding="utf-8")
    monkeypatch.setattr(update.harvest, "DATA", data)

    def failed_harvest(_args: list[str]) -> int:
        original.write_text('{"value":"partial"}\n', encoding="utf-8")
        (data / "new.json").write_text('{"value":"partial"}\n', encoding="utf-8")
        return 1

    monkeypatch.setattr(update.harvest, "main", failed_harvest)

    assert update.main(["--profile", "daily"]) == 1
    assert original.read_text(encoding="utf-8") == '{"value":"before"}\n'
    assert not (data / "new.json").exists()
