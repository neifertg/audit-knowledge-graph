// Round 1: open issues by business unit and rating
MATCH (i:Issue)-[:AGAINST]->(:Risk)<-[:EXPOSED_TO]-(:AuditableEntity)<-[:OWNS]-(b:BusinessUnit)
WHERE i.closed_date IS NULL
RETURN b.id AS business_unit_id, b.name AS business_unit_name, i.rating AS rating,
  count(DISTINCT i) AS open_issues
ORDER BY business_unit_id, rating;
