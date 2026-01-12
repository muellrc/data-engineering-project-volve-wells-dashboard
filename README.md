# Volve Wells AI Platform: Data Engineering & LLM Integration

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Volve Wells AI Platform                             │
│          Data Engineering, Visualization & LLM Integration             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐
│   Source     │         │   Source     │
│   Files      │         │   Files      │
│              │         │              │
│ • XML (EDM)  │         │ • CSV        │
│   Well Data  │         │   Production │
└──────┬───────┘         └──────┬───────┘
       │                        │
       └──────────┬─────────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Luigi Workflow      │
       │  (ETL Pipeline)      │
       │                      │
       │  • Extract           │
       │  • Transform         │
       │  • Validate          │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │   PostgreSQL          │
       │   Database            │
       │                       │
       │  • production_data    │
       │  • wells_data         │
       │  • wellbores_data     │
       └───────┬───────────────┘
               │
       ┌───────┴───────────────┬──────────────────┐
       │                        │                  │
       ▼                        ▼                  ▼
┌──────────────┐      ┌──────────────┐   ┌──────────────┐
│   Grafana    │      │  MCP Server   │   │  LLM Client  │
│  Dashboard   │      │               │   │  (Claude/    │
│              │      │  • 8 Tools    │   │   Cursor)    │
│ Visualization│      │  • Query API  │   │              │
│              │      │  • Protocol   │   │ Natural      │
│ • Wells Map  │      │    Handler    │   │ Language     │
│ • Production │      └───────┬───────┘   │ Queries      │
│   Metrics    │              │           └──────┬───────┘
└──────────────┘              │                  │
                               │                  │
                               └────────┬─────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  Natural Language│
                              │  Database Queries│
                              │  via MCP Protocol│
                              └─────────────────┘
