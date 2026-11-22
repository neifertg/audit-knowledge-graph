// Supporting query: owner concentration of key controls
MATCH (p:Person)<-[:OWNED_BY]-(c:Control {key_control: 'Y'})
OPTIONAL MATCH (c)-[:MITIGATES]->(:Risk)<-[:EXPOSED_TO]-(:AuditableEntity)<-[:OWNS]-(b:BusinessUnit)
RETURN p.id AS person_id, count(DISTINCT c) AS key_controls, count(DISTINCT b) AS business_units
ORDER BY key_controls DESC, business_units DESC, person_id
LIMIT 10;
