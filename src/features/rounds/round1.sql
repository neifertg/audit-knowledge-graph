-- Round 1: open issues by business unit and rating
SELECT b.business_unit_id, b.name AS business_unit_name, i.rating,
  COUNT(DISTINCT i.issue_id) AS open_issues
FROM issue AS i
JOIN against_risk AS ar ON ar.issue_id = i.issue_id
JOIN exposed_to AS ex ON ex.risk_id = ar.risk_id
JOIN business_unit_owns_auditable_entity AS o ON o.auditable_entity_id = ex.auditable_entity_id
JOIN business_unit AS b ON b.business_unit_id = o.business_unit_id
WHERE i.closed_date IS NULL
GROUP BY b.business_unit_id, b.name, i.rating
ORDER BY b.business_unit_id, i.rating;
