// Round 6: repeat findings in disguise
MATCH (c:Control {source: 'IA'})<-[:AGAINST]-(i:Issue)
WITH c, collect(i) AS issues, count(DISTINCT substring(i.opened_date, 0, 4)) AS years
WHERE years >= 2
UNWIND issues AS i
RETURN c.id AS control_id, i.issue_id AS issue_id, i.opened_date AS opened_date, i.title AS title
ORDER BY control_id, issue_id;
