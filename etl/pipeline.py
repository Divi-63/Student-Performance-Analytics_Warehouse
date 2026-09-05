from pathlib import Path
import sqlite3

import pandas as pd


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "student-mat.csv"
WAREHOUSE_DIR = PROJECT_ROOT / "warehouse"
DATABASE_PATH = WAREHOUSE_DIR / "student_analytics.db"


# ============================================================
# Expected source schema
# ============================================================

EXPECTED_COLUMNS = [
    "school",
    "sex",
    "age",
    "address",
    "famsize",
    "Pstatus",
    "Medu",
    "Fedu",
    "Mjob",
    "Fjob",
    "reason",
    "guardian",
    "traveltime",
    "studytime",
    "failures",
    "schoolsup",
    "famsup",
    "paid",
    "activities",
    "nursery",
    "higher",
    "internet",
    "romantic",
    "famrel",
    "freetime",
    "goout",
    "Dalc",
    "Walc",
    "health",
    "absences",
    "G1",
    "G2",
    "G3",
]


# ============================================================
# Extract
# ============================================================

def extract_data():
    """Read the source UCI dataset."""

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {RAW_DATA_PATH}"
        )

    df = pd.read_csv(RAW_DATA_PATH, sep=";")

    print(f"Extracted {len(df)} rows from {RAW_DATA_PATH}")

    return df


# ============================================================
# Validate
# ============================================================

def validate_data(df):
    """Validate the source dataset before transformation."""

    # Check the exact source schema.
    if df.columns.tolist() != EXPECTED_COLUMNS:
        missing_columns = [
            column
            for column in EXPECTED_COLUMNS
            if column not in df.columns
        ]

        unexpected_columns = [
            column
            for column in df.columns
            if column not in EXPECTED_COLUMNS
        ]

        raise ValueError(
            "Unexpected source schema.\n"
            f"Missing columns: {missing_columns}\n"
            f"Unexpected columns: {unexpected_columns}"
        )

    # Dataset must not be empty.
    if df.empty:
        raise ValueError("Source dataset is empty.")

    # Duplicate source records are not expected.
    if df.duplicated().any():
        duplicate_count = int(df.duplicated().sum())

        raise ValueError(
            f"Source dataset contains {duplicate_count} duplicate rows."
        )

    # Required numeric columns.
    numeric_columns = [
        "age",
        "Medu",
        "Fedu",
        "traveltime",
        "studytime",
        "failures",
        "famrel",
        "freetime",
        "goout",
        "Dalc",
        "Walc",
        "health",
        "absences",
        "G1",
        "G2",
        "G3",
    ]

    for column in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(
                f"Column '{column}' must contain numeric values."
            )

    # Grades must be within the UCI grading range.
    for column in ["G1", "G2", "G3"]:
        if not df[column].between(0, 20).all():
            raise ValueError(
                f"Column '{column}' contains values outside 0-20."
            )

    # Absences cannot be negative.
    if (df["absences"] < 0).any():
        raise ValueError(
            "Column 'absences' contains negative values."
        )

    # Validate important categorical fields.
    categorical_values = {
        "school": {"GP", "MS"},
        "sex": {"F", "M"},
        "address": {"U", "R"},
        "famsize": {"LE3", "GT3"},
        "Pstatus": {"T", "A"},
        "schoolsup": {"yes", "no"},
        "famsup": {"yes", "no"},
        "paid": {"yes", "no"},
        "activities": {"yes", "no"},
        "nursery": {"yes", "no"},
        "higher": {"yes", "no"},
        "internet": {"yes", "no"},
        "romantic": {"yes", "no"},
    }

    for column, allowed_values in categorical_values.items():
        actual_values = set(df[column].dropna().unique())

        invalid_values = actual_values - allowed_values

        if invalid_values:
            raise ValueError(
                f"Column '{column}' contains invalid values: "
                f"{sorted(invalid_values)}"
            )

    print("Validation successful.")


# ============================================================
# Transform
# ============================================================

