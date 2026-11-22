// Round 4: every path from a regulation to a business unit
MATCH (g:Regulation)-[:REQUIRES]->(:Control)-[:MITIGATES]->(:Risk)
  <-[:EXPOSED_TO]-(:AuditableEntity)<-[:OWNS]-(b:BusinessUnit)
RETURN g.id AS regulation_id, b.id AS business_unit_id, count(*) AS paths
ORDER BY regulation_id, business_unit_id;
