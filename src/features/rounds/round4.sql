-- Round 4: every path from a regulation to a business unit
SELECT rq.regulation_id, o.business_unit_id, COUNT(*) AS paths
FROM requires AS rq
JOIN mitigates AS mi ON mi.control_id = rq.control_id
JOIN exposed_to AS ex ON ex.risk_id = mi.risk_id
JOIN business_unit_owns_auditable_entity AS o ON o.auditable_entity_id = ex.auditable_entity_id
GROUP BY rq.regulation_id, o.business_unit_id
ORDER BY rq.regulation_id, o.business_unit_id;
