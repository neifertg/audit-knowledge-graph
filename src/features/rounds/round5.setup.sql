-- Round 5 setup: the fourth-party register arrives as a new table
CREATE TEMP TABLE vendor_relies_on (vendor TEXT NOT NULL, relies_on TEXT NOT NULL);
INSERT INTO vendor_relies_on (vendor, relies_on)
VALUES (:vendor, :relies_on);
