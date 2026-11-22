-- Round 7: year-over-year findings by ERM L1 (regulator, self-identified and 2nd-line issues)
SELECT l1.taxonomy_node_id AS l1_node_id, l1.name AS l1_name, substr(i.opened_date, 1, 4) AS year,
  COUNT(DISTINCT i.issue_id) AS issues
FROM issue AS i
JOIN issue_against_risk_erm AS ar ON ar.issue_id = i.issue_id
JOIN taxonomy_node_classifies_risk_erm AS c ON c.risk_id = ar.risk_id
JOIN taxonomy_node_parent_of_taxonomy_node_erm AS p3 ON p3.child_id = c.taxonomy_node_id
JOIN taxonomy_node_parent_of_taxonomy_node_erm AS p2 ON p2.child_id = p3.parent_id
JOIN taxonomy_node_erm AS l1 ON l1.taxonomy_node_id = p2.parent_id
WHERE i.source <> 'IA'
GROUP BY l1.taxonomy_node_id, l1.name, year
ORDER BY l1_node_id, year;
