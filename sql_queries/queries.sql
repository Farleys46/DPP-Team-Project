-- =========================================
-- SkySense Flight DATABASE | Test - QUERIES
-- =========================================

# Queries that MUST show in dashboard, should be put in the main.py!

-- Query 1: Compiled Flight Data
SELECT 
    (SELECT COUNT(*) FROM air_quality) as total_aq_rows,
    (SELECT COUNT(*) FROM live_flights) as total_flights,
    (SELECT MAX(db_timestamp) FROM air_quality) as last_update;

-- Query 2
SELECT 
    date_trunc('hour', f.timestamp) AS tidsintervall,
    COUNT(DISTINCT f.callsign) AS antal_flyg,
    ROUND(AVG(a.value)::numeric, 1) AS snitt_pm10
FROM live_flights f
LEFT JOIN air_quality a ON date_trunc('hour', f.timestamp) = date_trunc('hour', a.db_timestamp)
WHERE a.parameter = 'pm10'
GROUP BY tidsintervall
ORDER BY tidsintervall DESC;

-- Query 3: 
