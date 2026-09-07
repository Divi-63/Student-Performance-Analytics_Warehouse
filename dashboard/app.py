from pathlib import Path
import json
import sqlite3

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st


# Paths

ROOT_DIR = Path(__file__).resolve().parents[1]

WAREHOUSE_PATH = ROOT_DIR / "warehouse" / "student_analytics.db"

RISK_MODEL_PATH = ROOT_DIR / "models" / "student_risk_model.joblib"
GRADE_MODEL_PATH = ROOT_DIR / "models" / "student_grade_model.joblib"
RISK_CONFIG_PATH = ROOT_DIR / "models" / "risk_threshold.json"


LOW_RISK_THRESHOLD = 0.30
HIGH_RISK_THRESHOLD = 0.70


STUDYTIME_LABELS = {
    1: "<2 hours",
    2: "2-5 hours",
    3: "5-10 hours",
    4: ">10 hours",
}


EDUCATION_LABELS = {
    0: "None",
    1: "Primary",
    2: "5th-9th grade",
    3: "Secondary",
    4: "Higher education",
}


TRAVELTIME_LABELS = {
    1: "<15 min",
    2: "15-30 min",
    3: "30-60 min",
    4: ">60 min",
}


# Streamlit configuration

st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🎓",
    layout="wide",
)



# Data and model loading




@st.cache_resource
def load_models():
    return (
        joblib.load(RISK_MODEL_PATH),
        joblib.load(GRADE_MODEL_PATH),
    )


@st.cache_data
def load_risk_config():
    with open(RISK_CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_resource
def get_warehouse_connection():
    connection = sqlite3.connect(
        WAREHOUSE_PATH,
        check_same_thread=False,
    )
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


# Validate required files

for path, name in [
    
    (WAREHOUSE_PATH, "Data warehouse"),
    (RISK_MODEL_PATH, "Risk model"),
    (GRADE_MODEL_PATH, "Grade model"),
    (RISK_CONFIG_PATH, "Risk configuration"),
]:
    if not path.exists():
        st.error(f"{name} not found: {path}")
        st.stop()


# Load resources



risk_model, grade_model = load_models()
risk_config = load_risk_config()

warehouse_connection = get_warehouse_connection()

RISK_THRESHOLD = risk_config["classification_threshold"]





# Warehouse analytics

def get_overview_metrics(school, gender, age):
    """
    Retrieve filtered historical overview metrics from the
    SQLite data warehouse.
    """

    query = """
        SELECT
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_grade,
            COALESCE(SUM(f.observed_at_risk), 0) AS at_risk_students,
            CASE
                WHEN COUNT(*) > 0
                THEN ROUND(
                    100.0 * SUM(f.observed_at_risk) / COUNT(*),
                    2
                )
                ELSE NULL
            END AS at_risk_percentage,
            ROUND(AVG(f.absences), 2) AS average_absences
        FROM fact_student_performance f
        JOIN dim_student s
            ON f.student_key = s.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?);
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    result = pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )

    return result.iloc[0]

def get_grade_distribution(school, gender, age):
    """
    Retrieve filtered final-grade distribution
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            f.G3 AS final_grade,
            COUNT(*) AS student_count
        FROM fact_student_performance f
        JOIN dim_student s
            ON f.student_key = s.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY f.G3
        ORDER BY f.G3;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )


def get_studytime_performance(school, gender, age):
    """
    Retrieve filtered study-time performance
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            s.studytime,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3
        FROM dim_student s
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY s.studytime
        ORDER BY s.studytime;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )

def get_failure_performance(school, gender, age):
    """
    Retrieve filtered previous-failure performance
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            s.failures,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3,
            SUM(f.observed_at_risk) AS at_risk_students,
            ROUND(
                100.0 * SUM(f.observed_at_risk) / COUNT(*),
                2
            ) AS at_risk_percentage
        FROM dim_student s
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY s.failures
        ORDER BY s.failures;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )


