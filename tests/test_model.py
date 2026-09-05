import json
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RISK_MODEL_PATH = PROJECT_ROOT / "models" / "student_risk_model.joblib"
GRADE_MODEL_PATH = PROJECT_ROOT / "models" / "student_grade_model.joblib"
RISK_CONFIG_PATH = PROJECT_ROOT / "models" / "risk_threshold.json"


def load_models():
    risk_model = joblib.load(RISK_MODEL_PATH)
    grade_model = joblib.load(GRADE_MODEL_PATH)

    with open(RISK_CONFIG_PATH, "r", encoding="utf-8") as file:
        risk_config = json.load(file)

    return risk_model, grade_model, risk_config


def create_early_student():
    return pd.DataFrame([{
        "school": "GP",
        "sex": "F",
        "age": 17,
        "address": "U",
        "famsize": "GT3",
        "Pstatus": "T",
        "Medu": 3,
        "Fedu": 3,
        "Mjob": "services",
        "Fjob": "services",
        "reason": "course",
        "guardian": "mother",
        "traveltime": 2,
        "studytime": 2,
        "failures": 0,
        "schoolsup": "yes",
        "famsup": "yes",
        "paid": "no",
        "activities": "yes",
        "nursery": "yes",
        "higher": "yes",
        "internet": "yes",
        "romantic": "no",
        "famrel": 4,
        "freetime": 3,
        "goout": 3,
        "Dalc": 1,
        "Walc": 1,
        "health": 3,
        "absences": 5,
    }])


def test_models_and_configuration_load():
    risk_model, grade_model, risk_config = load_models()

    assert risk_model is not None
    assert grade_model is not None
    assert "classification_threshold" in risk_config
    assert "low_risk_threshold" in risk_config
    assert "high_risk_threshold" in risk_config


def test_early_risk_model_has_no_grade_leakage():
    risk_model, _, _ = load_models()

    risk_features = set(risk_model.feature_names_in_)

    assert not {"G1", "G2", "G3"} & risk_features


def test_grade_model_uses_g1_g2_but_not_g3():
    _, grade_model, _ = load_models()

    grade_features = set(grade_model.feature_names_in_)

    assert "G1" in grade_features
    assert "G2" in grade_features
    assert "G3" not in grade_features


def test_risk_prediction_and_probability():
    risk_model, _, risk_config = load_models()

    student = create_early_student()

    risk_threshold = risk_config["classification_threshold"]

    risk_probability = risk_model.predict_proba(student)[0, 1]
    risk_prediction = int(risk_probability >= risk_threshold)

    assert risk_prediction in [0, 1]
    assert 0 <= risk_probability <= 1
    assert 0 <= risk_threshold <= 1


def test_risk_level():
    risk_model, _, risk_config = load_models()

    student = create_early_student()

    risk_probability = risk_model.predict_proba(student)[0, 1]

    low_threshold = risk_config["low_risk_threshold"]
    high_threshold = risk_config["high_risk_threshold"]

    if risk_probability < low_threshold:
        risk_level = "Low"
    elif risk_probability < high_threshold:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    assert risk_level in ["Low", "Moderate", "High"]


def test_final_grade_prediction():
    _, grade_model, _ = load_models()

    student = create_early_student()

    student["G1"] = 11
    student["G2"] = 12

    grade_prediction = grade_model.predict(student)[0]

    assert 0 <= grade_prediction <= 20