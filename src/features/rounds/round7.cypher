// Round 7: year-over-year findings by ERM L1 (regulator, self-identified and 2nd-line issues)
MATCH (l1:TaxonomyNode {source: 'ERM', level: 1})-[:PARENT_OF*2]->(:TaxonomyNode)
  -[:CLASSIFIES]->(:Risk)<-[:AGAINST]-(i:Issue)
WHERE i.source <> 'IA'
RETURN l1.id AS l1_node_id, l1.name AS l1_name, substring(i.opened_date, 0, 4) AS year,
  count(DISTINCT i) AS issues
ORDER BY l1_node_id, year;
