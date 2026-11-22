// Round 5 setup: vendors become nodes, and the fourth-party register becomes edges
MATCH (s:System)
MERGE (v:Vendor {name: s.vendor})
CREATE (s)-[:SUPPLIED_BY]->(v);
UNWIND $rows AS row
MERGE (a:Vendor {name: row.vendor})
MERGE (b:Vendor {name: row.relies_on})
CREATE (a)-[:RELIES_ON]->(b);