def get_absence_performance(school, gender, age):
    """
    Retrieve filtered absence-band performance
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            CASE
                WHEN f.absences BETWEEN 0 AND 5 THEN '0-5'
                WHEN f.absences BETWEEN 6 AND 10 THEN '6-10'
                WHEN f.absences BETWEEN 11 AND 20 THEN '11-20'
                ELSE '21+'
            END AS absence_band,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3,
            ROUND(AVG(f.absences), 2) AS average_absences,
            SUM(f.observed_at_risk) AS at_risk_students,
            ROUND(
                100.0 * SUM(f.observed_at_risk) / COUNT(*),
                2
            ) AS at_risk_percentage
        FROM dim_student s
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY absence_band
        ORDER BY
            CASE absence_band
                WHEN '0-5' THEN 1
                WHEN '6-10' THEN 2
                WHEN '11-20' THEN 3
                WHEN '21+' THEN 4
            END;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )


def get_risk_segments(school, gender, age):
    """
    Retrieve filtered historical risk segments
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            CASE
                WHEN s.failures = 0 AND f.absences <= 10
                    THEN 'Low Historical Risk'
                WHEN s.failures = 0 AND f.absences > 10
                    THEN 'Moderate Historical Risk'
                WHEN s.failures > 0 AND f.absences <= 10
                    THEN 'High Historical Risk'
                ELSE 'Very High Historical Risk'
            END AS risk_segment,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3,
            SUM(f.observed_at_risk) AS at_risk_students,
            ROUND(
                100.0 * SUM(f.observed_at_risk) / COUNT(*),
                2
            ) AS at_risk_percentage
        FROM dim_student s
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY risk_segment
        ORDER BY
            CASE risk_segment
                WHEN 'Low Historical Risk' THEN 1
                WHEN 'Moderate Historical Risk' THEN 2
                WHEN 'High Historical Risk' THEN 3
                WHEN 'Very High Historical Risk' THEN 4
            END;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )


def get_filter_options():
    """
    Retrieve filter options directly from the SQLite warehouse.
    """

    school_query = """
        SELECT school_code
        FROM dim_school
        ORDER BY school_code;
    """

    gender_query = """
        SELECT DISTINCT sex
        FROM dim_student
        ORDER BY sex;
    """

    age_query = """
        SELECT DISTINCT age
        FROM dim_student
        ORDER BY age;
    """

    schools = pd.read_sql_query(
        school_query,
        warehouse_connection,
    )["school_code"].tolist()

    genders = pd.read_sql_query(
        gender_query,
        warehouse_connection,
    )["sex"].tolist()

    ages = pd.read_sql_query(
        age_query,
        warehouse_connection,
    )["age"].tolist()

    return schools, genders, ages


def get_student_preview(school, gender, age):
    """
    Retrieve a filtered student preview from the
    SQLite data warehouse.
    """

    query = """
        SELECT
            d.school_code AS school,
            s.sex,
            s.age,
            s.address,
            s.studytime,
            s.failures,
            f.absences,
            f.G1,
            f.G2,
            f.G3,
            f.observed_at_risk
        FROM dim_student s
        JOIN dim_school d
            ON s.school_key = d.school_key
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        ORDER BY s.student_key
        LIMIT 10;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )

def get_school_performance(school, gender, age):
    """
    Retrieve filtered academic performance by school
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            d.school_code AS school,
            d.school_name,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3,
            ROUND(AVG(f.absences), 2) AS average_absences,
            SUM(f.observed_at_risk) AS at_risk_students,
            ROUND(
                100.0 * SUM(f.observed_at_risk) / COUNT(*),
                2
            ) AS at_risk_percentage
        FROM dim_school d
        JOIN dim_student s
            ON d.school_key = s.school_key
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY
            d.school_code,
            d.school_name
        ORDER BY d.school_code;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )


def get_gender_performance(school, gender, age):
    """
    Retrieve filtered academic performance by gender
    from the SQLite data warehouse.
    """

    query = """
        SELECT
            s.sex AS gender,
            COUNT(*) AS student_count,
            ROUND(AVG(f.G3), 2) AS average_g3,
            ROUND(AVG(f.absences), 2) AS average_absences,
            SUM(f.observed_at_risk) AS at_risk_students,
            ROUND(
                100.0 * SUM(f.observed_at_risk) / COUNT(*),
                2
            ) AS at_risk_percentage
        FROM dim_student s
        JOIN fact_student_performance f
            ON s.student_key = f.student_key
        JOIN dim_school d
            ON s.school_key = d.school_key
        WHERE
            (? IS NULL OR d.school_code = ?)
            AND (? IS NULL OR s.sex = ?)
            AND (? IS NULL OR s.age = ?)
        GROUP BY s.sex
        ORDER BY s.sex;
    """

    school_filter = None if school == "All" else school
    gender_filter = None if gender == "All" else gender
    age_filter = None if age == "All" else age

    return pd.read_sql_query(
        query,
        warehouse_connection,
        params=[
            school_filter,
            school_filter,
            gender_filter,
            gender_filter,
            age_filter,
            age_filter,
        ],
    )

