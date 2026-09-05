import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "warehouse" / "student_analytics.db"


def test_warehouse_structure():
    connection = sqlite3.connect(DATABASE_PATH)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'"
        ).fetchall()
    }

    expected_tables = {
        "dim_school",
        "dim_student",
        "fact_student_performance",
    }

    assert tables == expected_tables

    connection.close()


def test_warehouse_row_counts():
    connection = sqlite3.connect(DATABASE_PATH)

    school_count = connection.execute(
        "SELECT COUNT(*) FROM dim_school"
    ).fetchone()[0]

    student_count = connection.execute(
        "SELECT COUNT(*) FROM dim_student"
    ).fetchone()[0]

    performance_count = connection.execute(
        "SELECT COUNT(*) FROM fact_student_performance"
    ).fetchone()[0]

    assert school_count == 2
    assert student_count == 395
    assert performance_count == 395

    connection.close()


def test_foreign_key_integrity():
    connection = sqlite3.connect(DATABASE_PATH)

    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert violations == []

    connection.close()


def test_student_keys_are_unique():
    connection = sqlite3.connect(DATABASE_PATH)

    duplicate_keys = connection.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT student_key) "
        "FROM dim_student"
    ).fetchone()[0]

    duplicate_source_ids = connection.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT student_source_id) "
        "FROM dim_student"
    ).fetchone()[0]

    assert duplicate_keys == 0
    assert duplicate_source_ids == 0

    connection.close()


def test_fact_data_ranges():
    connection = sqlite3.connect(DATABASE_PATH)

    invalid_g3 = connection.execute(
        "SELECT COUNT(*) "
        "FROM fact_student_performance "
        "WHERE G3 < 0 OR G3 > 20"
    ).fetchone()[0]

    invalid_absences = connection.execute(
        "SELECT COUNT(*) "
        "FROM fact_student_performance "
        "WHERE absences < 0"
    ).fetchone()[0]

    invalid_risk = connection.execute(
        "SELECT COUNT(*) "
        "FROM fact_student_performance "
        "WHERE observed_at_risk NOT IN (0, 1)"
    ).fetchone()[0]

    assert invalid_g3 == 0
    assert invalid_absences == 0
    assert invalid_risk == 0

    connection.close()