def transform_data(df):
    """
    Transform the source dataset into warehouse tables.

    Warehouse structure:

        dim_school
        dim_student
        fact_student_performance
    """

    data = df.copy()

    # --------------------------------------------------------
    # Dimension: School
    # --------------------------------------------------------

    dim_school = pd.DataFrame(
        {
            "school_code": ["GP", "MS"],
            "school_name": [
                "Gabriel Pereira",
                "Mousinho da Silveira",
            ],
        }
    )

    dim_school.insert(
        0,
        "school_key",
        range(1, len(dim_school) + 1),
    )

    school_map = dict(
        zip(
            dim_school["school_code"],
            dim_school["school_key"],
        )
    )

    # --------------------------------------------------------
    # Dimension: Student
    # --------------------------------------------------------

    student_columns = [
    "school",
    "sex",
    "age",
    "address",
    "famsize",
    "Pstatus",
    "Medu",
    "Fedu",
    "Mjob",
    "Fjob",
    "reason",
    "guardian",
    "traveltime",
    "studytime",
    "failures",
    "schoolsup",
    "famsup",
    "paid",
    "activities",
    "nursery",
    "higher",
    "internet",
    "romantic",
    "famrel",
    "freetime",
    "goout",
    "Dalc",
    "Walc",
    "health",
]

    dim_student = data[student_columns].copy()

    # The original UCI dataset does not contain a student ID.
    # Generate warehouse keys during ETL.
    dim_student.insert(
        0,
        "student_source_id",
        range(1, len(dim_student) + 1),
    )

    dim_student.insert(
        0,
        "student_key",
        range(1, len(dim_student) + 1),
    )

    # Replace source school code with warehouse foreign key.
    dim_student["school_key"] = dim_student["school"].map(
        school_map
    )

    if dim_student["school_key"].isna().any():
        raise ValueError(
            "Failed to map one or more students to a school."
        )

    # The source school code has been represented by school_key.
    dim_student.drop(columns=["school"], inplace=True)

    # Keep school_key at the end of the dimension.
    student_column_order = [
        "student_key",
        "student_source_id",
        "sex",
        "age",
        "address",
        "famsize",
        "Pstatus",
        "Medu",
        "Fedu",
        "Mjob",
        "Fjob",
        "reason",
        "guardian",
        "traveltime",
        "studytime",
        "failures",
        "schoolsup",
        "famsup",
        "paid",
        "activities",
        "nursery",
        "higher",
        "internet",
        "romantic",
        "famrel",
        "freetime",
        "goout",
        "Dalc",
        "Walc",
        "health",
        "school_key",
    ]

    dim_student = dim_student[student_column_order]

    # --------------------------------------------------------
    # Fact: Student Performance
    # --------------------------------------------------------

    fact_student_performance = pd.DataFrame(
        {
            "performance_key": range(1, len(data) + 1),
            "student_key": range(1, len(data) + 1),
            "G1": data["G1"].astype(int),
            "G2": data["G2"].astype(int),
            "G3": data["G3"].astype(int),
            "absences": data["absences"].astype(int),
            "observed_at_risk": (
                data["G3"] < 10
            ).astype(int),
        }
    )

    return {
        "dim_school": dim_school,
        "dim_student": dim_student,
        "fact_student_performance": fact_student_performance,
    }


# ============================================================
# Data Quality Checks
# ============================================================

def run_quality_checks(tables):
    """Run checks on transformed warehouse tables."""

    expected_tables = {
        "dim_school",
        "dim_student",
        "fact_student_performance",
    }

    if set(tables.keys()) != expected_tables:
        raise ValueError(
            "Unexpected warehouse table set."
        )

    # Expected student and performance counts.
    if len(tables["dim_student"]) != 395:
        raise ValueError(
            "dim_student should contain 395 rows."
        )

    if len(tables["fact_student_performance"]) != 395:
        raise ValueError(
            "fact_student_performance should contain 395 rows."
        )

    # School dimension should contain the two source schools.
    if len(tables["dim_school"]) != 2:
        raise ValueError(
            "dim_school should contain 2 rows."
        )

    # Student keys should be unique.
    if tables["dim_student"]["student_key"].duplicated().any():
        raise ValueError(
            "student_key contains duplicates."
        )

    # Fact keys should be unique.
    if tables[
        "fact_student_performance"
    ]["performance_key"].duplicated().any():
        raise ValueError(
            "performance_key contains duplicates."
        )

    # Every fact should reference a student.
    student_keys = set(
        tables["dim_student"]["student_key"]
    )

    fact_student_keys = set(
        tables[
            "fact_student_performance"
        ]["student_key"]
    )

    if not fact_student_keys.issubset(student_keys):
        raise ValueError(
            "Fact table contains invalid student_key values."
        )

    # observed_at_risk must be binary.
    if not tables[
        "fact_student_performance"
    ]["observed_at_risk"].isin([0, 1]).all():
        raise ValueError(
            "observed_at_risk must contain only 0 or 1."
        )

    print("Data-quality checks successful.")


