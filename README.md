# Data Engineering Project: Volve Wells Dashboard

<img width="356" src="https://user-images.githubusercontent.com/89973885/166164396-756806d6-d730-4e5b-ba4c-d53a66783949.png">


## Introduction

The data ingested comes from a XML file containing Technical Well Data (original source: EDM) and Production data from a csv file, both from the [Volve Dataset](https://www.equinor.com/news/archive/14jun2018-disclosing-volve-data), an open dataset which was disclosed in 2018 by Norwegian public company Equinor. <br />

A Batch-based python code, running every day on a docker container and managed by the Luigi package extracts this data and run transformations on it, such as making sure only valid Wells are ingested and cleaning production data measurements. <br />

After data transformation, Luigi, the package that manages the python batches while running on a standard Docker container, writes the transformed data into a PostgreSQL database which is running on another standard Docker container. <br />

For the visualization, a dashboard in Grafana (running on another standard Docker container) shows the Wells, Wellbores and their locations, and the Volumetric Data for Produced Oil, Water & Injected Water previously transformed and stored in the PostgreSQL database:

<img alt="image" src="https://user-images.githubusercontent.com/89973885/166163284-a914ac1c-56a7-462b-a25a-d61c3d54e6dc.png">

A Docker network is used to ensure security.<br />

## How to Run

To run this project, simply call docker-compose:<br />

Step 1: docker-compose build <br />
Step 2: docker-compose up <br />
Step 3: Monitor the status updates from luigi until the workflow is executed <br />
Step 4: Open the Grafana dashboard in http://127.0.0.1:8080/d/aJotvZlnk/wells?orgId=1

## Components:

The following containers are used to provide the functionality described above:

- dev-postgres-db: Container based on a standard postgres Docker image, with an initialisation script that creates the tables production_data, wells_data and wellbores_data.

- dev-luigi-python: Container based on a standard Python Docker image with the Luigi module used to build  pipelines of batch jobs installed during provisioning along with other prerequisites.

- dev-grafana: Container based on a standard Grafana Docker image, with a dashboard called Wells provisioned via Dockerfile.






