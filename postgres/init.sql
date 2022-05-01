CREATE TABLE production_data (
  productiontime datetime,
  wellbore TEXT,
  boreoilvol float,
  boregasvol float,
  borewatvol float,
  borewivol float,
  flowkind text,
  welltype text
);

CREATE TABLE drilling_data (
  wellbore TEXT,
  measureddepth float,
  azimuth float,
  inclination float
);

CREATE TABLE wellbore_data (
	geo_latitude_ko float,
    geo_longitude_ko float,
    geo_latitude_bh float,
    geo_longitude_bh float,
    geo_offset_east_bh float,
    geo_offset_north_ko float
	geo_offset_north_bh float,
	geo_offset_east_ko float,
    wellbore_type_id text,
	wellbore_id text,
	ko_md float,
	well_id text,
	bh_md float,
	ow_well_uwi text,
	rig_name text,
	wellbore_name text,
	create_date text,	
	update_date text,
	is_deviated text,
	parent_wellbore_id text,
	well_legal_name text,
	default_fluid_id text,
	wellbore_type_policy_id text,
);
