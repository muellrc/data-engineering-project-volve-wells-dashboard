CREATE TABLE production_data (
  productiontime timestamp,
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
    geo_offset_north_ko float,
	geo_offset_north_bh float,
	geo_offset_east_ko float,
	ko_md float,
	bh_md float,
	rig_name text,
	wellbore_name text,
	well_legal_name text
);

-- Maintenance Work Orders Table (SAP Plant Maintenance simulation)
CREATE TABLE IF NOT EXISTS maintenance_work_orders (
    work_order_id SERIAL PRIMARY KEY,
    well_legal_name VARCHAR(255) NOT NULL,
    wellbore_name VARCHAR(255),
    maintenance_type VARCHAR(100) NOT NULL,  -- 'preventive', 'corrective', 'predictive'
    priority VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    scheduled_date DATE NOT NULL,
    estimated_duration_hours DECIMAL(10,2),
    description TEXT,
    predicted_failure_date DATE,
    confidence_score DECIMAL(5,2),  -- 0-100
    status VARCHAR(20) DEFAULT 'scheduled',  -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'predictive_maintenance_agent',
    completed_at TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_work_orders_well ON maintenance_work_orders(well_legal_name);
CREATE INDEX idx_work_orders_status ON maintenance_work_orders(status);
CREATE INDEX idx_work_orders_scheduled ON maintenance_work_orders(scheduled_date);
