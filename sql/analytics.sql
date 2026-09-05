-- ============================================================
-- Student Performance Analytics
-- SQL Analytics Layer
-- ============================================================


-- ============================================================
-- 1. Overall student and academic summary
-- ============================================================

SELECT
    COUNT(*) AS total_students,
    ROUND(AVG(G1), 2) AS average_g1,
    ROUND(AVG(G2), 2) AS average_g2,
    ROUND(AVG(G3), 2) AS average_g3,
    ROUND(AVG(absences), 2) AS average_absences
FROM fact_student_performance;


-- ============================================================
-- 2. Observed historical at-risk summary
--
-- observed_at_risk = 1 when G3 < 10
-- This is historical observed status, NOT ML prediction.
-- ============================================================

SELECT
    COUNT(*) AS total_students,
    SUM(observed_at_risk) AS at_risk_students,
    ROUND(
        100.0 * SUM(observed_at_risk) / COUNT(*),
        2
    ) AS at_risk_percentage
FROM fact_student_performance;


-- ============================================================
-- 3. Final grade distribution
-- ============================================================

SELECT
    G3 AS final_grade,
    COUNT(*) AS student_count
FROM fact_student_performance
GROUP BY G3
ORDER BY G3;


-- ============================================================
-- 4. Final grade bands
-- ============================================================

SELECT
    CASE
        WHEN G3 < 10 THEN 'At Risk'
        WHEN G3 < 14 THEN 'Satisfactory'
        WHEN G3 < 17 THEN 'Good'
        ELSE 'Excellent'
    END AS grade_band,
    COUNT(*) AS student_count,
    ROUND(AVG(G3), 2) AS average_g3
FROM fact_student_performance
GROUP BY
    CASE
        WHEN G3 < 10 THEN 'At Risk'
        WHEN G3 < 14 THEN 'Satisfactory'
        WHEN G3 < 17 THEN 'Good'
        ELSE 'Excellent'
    END
ORDER BY
    CASE
        WHEN grade_band = 'At Risk' THEN 1
        WHEN grade_band = 'Satisfactory' THEN 2
        WHEN grade_band = 'Good' THEN 3
        WHEN grade_band = 'Excellent' THEN 4
    END;

-- ============================================================
-- 5. Academic performance by school
-- ============================================================

SELECT
    d.school_code,
    d.school_name,
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
GROUP BY
    d.school_code,
    d.school_name
ORDER BY average_g3 DESC;


-- ============================================================
-- 6. Academic performance by gender
-- ============================================================

SELECT
    s.sex,
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
GROUP BY s.sex
ORDER BY average_g3 DESC;

-- ============================================================
-- 7. Study time vs academic performance
-- ============================================================

SELECT
    s.studytime,
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
GROUP BY s.studytime
ORDER BY s.studytime;

-- ============================================================
-- 8. Previous failures vs academic performance
-- ============================================================

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
GROUP BY s.failures
ORDER BY s.failures;

-- ============================================================
-- 9. Absence bands vs academic performance
-- ============================================================

SELECT
    CASE
        WHEN f.absences <= 5 THEN '0-5'
        WHEN f.absences <= 10 THEN '6-10'
        WHEN f.absences <= 20 THEN '11-20'
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

FROM fact_student_performance f

GROUP BY
    CASE
        WHEN f.absences <= 5 THEN '0-5'
        WHEN f.absences <= 10 THEN '6-10'
        WHEN f.absences <= 20 THEN '11-20'
        ELSE '21+'
    END

ORDER BY
    CASE
        WHEN absence_band = '0-5' THEN 1
        WHEN absence_band = '6-10' THEN 2
        WHEN absence_band = '11-20' THEN 3
        WHEN absence_band = '21+' THEN 4
    END;

-- ============================================================
-- 10. Mother's education vs academic performance
-- ============================================================

SELECT
    s.Medu AS mother_education_level,
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
GROUP BY s.Medu
ORDER BY s.Medu;


-- ============================================================
-- 11. Father's education vs academic performance
-- ============================================================

SELECT
    s.Fedu AS father_education_level,
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
GROUP BY s.Fedu
ORDER BY s.Fedu;


-- ============================================================
-- 12. Internet access vs academic performance
-- ============================================================

SELECT
    s.internet AS internet_access,
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
GROUP BY s.internet
ORDER BY s.internet;


-- ============================================================
-- 13. Extracurricular activities vs academic performance
-- ============================================================

SELECT
    s.activities AS extracurricular_activities,
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
GROUP BY s.activities
ORDER BY s.activities;


-- ============================================================
-- 14. School support vs academic performance
-- ============================================================

SELECT
    s.schoolsup AS school_support,
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
GROUP BY s.schoolsup
ORDER BY s.schoolsup;


-- ============================================================
-- 15. Family support vs academic performance
-- ============================================================

SELECT
    s.famsup AS family_support,
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
GROUP BY s.famsup
ORDER BY s.famsup;

-- 16. Combined Risk Segment Analysis
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
GROUP BY risk_segment
ORDER BY
    CASE risk_segment
        WHEN 'Low Historical Risk' THEN 1
        WHEN 'Moderate Historical Risk' THEN 2
        WHEN 'High Historical Risk' THEN 3
        WHEN 'Very High Historical Risk' THEN 4
    END;