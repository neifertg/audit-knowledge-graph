-- Round 5: entities exposed to a vendor, directly or through fourth parties
WITH RECURSIVE upstream(vendor) AS (
  SELECT :vendor
  UNION
  SELECT r.vendor
  FROM vendor_relies_on AS r
  JOIN upstream AS u ON r.relies_on = u.vendor)
SELECT p.auditable_entity_id,
  CASE WHEN MAX(s.vendor = :vendor) = 1 THEN 'direct' ELSE 'fourth_party_only' END AS exposure
FROM auditable_entity_performs_process AS p
JOIN process_runs_on_system AS ro ON ro.process_id = p.process_id
JOIN system AS s ON s.system_id = ro.system_id
JOIN upstream AS u ON u.vendor = s.vendor
GROUP BY p.auditable_entity_id
ORDER BY p.auditable_entity_id;
