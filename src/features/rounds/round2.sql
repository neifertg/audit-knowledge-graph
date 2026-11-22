-- Round 2: High canonical risks with stale coverage
WITH fresh AS (
  SELECT DISTINCT m.canonical_risk_id
  FROM risk_maps_to_canonical AS m
  JOIN mitigates AS mi ON mi.risk_id = m.risk_id
  JOIN audit_tested_control_ia AS t ON t.control_id = mi.control_id
  JOIN audit AS a ON a.audit_id = t.audit_id
  WHERE a.end_date >= :cutoff)
SELECT m.canonical_risk_id, MAX(CASE WHEN m.source = 'IA' THEN 'Y' ELSE 'N' END) AS has_ia_member
FROM risk_maps_to_canonical AS m
JOIN risk AS r ON r.risk_id = m.risk_id
LEFT JOIN fresh AS f ON f.canonical_risk_id = m.canonical_risk_id
WHERE f.canonical_risk_id IS NULL
GROUP BY m.canonical_risk_id
HAVING MAX(r.inherent_rating = 'High') = 1
ORDER BY m.canonical_risk_id;