# Dashboard

st.title(" Student Performance Analytics")

st.write(
    "Explore historical student performance and predict final grade "
    "and academic risk."
)


# Student Filters

st.subheader("Student Filters")

schools, genders, ages = get_filter_options()

col1, col2, col3 = st.columns(3)

with col1:
    selected_school = st.selectbox(
        "School",
        ["All", *schools],
    )

with col2:
    selected_gender = st.selectbox(
        "Gender",
        ["All", *genders],
    )

with col3:
    selected_age = st.selectbox(
        "Age",
        ["All", *ages],
    )


# Retrieve the filtered student count from the warehouse.
overview = get_overview_metrics(
    selected_school,
    selected_gender,
    selected_age,
)

student_count = int(overview["student_count"])

st.write(f"Showing **{student_count} students**")

if student_count == 0:
    st.warning(
        "No students match the selected filters. "
        "Please choose a different filter combination."
    )

# Overview metrics

st.subheader("Overview")



student_count = int(overview["student_count"])

average_grade = overview["average_grade"]

at_risk_count = int(overview["at_risk_students"])

at_risk_percentage = overview["at_risk_percentage"]

average_absences = overview["average_absences"]


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Students",
    student_count,
)

col2.metric(
    "Average Final Grade",
    f"{average_grade:.2f}" if pd.notna(average_grade) else "N/A",
)

col3.metric(
    "Observed At-Risk %",
    (
        f"{at_risk_percentage:.1f}%"
        if pd.notna(at_risk_percentage)
        else "N/A"
    ),
)

col4.metric(
    "Average Absences",
    (
        f"{average_absences:.2f}"
        if pd.notna(average_absences)
        else "N/A"
    ),
)


# Academic analytics

st.subheader("Academic Analytics")

grade_distribution = get_grade_distribution(
    selected_school,
    selected_gender,
    selected_age,
)

studytime_performance = get_studytime_performance(
    selected_school,
    selected_gender,
    selected_age,
)

school_performance = get_school_performance(
    selected_school,
    selected_gender,
    selected_age,
)

gender_performance = get_gender_performance(
    selected_school,
    selected_gender,
    selected_age,
)


