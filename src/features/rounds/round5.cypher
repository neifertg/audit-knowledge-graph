// Round 5: entities exposed to a vendor, directly or through fourth parties
MATCH p = (e:AuditableEntity)-[:PERFORMS]->(:Process)-[:RUNS_ON]->(:System)
  -[:SUPPLIED_BY]->(:Vendor)-[:RELIES_ON*0..]->(:Vendor {name: $vendor})
RETURN e.id AS auditable_entity_id,
  CASE WHEN min(length(p)) = 3 THEN 'direct' ELSE 'fourth_party_only' END AS exposure
ORDER BY auditable_entity_id;
