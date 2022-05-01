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


CREATE TABLE wells_data (
	geo_offset_east float,
	well_legal_name text,
	geo_longitude float,
	wellhead_depth float,
	geo_latitude float,
	geo_offset_north float,
	water_depth float
);

CREATE TABLE wellbores_data (
	geo_latitude_ko float,
    geo_longitude_ko float,
    geo_latitude_bh float,
    geo_longitude_bh float,
    geo_offset_east_bh float,
    geo_offset_north_ko float
	geo_offset_north_bh float,
	geo_offset_east_ko float,
	ko_md float,
	bh_md float,
	rig_name text,
	wellbore_name text,
	well_legal_name text
);
