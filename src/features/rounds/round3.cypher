// Round 3: shared-system blast radius
MATCH (s:System)<-[:DEPENDS_ON]-(:Control)-[:MITIGATES]->(:Risk)<-[:EXPOSED_TO]-(e:AuditableEntity)
RETURN s.id AS system_id, s.name AS system_name, count(DISTINCT e) AS entities
ORDER BY entities DESC, system_name
LIMIT 3;
