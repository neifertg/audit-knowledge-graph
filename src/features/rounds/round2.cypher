// Round 2: High canonical risks with stale coverage
MATCH (c:CanonicalRisk)<-[:MAPS_TO]-(r:Risk)
WITH c, collect(r) AS members
WHERE any(m IN members WHERE m.inherent_rating = 'High')
  AND NOT EXISTS {
    MATCH (c)<-[:MAPS_TO]-(:Risk)<-[:MITIGATES]-(:Control)<-[:TESTED]-(a:Audit)
    WHERE a.end_date >= $cutoff }
RETURN c.id AS canonical_risk_id,
  CASE WHEN any(m IN members WHERE m.source = 'IA') THEN 'Y' ELSE 'N' END AS has_ia_member
ORDER BY canonical_risk_id;