# Final grade distribution

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        grade_distribution,
        x="final_grade",
        y="student_count",
        title="Final Grade Distribution",
        labels={
            "final_grade": "Final Grade",
            "student_count": "Students",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# Study time

with col2:
    studytime_performance["studytime"] = (
        studytime_performance["studytime"]
        .map(STUDYTIME_LABELS)
    )

    fig = px.bar(
        studytime_performance,
        x="studytime",
        y="average_g3",
        title="Average Grade by Study Time",
        labels={
            "studytime": "Study Time",
            "average_g3": "Average Final Grade",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# School performance

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        school_performance,
        x="school",
        y="average_g3",
        title="Average Grade by School",
        labels={
            "school": "School",
            "average_g3": "Average Final Grade",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# Gender performance

with col2:
    fig = px.bar(
        gender_performance,
        x="gender",
        y="average_g3",
        title="Average Grade by Gender",
        labels={
            "gender": "Gender",
            "average_g3": "Average Final Grade",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

# Historical risk analytics

st.subheader("Historical Risk Analytics")

failure_performance = get_failure_performance(
    selected_school,
    selected_gender,
    selected_age,
)

absence_performance = get_absence_performance(
    selected_school,
    selected_gender,
    selected_age,
)

risk_segments = get_risk_segments(
    selected_school,
    selected_gender,
    selected_age,
)


# Previous failures

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        failure_performance,
        x="failures",
        y="average_g3",
        title="Average Grade by Previous Failures",
        labels={
            "failures": "Previous Failures",
            "average_g3": "Average Final Grade",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# Absence bands

with col2:
    fig = px.bar(
        absence_performance,
        x="absence_band",
        y="at_risk_percentage",
        title="Observed At-Risk % by Absence Band",
        labels={
            "absence_band": "Absence Band",
            "at_risk_percentage": "Observed At-Risk %",
        },
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# Historical risk segments

st.subheader("Historical Risk Segments")

fig = px.bar(
    risk_segments,
    x="risk_segment",
    y="at_risk_percentage",
    title="Observed At-Risk % by Historical Risk Segment",
    labels={
        "risk_segment": "Historical Risk Segment",
        "at_risk_percentage": "Observed At-Risk %",
    },
)

st.plotly_chart(
    fig,
    width="stretch",
)


# Student data preview

st.subheader("Student Data Preview")

student_preview = get_student_preview(
    selected_school,
    selected_gender,
    selected_age,
)

st.dataframe(
    student_preview,
    width="stretch",
)

# Student prediction

st.subheader("Student Performance Prediction")

st.write(
    "Enter student information to estimate the final grade "
    "and assess early academic risk."
)


with st.form("student_prediction_form"):

    st.markdown("### Personal Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        school = st.selectbox(
            "School",
            ["GP", "MS"],
        )

    with col2:
        sex = st.selectbox(
            "Gender",
            ["F", "M"],
        )

    with col3:
        age = st.number_input(
            "Age",
            min_value=15,
            max_value=22,
            value=17,
            step=1,
        )

    col1, col2 = st.columns(2)

    with col1:
        address = st.selectbox(
            "Address",
            ["U", "R"],
        )

    with col2:
        famsize = st.selectbox(
            "Family Size",
            ["GT3", "LE3"],
        )

    Pstatus = st.selectbox(
        "Parent Cohabitation Status",
        ["T", "A"],
    )

    st.markdown("### Family & Background")

    col1, col2 = st.columns(2)

    with col1:
        Medu = st.selectbox(
            "Mother's Education",
            list(EDUCATION_LABELS),
            format_func=EDUCATION_LABELS.get,
        )

    with col2:
        Fedu = st.selectbox(
            "Father's Education",
            list(EDUCATION_LABELS),
            format_func=EDUCATION_LABELS.get,
        )

    col1, col2 = st.columns(2)

    with col1:
        Mjob = st.selectbox(
            "Mother's Job",
            [
                "teacher",
                "health",
                "services",
                "at_home",
                "other",
            ],
        )

    with col2:
        Fjob = st.selectbox(
            "Father's Job",
            [
                "teacher",
                "health",
                "services",
                "at_home",
                "other",
            ],
        )

    reason = st.selectbox(
        "Reason for Choosing School",
        [
            "home",
            "reputation",
            "course",
            "other",
        ],
    )

    guardian = st.selectbox(
        "Guardian",
        [
            "mother",
            "father",
            "other",
        ],
    )

    st.markdown("### Academic Behaviour")

    col1, col2, col3 = st.columns(3)

    with col1:
        traveltime = st.selectbox(
            "Travel Time",
            list(TRAVELTIME_LABELS),
            format_func=TRAVELTIME_LABELS.get,
        )

    with col2:
        studytime = st.selectbox(
            "Study Time",
            list(STUDYTIME_LABELS),
            format_func=STUDYTIME_LABELS.get,
        )

    with col3:
        failures = st.selectbox(
            "Previous Failures",
            [0, 1, 2, 3],
        )

    col1, col2 = st.columns(2)

    with col1:
        schoolsup = st.selectbox(
            "School Support",
            ["yes", "no"],
        )

    with col2:
        famsup = st.selectbox(
            "Family Support",
            ["yes", "no"],
        )

    col1, col2 = st.columns(2)

    with col1:
        paid = st.selectbox(
            "Extra Paid Classes",
            ["yes", "no"],
        )

    with col2:
        activities = st.selectbox(
            "Extra-curricular Activities",
            ["yes", "no"],
        )

    st.markdown("### School & Lifestyle")

    col1, col2, col3 = st.columns(3)

    with col1:
        nursery = st.selectbox(
            "Attended Nursery",
            ["yes", "no"],
        )

    with col2:
        higher = st.selectbox(
            "Wants Higher Education",
            ["yes", "no"],
        )

    with col3:
        internet = st.selectbox(
            "Internet Access",
            ["yes", "no"],
        )

    romantic = st.selectbox(
        "Romantic Relationship",
        ["yes", "no"],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        famrel = st.slider(
            "Family Relationship Quality",
            1,
            5,
            4,
        )

    with col2:
        freetime = st.slider(
            "Free Time",
            1,
            5,
            3,
        )

    with col3:
        goout = st.slider(
            "Going Out",
            1,
            5,
            3,
        )

    col1, col2 = st.columns(2)

    with col1:
        Dalc = st.slider(
            "Workday Alcohol Consumption",
            1,
            5,
            1,
        )

    with col2:
        Walc = st.slider(
            "Weekend Alcohol Consumption",
            1,
            5,
            1,
        )

    health = st.slider(
        "Current Health",
        1,
        5,
        3,
    )

    st.markdown("### Attendance")

    absences = st.number_input(
        "Number of Absences",
        min_value=0,
        max_value=75,
        value=5,
        step=1,
    )

    st.markdown("### Academic Progress")

    st.caption(
        "G1 and G2 are first- and second-period grades used by "
        "the final-grade prediction model."
    )

    col1, col2 = st.columns(2)

    with col1:
        G1 = st.number_input(
            "First Period Grade (G1)",
            min_value=0,
            max_value=20,
            value=10,
            step=1,
        )

    with col2:
        G2 = st.number_input(
            "Second Period Grade (G2)",
            min_value=0,
            max_value=20,
            value=10,
            step=1,
        )

    submitted = st.form_submit_button(
        "Predict Final Grade & Risk"
    )


# Prediction processing

if submitted:

    student_data = pd.DataFrame([{
        "school": school,
        "sex": sex,
        "age": age,
        "address": address,
        "famsize": famsize,
        "Pstatus": Pstatus,
        "Medu": Medu,
        "Fedu": Fedu,
        "Mjob": Mjob,
        "Fjob": Fjob,
        "reason": reason,
        "guardian": guardian,
        "traveltime": traveltime,
        "studytime": studytime,
        "failures": failures,
        "schoolsup": schoolsup,
        "famsup": famsup,
        "paid": paid,
        "activities": activities,
        "nursery": nursery,
        "higher": higher,
        "internet": internet,
        "romantic": romantic,
        "famrel": famrel,
        "freetime": freetime,
        "goout": goout,
        "Dalc": Dalc,
        "Walc": Walc,
        "health": health,
        "absences": absences,
    }])

    # Early-risk model
    # Uses only early-stage student information.
    # G1, G2 and G3 are intentionally excluded.

    risk_probability = risk_model.predict_proba(
        student_data
    )[0, 1]

    risk_prediction = int(
        risk_probability >= RISK_THRESHOLD
    )

    if risk_probability < LOW_RISK_THRESHOLD:
        risk_level = "Low"

    elif risk_probability < HIGH_RISK_THRESHOLD:
        risk_level = "Moderate"

    else:
        risk_level = "High"


    # Final-grade regression model
    # Uses student information plus G1 and G2.

    grade_data = student_data.copy()

    grade_data["G1"] = G1
    grade_data["G2"] = G2

    grade_prediction = grade_model.predict(
        grade_data
    )[0]

    grade_prediction = max(
        0,
        min(20, grade_prediction),
    )


    # Grade-based status

    grade_status = (
        "At Risk"
        if grade_prediction < 10
        else "Not At Risk"
    )


    # Prediction results

    st.markdown("---")

    st.subheader("Prediction Result")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Predicted Final Grade",
            f"{grade_prediction:.2f} / 20",
        )

    with col2:
        if grade_status == "At Risk":
            st.error(
                "Grade-Based Status: At Risk"
            )
        else:
            st.success(
                "Grade-Based Status: Not At Risk"
            )

    with col3:
        if risk_level == "High":
            st.error(
                "Early-Risk Level: High"
            )

        elif risk_level == "Moderate":
            st.warning(
                "Early-Risk Level: Moderate"
            )

        else:
            st.success(
                "Early-Risk Level: Low"
            )

    with col4:
        st.metric(
            "Early-Risk Probability",
            f"{risk_probability:.1%}",
        )


    binary_status = (
        "At Risk"
        if risk_prediction == 1
        else "Not At Risk"
    )


    st.caption(
        f"Early-intervention classification: **{binary_status}** "
        f"(tuned threshold: {RISK_THRESHOLD:.1%})."
    )


    st.info(
        "Predicted final grade uses student information plus G1 and G2. "
        "Grade-based status is At Risk when the predicted grade is below 10. "
        "Early-risk probability comes from the classifier using student "
        "information without G1, G2, or G3. Risk level is Low below 30%, "
        "Moderate from 30% to below 70%, and High at 70% or above."
    )