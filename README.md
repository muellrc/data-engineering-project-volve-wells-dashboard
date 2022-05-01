# Data Engineering Project: Volve Dataset Wells Dashboard

<img width="356" alt="image" src="https://user-images.githubusercontent.com/89973885/163265110-8570641c-825e-4de7-82c2-8b7fb55327fd.png">

The data ingested comes from a XML file containing Technical Well Data (original source: EDM) from an open dataset called Volve Dataset, very commonly used within the Oil & Gas sector and provided by Norwegian public company Equinor. 
A Batch-based python code, running every day on a docker container and managed by the Luigi package extracts this data and run transformations on it, such as making sure only valid Wells are ingested and cleaning production data measurements.
After data transformation, Luigi, the package that manages the python batches while running on a standard Docker container, writes the transformed data into a PostgreSQL database which is running on another standard Docker container.
For the visualization, a dashboard in Grafana (running on another standard Docker container) shows the Wells, Wellbores and their locations, and the Volumetric Data for Produced Oil, Water & Injected Water previously transformed and stored in the PostgreSQL database:

<img alt="image" src="https://user-images.githubusercontent.com/89973885/166163284-a914ac1c-56a7-462b-a25a-d61c3d54e6dc.png">

A Docker network is used to ensure security.

