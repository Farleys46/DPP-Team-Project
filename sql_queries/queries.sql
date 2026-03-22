-- =========================================
-- SkySense Flight DATABASE | Test - QUERIES
-- =========================================

# Queries that MUST show in dashboard, should be put in the main.py!

-- Query 1: Compiled Flight Data
SELECT 
    (SELECT COUNT(*) FROM air_quality) as total_aq_rows,
    (SELECT COUNT(*) FROM live_flights) as total_flights,
    (SELECT MAX(db_timestamp) FROM air_quality) as last_update;

-- Query 2: Air traffic and air quality, hour by hour comparison
SELECT 
    date_trunc('hour', f.timestamp) AS tidsintervall,
    COUNT(DISTINCT f.callsign) AS antal_flyg,
    ROUND(AVG(a.value)::numeric, 1) AS snitt_pm10
FROM live_flights f
LEFT JOIN air_quality a ON date_trunc('hour', f.timestamp) = date_trunc('hour', a.db_timestamp)
WHERE a.parameter = 'pm10'
GROUP BY tidsintervall
ORDER BY tidsintervall DESC;

-- Query 3: Top 5 most polluted stations
SELECT 
    station_name, 
    ROUND(AVG(value)::numeric, 1) as medelvärde_pm10,
    COUNT(*) as antal_mätningar,
    MAX(db_timestamp) as senaste_mätning
FROM air_quality
WHERE parameter = 'pm10'
GROUP BY station_name
HAVING COUNT(*) > 5 -- Vi vill bara se stationer som skickat minst 5 värden
ORDER BY medelvärde_pm10 DESC
LIMIT 5;