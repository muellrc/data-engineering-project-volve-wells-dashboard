CREATE TABLE wellbores_clean (wellbore_key varchar(15), wellbore_name varchar(50));

CREATE TABLE trajectories_clean (
  Wellbore varchar(50),
  MeasuredDepth decimal,
  Azimuth decimal,
  Inclination decimal
);
