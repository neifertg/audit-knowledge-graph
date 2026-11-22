-- Supporting query: owner concentration of key controls
SELECT o.person_id, COUNT(DISTINCT c.control_id) AS key_controls,
  COUNT(DISTINCT bo.business_unit_id) AS business_units
FROM owned_by AS o
JOIN control AS c ON c.control_id = o.control_id
LEFT JOIN mitigates AS mi ON mi.control_id = c.control_id
LEFT JOIN exposed_to AS ex ON ex.risk_id = mi.risk_id
LEFT JOIN business_unit_owns_auditable_entity AS bo
  ON bo.auditable_entity_id = ex.auditable_entity_id
WHERE c.key_control = 'Y'
GROUP BY o.person_id
ORDER BY key_controls DESC, business_units DESC, o.person_id
LIMIT 10;
