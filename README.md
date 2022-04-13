# DLMDSEDE02-project-cmueller

## Conception Phase

The data ingested will come from a XML file containing Technical Well Data from an open dataset called Volve Dataset, very commonly used within the Oil & Gas sector and provided by Norwegian public company Equinor. A Batch based python code, running every day on a docker container and managed by the Luigi package will extract this data and run transformations on it, such as listing all Wells and converting measurements for wellbore trajectories.
After data transformation, Luigi, the package that manages the python batches while running on a standard Docker container, will write the transformed data into a PostgreSQL database which is running on another standard Docker container.
For the visualization, a dashboard in Grafana will show the trajectory data and wells previously transformed and stored in the PostgreSQL database. The Grafana installation will run on another (standard) Docker container.
A Docker network with carefully configured ports will be used to ensure security, and appropriate login security will be used. Reliability, scalability, and maintainability are ensured by the usage of standard Docker images and open source data, which are easily maintained and with plenty of documentation available in case future scope increase-related updates and changes are needed.

<img width="356" alt="image" src="https://user-images.githubusercontent.com/89973885/163265110-8570641c-825e-4de7-82c2-8b7fb55327fd.png">
