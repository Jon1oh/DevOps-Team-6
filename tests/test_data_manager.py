"""Tests for managers/data_manager.py. Run from the project folder with:

    python -m pytest tests/test_data_manager.py

Every test gives DataManager a JsonRecordStorage that points at pytest's
tmp_path folder, so the real data/ folder is never touched.
"""

import managers.data_manager as data_manager_module
from classes.json_record_storage import JsonRecordStorage
from record import Record
from managers.data_manager import DataManager


def make_valid_dict(phone_number: str = "+6591234567", risk_level: str = "HIGH") -> dict:
    return {
        "record_id": 1,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": phone_number,
        "country_code": "+65",
        "message_content": "Your account is suspended. Click http://bad.link",
        "scam_probability": 90,
        "risk_level": risk_level,
        "scam_type": "Bank Impersonation Scam",
        "indicators": ["Urgent language", "Suspicious link"],
        "explanation": "Impersonates a bank.",
        "recommendation": "Do not click the link.",
    }


def make_manager(tmp_path) -> DataManager:
    storage = JsonRecordStorage(
        data_file=str(tmp_path / "scam_data.json"),
        backup_file=str(tmp_path / "backup_database.json"),
    )
    return DataManager(storage)


# ---------- saving ----------

def test_save_then_load(tmp_path) -> None:
    manager = make_manager(tmp_path)

    assert manager.save_record(make_valid_dict()) == (True, "")

    records = manager.load_records()
    assert len(records) == 1
    assert isinstance(records[0], Record)


def test_ids_are_assigned_in_order(tmp_path) -> None:
    manager = make_manager(tmp_path)
    manager.save_record(make_valid_dict())
    manager.save_record(make_valid_dict())     # same incoming id (1) on purpose

    ids = [record.record_id for record in manager.load_records()]
    assert ids == [1, 2]


def test_incoming_id_is_never_trusted(tmp_path) -> None:
    manager = make_manager(tmp_path)
    data = make_valid_dict()
    data["record_id"] = "not a number"         # would fail validation if used

    assert manager.save_record(data) == (True, "")
    assert manager.load_records()[0].record_id == 1


def test_incoming_old_message_id_is_ignored(tmp_path) -> None:
    manager = make_manager(tmp_path)
    data = make_valid_dict()
    del data["record_id"]
    data["message_id"] = 50                    # old name from the AI output

    manager.save_record(data)

    assert manager.load_records()[0].record_id == 1


def test_missing_id_and_country_are_filled_in(tmp_path) -> None:
    manager = make_manager(tmp_path)
    data = make_valid_dict()
    del data["record_id"]
    del data["country_code"]

    assert manager.save_record(data) == (True, "")
    record = manager.load_records()[0]
    assert record.record_id == 1
    assert record.country_code == "+65"


def test_invalid_record_is_not_saved(tmp_path) -> None:
    manager = make_manager(tmp_path)
    data = make_valid_dict()
    data["message_content"] = ""

    ok, error = manager.save_record(data)

    assert ok is False
    assert error == "message_content cannot be empty."
    assert manager.load_records() == []


def test_non_dict_is_rejected(tmp_path) -> None:
    manager = make_manager(tmp_path)
    assert manager.save_record("garbage") == (False, "Record is not a dictionary.")


def test_caller_dict_is_not_changed(tmp_path) -> None:
    manager = make_manager(tmp_path)
    data = make_valid_dict()
    data["record_id"] = 99
    manager.save_record(data)
    assert data["record_id"] == 99


# ---------- retrieving and counting ----------

def test_get_record_by_id(tmp_path) -> None:
    manager = make_manager(tmp_path)
    manager.save_record(make_valid_dict())
    manager.save_record(make_valid_dict(phone_number="+6588887777"))

    assert manager.get_record(2).phone_number == "+6588887777"
    assert manager.get_record(99) is None


