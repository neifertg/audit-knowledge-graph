-- Round 6: repeat findings in disguise
WITH repeat AS (
  SELECT ac.control_id
  FROM issue_against_control_ia AS ac
  JOIN issue AS i ON i.issue_id = ac.issue_id
  GROUP BY ac.control_id
  HAVING COUNT(DISTINCT substr(i.opened_date, 1, 4)) >= 2)
SELECT ac.control_id, i.issue_id, i.opened_date, i.title
FROM repeat AS r
JOIN issue_against_control_ia AS ac ON ac.control_id = r.control_id
JOIN issue AS i ON i.issue_id = ac.issue_id
ORDER BY ac.control_id, i.issue_id;
