import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "warehouse" / "student_analytics.db"
SQL_PATH = PROJECT_ROOT / "sql" / "analytics.sql"


def execute_queries():
    connection = sqlite3.connect(DATABASE_PATH)

    with open(SQL_PATH, "r", encoding="utf-8") as file:
        sql_script = file.read()

    cursor = connection.cursor()

    results = []

    for statement in sql_script.split(";"):
        statement = statement.strip()

        if not statement:
            continue

        cursor.execute(statement)
        results.append(cursor.fetchall())

    connection.close()

    return results


def test_sql_query_count():
    results = execute_queries()

    assert len(results) == 16


def test_overall_academic_summary():
    results = execute_queries()

    assert results[0] == [
        (395, 10.91, 10.71, 10.42, 5.71)
    ]


def test_observed_at_risk_summary():
    results = execute_queries()

    assert results[1] == [
        (395, 130, 32.91)
    ]


def test_final_grade_distribution():
    results = execute_queries()

    distribution = dict(results[2])

    assert distribution[0] == 38
    assert distribution[10] == 56
    assert distribution[20] == 1
    assert sum(distribution.values()) == 395


def test_final_grade_bands():
    results = execute_queries()

    assert results[3] == [
        ("At Risk", 130, 5.38),
        ("Satisfactory", 165, 11.22),
        ("Good", 76, 14.86),
        ("Excellent", 24, 18.04),
    ]


def test_school_analysis():
    results = execute_queries()

    assert results[4] == [
        ("GP", "Gabriel Pereira", 349, 10.49, 5.97, 113, 32.38),
        ("MS", "Mousinho da Silveira", 46, 9.85, 3.76, 17, 36.96),
    ]


def test_gender_analysis():
    results = execute_queries()

    assert results[5] == [
        ("M", 187, 10.91, 5.14, 55, 29.41),
        ("F", 208, 9.97, 6.22, 75, 36.06),
    ]


def test_study_time_analysis():
    results = execute_queries()

    assert results[6] == [
        (1, 105, 10.05, 37, 35.24),
        (2, 198, 10.17, 70, 35.35),
        (3, 65, 11.4, 16, 24.62),
        (4, 27, 11.26, 7, 25.93),
    ]


def test_previous_failures_analysis():
    results = execute_queries()

    assert results[7] == [
        (0, 312, 11.25, 78, 25.0),
        (1, 50, 8.12, 26, 52.0),
        (2, 17, 6.24, 14, 82.35),
        (3, 16, 5.69, 12, 75.0),
    ]


def test_absence_analysis():
    results = execute_queries()

    assert results[8] == [
        ("0-5", 249, 10.17, 1.58, 79, 31.73),
        ("6-10", 80, 11.4, 7.6, 21, 26.25),
        ("11-20", 51, 10.12, 14.65, 22, 43.14),
        ("21+", 15, 10.27, 33.73, 8, 53.33),
    ]


def test_combined_risk_segments():
    results = execute_queries()

    assert results[15] == [
        ("Low Historical Risk", 273, 11.35, 63, 23.08),
        ("Moderate Historical Risk", 39, 10.56, 15, 38.46),
        ("High Historical Risk", 56, 6.16, 37, 66.07),
        ("Very High Historical Risk", 27, 9.56, 15, 55.56),
    ]