def test_count_risk_levels_for_one_number(tmp_path) -> None:
    manager = make_manager(tmp_path)
    manager.save_record(make_valid_dict("+6591234567", "HIGH"))
    manager.save_record(make_valid_dict("+6591234567", "LOW"))
    manager.save_record(make_valid_dict("+6500000000", "HIGH"))

    assert manager.count_risk_levels("+6591234567") == {"HIGH": 1, "MEDIUM": 0, "LOW": 1}
    assert manager.count_risk_levels("+6599999999") == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


# ---------- summary and status ----------

def test_summary_of_saved_records(tmp_path) -> None:
    manager = make_manager(tmp_path)
    manager.save_record(make_valid_dict())
    manager.save_record(make_valid_dict())

    summary = manager.summary()

    assert summary["total_messages"] == 2
    assert summary["most_common_scam"] == "Bank Impersonation Scam"


def test_status_message_comes_from_storage(tmp_path) -> None:
    (tmp_path / "scam_data.json").write_text("{ broken", encoding="utf-8")
    manager = make_manager(tmp_path)

    manager.load_records()

    assert "corrupt" in manager.status_message


# ---------- temporary app.py wrappers ----------

def use_test_manager(monkeypatch, tmp_path) -> None:
    """Point the module-level wrappers at tmp_path instead of the real data/."""
    monkeypatch.setattr(data_manager_module, "_default_manager", make_manager(tmp_path))


def test_wrappers_work_like_phase_1(monkeypatch, tmp_path) -> None:
    use_test_manager(monkeypatch, tmp_path)

    assert data_manager_module.save_record(make_valid_dict()) == (True, "")

    records = data_manager_module.load_records()
    assert isinstance(records[0], dict)                 # Phase 1 returned dicts
    assert records[0]["record_id"] == 1
    assert records[0]["message_id"] == 1                # TEMPORARY old name for app.py

    summary = data_manager_module.summary_with_percentages(records)
    assert summary["total_messages"] == 1

    counts = data_manager_module.count_risk_levels("+6591234567")
    assert counts == {"HIGH": 1, "MEDIUM": 0, "LOW": 0}



# """Tests for managers/data_manager.py. Run from the project folder with:
 
#     python -m pytest tests/test_data_manager.py
 
# Every test gives DataManager a JsonRecordStorage that points at pytest's
# tmp_path folder, so the real data/ folder is never touched.
# """
 
# import managers.data_manager as data_manager_module
# from classes.json_record_storage import JsonRecordStorage
# # from classes.scam_record import ScamRecord
# from managers.data_manager import DataManager
# from record import Record
 
 
# def make_valid_dict(phone_number: str = "+6591234567", risk_level: str = "HIGH") -> dict:
#     return {
#         "record_id": 1,
#         "timestamp": "2026-10-02 11:40:00",
#         "phone_number": phone_number,
#         "country_code": "+65",
#         "message_content": "Your account is suspended. Click http://bad.link",
#         "scam_probability": 90,
#         "risk_level": risk_level,
#         "scam_type": "Bank Impersonation Scam",
#         "indicators": ["Urgent language", "Suspicious link"],
#         "explanation": "Impersonates a bank.",
#         "recommendation": "Do not click the link.",
#     }
 
 
# def make_manager(tmp_path) -> DataManager:
#     storage = JsonRecordStorage(
#         data_file=str(tmp_path / "scam_data.json"),
#         backup_file=str(tmp_path / "backup_database.json"),
#     )
#     return DataManager(storage)
 
 
# # ---------- saving ----------
 
# def test_save_then_load(tmp_path) -> None:
#     manager = make_manager(tmp_path)
 
#     assert manager.save_record(make_valid_dict()) == (True, "")
 
#     records = manager.load_records()
#     assert len(records) == 1
#     assert isinstance(records[0], Record)
 
 
# def test_ids_are_assigned_in_order(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     manager.save_record(make_valid_dict())
#     manager.save_record(make_valid_dict())     # same incoming id (1) on purpose
 