```

## Introduction

The data ingested comes from a XML file containing Technical Well Data (original source: EDM) and Production data from a csv file, both from the [Volve Dataset](https://www.equinor.com/news/archive/14jun2018-disclosing-volve-data), an open dataset which was disclosed in 2018 by Norwegian public company Equinor. <br />

A Batch-based python code, running every day on a docker container and managed by the Luigi package extracts this data and run transformations on it, such as making sure only valid Wells are ingested and cleaning production data measurements. <br />

After data transformation, Luigi, the package that manages the python batches while running on a standard Docker container, writes the transformed data into a PostgreSQL database which is running on another standard Docker container. <br />

For the visualization, a dashboard in Grafana (running on another standard Docker container) shows the Wells, Wellbores and their locations, and the Volumetric Data for Produced Oil, Water & Injected Water previously transformed and stored in the PostgreSQL database.

Additionally, the project includes a **Model Context Protocol (MCP) Server** that enables LLM integration, allowing AI assistants like Claude to query and analyze the Volve wells database through natural language. The MCP server exposes 8 database query tools and can be integrated with LLM clients for interactive data exploration. See the [MCP Server documentation](mcp_server/README.md) for details.

A Docker network is used to ensure security.<br />

## Prerequisites

This project requires **Docker** and **Docker Compose** to be installed on your machine.

### Installing Docker on macOS

1. **Download Docker Desktop for Mac:**
   - Visit [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
   - Download Docker Desktop for Mac (choose the version for your chip: Intel or Apple Silicon/M1/M2)
   - Open the downloaded `.dmg` file and drag Docker to your Applications folder

2. **Install and Start Docker:**
   - Open Docker from your Applications folder
   - Follow the installation wizard
   - Docker Desktop will start automatically and you'll see the Docker icon in your menu bar
   - Wait for Docker to fully start (the icon will stop animating when ready)

3. **Verify Installation:**
   Open a terminal and run:
   ```bash
   docker --version
   docker compose version
   ```
   
   You should see version numbers for both commands. 
   
   **Note:** Newer versions of Docker Desktop (v2.0+) use `docker compose` (with a space) instead of `docker-compose` (with a hyphen). Both commands work, but `docker compose` is the recommended approach.

### System Requirements

- **macOS:** 10.15 or newer (Catalina or later)
- **RAM:** At least 4GB (8GB recommended)
- **Disk Space:** At least 5GB free space

## How to Run

Once Docker is installed and running, follow these steps:

**Step 1:** Navigate to the project directory:
```bash
cd /path/to/data-engineering-project-volve-wells-dashboard
```

**Step 2:** Build the Docker containers:
```bash
docker compose build
```
*(Note: If `docker compose` doesn't work, try `docker-compose build`)*

**Step 3:** Start all services:
```bash
docker compose up
```
*(Note: If `docker compose` doesn't work, try `docker-compose up`)*

The containers will start in the following order:
1. PostgreSQL database (waits until healthy)
2. Grafana dashboard
3. Luigi Python workflow (waits for PostgreSQL to be ready)
4. MCP Server (waits for PostgreSQL to be ready)

**Step 4:** Monitor the status updates from luigi until the final workflow is executed and the message is shown:

```
===== Luigi Execution Summary =====
Scheduled 1 tasks of which:
* 1 ran successfully:
- 1 workflow()
This progress looks :) because there were no failed tasks or missing dependencies 
===== Luigi Execution Summary =====
```

**Step 5:** Open the Grafana dashboard in http://127.0.0.1:8080/d/aJotvZlnk/wells?orgId=1

**Optional - Step 6:** The MCP server is now running and ready to accept connections. You can integrate it with LLM clients like Claude Desktop or Cursor. See the [MCP Server documentation](mcp_server/README.md) for setup instructions.

### Running in Background (Detached Mode)

To run the containers in the background, use:
```bash
docker compose up -d
```

To view logs:
```bash
docker compose logs -f
```

To view logs for a specific service:
```bash
docker compose logs -f dev-luigi-python
```

To stop all containers:
```bash
docker compose down
```

To stop and remove volumes (clean slate):
```bash
docker compose down -v
```

## Troubleshooting

### Docker is not running
- Make sure Docker Desktop is running (check the menu bar icon)
- If Docker Desktop isn't starting, try restarting your Mac

### Port already in use
If you get an error about ports being in use:
- **Port 5432 (PostgreSQL):** Check if you have a local PostgreSQL instance running
- **Port 8080 (Grafana):** Another service might be using this port
- **Port 8082 (Luigi):** Another service might be using this port

You can change the ports in `docker-compose.yaml` if needed.

### Build fails
- Make sure you have a stable internet connection (Docker needs to download images)
- Try running `docker compose build --no-cache` to rebuild from scratch
- Check that all source files are present in `python/source-files/`

### Luigi container exits immediately
- This is normal! The Luigi workflow runs once and completes. Check the logs with `docker compose logs dev-luigi-python` to verify it completed successfully.
- If you see connection errors, make sure PostgreSQL is healthy: `docker compose ps`

### Accessing the services
- **Grafana Dashboard:** http://127.0.0.1:8080/d/aJotvZlnk/wells?orgId=1
- **PostgreSQL:** localhost:5432 (username: postgres, password: postgres)
- **MCP Server:** Running via stdio transport (see [MCP Server README](mcp_server/README.md) for integration instructions)


## Components

The following containers are used to provide the functionality described above:

- **dev-postgres-db:** Container based on PostgreSQL 15 Docker image, with an initialization script that creates the tables `production_data`, `wells_data` and `wellbores_data`. Includes a healthcheck to ensure the database is ready before other services start.

- **dev-luigi-python:** Container based on Python 3.11 Docker image with the Luigi module used to build pipelines of batch jobs. Includes dependencies: luigi, psycopg2-binary, pandas, sqlalchemy, lxml, and requests. The workflow runs once on container startup and then exits.

- **dev-grafana:** Container based on Grafana Docker image, with a dashboard called "Wells" provisioned via Dockerfile. Accessible at http://127.0.0.1:8080

- **dev-mcp-server:** Container running the Volve Wells MCP (Model Context Protocol) server, which exposes database query tools for LLM integration. Allows AI assistants like Claude to interact with the Volve wells database through natural language queries. Provides 8 tools for querying production data, well statistics, geographic searches, anomaly detection, and more. See the [MCP Server README](mcp_server/README.md) for detailed documentation and the [Learning Guide](mcp_server/LEARNING_GUIDE.md) for an in-depth explanation of MCP servers.






