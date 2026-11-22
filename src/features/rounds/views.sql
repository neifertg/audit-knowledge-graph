-- Shared views: one per relationship that ERM and IA publish as separate tables.
CREATE TEMP VIEW risk AS
SELECT 'ERM' AS source, risk_id, inherent_rating
FROM risk_erm
UNION ALL
SELECT 'IA', risk_id, inherent_rating
FROM risk_ia;
CREATE TEMP VIEW mitigates AS
SELECT control_id, risk_id
FROM control_mitigates_risk_erm
UNION ALL
SELECT control_id, risk_id
FROM control_mitigates_risk_ia;
CREATE TEMP VIEW exposed_to AS
SELECT auditable_entity_id, risk_id
FROM auditable_entity_exposed_to_risk_erm
UNION ALL
SELECT auditable_entity_id, risk_id
FROM auditable_entity_exposed_to_risk_ia;
CREATE TEMP VIEW against_risk AS
SELECT issue_id, risk_id
FROM issue_against_risk_erm
UNION ALL
SELECT issue_id, risk_id
FROM issue_against_risk_ia;
CREATE TEMP VIEW depends_on AS
SELECT control_id, system_id
FROM control_depends_on_system_erm
UNION ALL
SELECT control_id, system_id
FROM control_depends_on_system_ia;
CREATE TEMP VIEW requires AS
SELECT regulation_id, control_id
FROM regulation_requires_control_erm
UNION ALL
SELECT regulation_id, control_id
FROM regulation_requires_control_ia;
CREATE TEMP VIEW control AS
SELECT 'ERM' AS source, control_id, key_control
FROM control_erm
UNION ALL
SELECT 'IA', control_id, key_control
FROM control_ia;
CREATE TEMP VIEW owned_by AS
SELECT control_id, person_id
FROM control_owned_by_person_erm
UNION ALL
SELECT control_id, person_id
FROM control_owned_by_person_ia;