#     ids = [record.record_id for record in manager.load_records()]
#     assert ids == [1, 2]
 
 
# def test_incoming_id_is_never_trusted(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     data = make_valid_dict()
#     data["record_id"] = "not a number"        # would fail validation if used
 
#     assert manager.save_record(data) == (True, "")
#     assert manager.load_records()[0].record_id == 1
 
 
# def test_missing_id_and_country_are_filled_in(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     data = make_valid_dict()
#     del data["record_id"]
#     del data["country_code"]
 
#     assert manager.save_record(data) == (True, "")
#     record = manager.load_records()[0]
#     assert record.record_id == 1
#     assert record.country_code == "+65"
 
 
# def test_invalid_record_is_not_saved(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     data = make_valid_dict()
#     data["message_content"] = ""
 
#     ok, error = manager.save_record(data)
 
#     assert ok is False
#     assert error == "message_content cannot be empty."
#     assert manager.load_records() == []
 
 
# def test_non_dict_is_rejected(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     assert manager.save_record("garbage") == (False, "Record is not a dictionary.")
 
 
# def test_caller_dict_is_not_changed(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     data = make_valid_dict()
#     data["record_id"] = 99
#     manager.save_record(data)
#     assert data["record_id"] == 99
 
 
# # ---------- retrieving and counting ----------
 
# def test_get_record_by_id(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     manager.save_record(make_valid_dict())
#     manager.save_record(make_valid_dict(phone_number="+6588887777"))
 
#     assert manager.get_record(2).phone_number == "+6588887777"
#     assert manager.get_record(99) is None
 
 
# def test_count_risk_levels_for_one_number(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     manager.save_record(make_valid_dict("+6591234567", "HIGH"))
#     manager.save_record(make_valid_dict("+6591234567", "LOW"))
#     manager.save_record(make_valid_dict("+6500000000", "HIGH"))
 
#     assert manager.count_risk_levels("+6591234567") == {"HIGH": 1, "MEDIUM": 0, "LOW": 1}
#     assert manager.count_risk_levels("+6599999999") == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
 
 
# # ---------- summary and status ----------
 
# def test_summary_of_saved_records(tmp_path) -> None:
#     manager = make_manager(tmp_path)
#     manager.save_record(make_valid_dict())
#     manager.save_record(make_valid_dict())
 
#     summary = manager.summary()
 
#     assert summary["total_messages"] == 2
#     assert summary["most_common_scam"] == "Bank Impersonation Scam"
 
 
# def test_status_message_comes_from_storage(tmp_path) -> None:
#     (tmp_path / "scam_data.json").write_text("{ broken", encoding="utf-8")
#     manager = make_manager(tmp_path)
 
#     manager.load_records()
 
#     assert "corrupt" in manager.status_message
 
 
# # ---------- temporary app.py wrappers ----------
 
# def use_test_manager(monkeypatch, tmp_path) -> None:
#     """Point the module-level wrappers at tmp_path instead of the real data/."""
#     monkeypatch.setattr(data_manager_module, "_default_manager", make_manager(tmp_path))
 
 
# def test_wrappers_work_like_phase_1(monkeypatch, tmp_path) -> None:
#     use_test_manager(monkeypatch, tmp_path)
 
#     assert data_manager_module.save_record(make_valid_dict()) == (True, "")
 
#     records = data_manager_module.load_records()
#     assert isinstance(records[0], dict)                 # Phase 1 returned dicts
#     assert records[0]["record_id"] == 1
 
#     summary = data_manager_module.summary_with_percentages(records)
#     assert summary["total_messages"] == 1
 
#     counts = data_manager_module.count_risk_levels("+6591234567")
#     assert counts == {"HIGH": 1, "MEDIUM": 0, "LOW": 0}
 