# ============================================================
# Load
# ============================================================

def load_to_sqlite(tables):
    """Load warehouse tables into SQLite."""

    WAREHOUSE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Rebuild the warehouse so the ETL is repeatable.
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    with sqlite3.connect(DATABASE_PATH) as connection:

        # Enable foreign-key enforcement for this connection.
        connection.execute("PRAGMA foreign_keys = ON")

        # Create school dimension.
        connection.execute(
            """
            CREATE TABLE dim_school (
                school_key INTEGER PRIMARY KEY,
                school_code TEXT NOT NULL UNIQUE,
                school_name TEXT NOT NULL
            )
            """
        )

        # Create student dimension.
        connection.execute(
            """
            CREATE TABLE dim_student (
                student_key INTEGER PRIMARY KEY,
                student_source_id INTEGER NOT NULL UNIQUE,
                sex TEXT NOT NULL,
                age INTEGER NOT NULL,
                address TEXT NOT NULL,
                famsize TEXT NOT NULL,
                Pstatus TEXT NOT NULL,
                Medu INTEGER NOT NULL,
                Fedu INTEGER NOT NULL,
                Mjob TEXT NOT NULL,
                Fjob TEXT NOT NULL,
                reason TEXT NOT NULL,
                guardian TEXT NOT NULL,
                traveltime INTEGER NOT NULL,
                studytime INTEGER NOT NULL,
                failures INTEGER NOT NULL,
                schoolsup TEXT NOT NULL,
                famsup TEXT NOT NULL,
                paid TEXT NOT NULL,
                activities TEXT NOT NULL,
                nursery TEXT NOT NULL,
                higher TEXT NOT NULL,
                internet TEXT NOT NULL,
                romantic TEXT NOT NULL,
                famrel INTEGER NOT NULL,
                freetime INTEGER NOT NULL,
                goout INTEGER NOT NULL,
                Dalc INTEGER NOT NULL,
                Walc INTEGER NOT NULL,
                health INTEGER NOT NULL,
                school_key INTEGER NOT NULL,
                FOREIGN KEY (school_key)
                    REFERENCES dim_school(school_key)
            )
            """
        )

        # Create performance fact table.
        connection.execute(
            """
            CREATE TABLE fact_student_performance (
                performance_key INTEGER PRIMARY KEY,
                student_key INTEGER NOT NULL,
                G1 INTEGER NOT NULL,
                G2 INTEGER NOT NULL,
                G3 INTEGER NOT NULL,
                absences INTEGER NOT NULL,
                observed_at_risk INTEGER NOT NULL,
                FOREIGN KEY (student_key)
                    REFERENCES dim_student(student_key)
            )
            """
        )

        # Load dimensions first because facts reference them.
        tables["dim_school"].to_sql(
            "dim_school",
            connection,
            if_exists="append",
            index=False,
        )

        tables["dim_student"].to_sql(
            "dim_student",
            connection,
            if_exists="append",
            index=False,
        )

        tables["fact_student_performance"].to_sql(
            "fact_student_performance",
            connection,
            if_exists="append",
            index=False,
        )

        # Verify foreign-key integrity.
        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise ValueError(
                f"Foreign-key violations found: "
                f"{foreign_key_errors}"
            )

    print(f"Warehouse created: {DATABASE_PATH}")


# ============================================================
# Main ETL Pipeline
# ============================================================

def main():
    print("Starting Student Performance ETL...")
    print("-" * 50)

    # Extract
    df = extract_data()

    # Validate
    validate_data(df)

    # Transform
    tables = transform_data(df)

    # Quality checks
    run_quality_checks(tables)

    # Load
    load_to_sqlite(tables)

    print("-" * 50)
    print("ETL completed successfully.")


if __name__ == "__main__":
    main()