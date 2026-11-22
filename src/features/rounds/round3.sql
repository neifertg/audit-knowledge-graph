-- Round 3: shared-system blast radius
SELECT s.system_id, s.name AS system_name, COUNT(DISTINCT ex.auditable_entity_id) AS entities
FROM system AS s
JOIN depends_on AS d ON d.system_id = s.system_id
JOIN mitigates AS mi ON mi.control_id = d.control_id
JOIN exposed_to AS ex ON ex.risk_id = mi.risk_id
GROUP BY s.system_id, s.name
ORDER BY entities DESC, system_name
LIMIT 3;
