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
       ┌───────┴───────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┐
       │                        │                  │                  │                  │                  │
       ▼                        ▼                  ▼                  ▼                  ▼                  ▼
┌──────────────┐      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Grafana    │      │  MCP Server   │   │  NLQ Service  │   │ Data Quality │   │ Predictive   │   │  LLM Client  │
│  Dashboard   │      │               │   │  (REST API)  │   │    Agent     │   │ Maintenance  │   │  (Claude/    │
│              │      │  • 8 Tools    │   │              │   │  (Agentic AI)│   │    Agent     │   │   Cursor)    │
│ Visualization│      │  • Query API  │   │  • NL to SQL │   │              │   │ (Advanced    │   │              │
│              │      │  • Protocol   │   │  • Validation│   │  • Monitoring│   │  Agentic AI) │   │ Natural      │
│ • Wells Map  │      │    Handler    │   │  • Execution │   │  • Reasoning │   │              │   │ Language     │
│ • Production │      └───────┬───────┘   └──────┬───────┘   │  • Reports   │   │  • Predictive│   │ Queries      │
│   Metrics    │              │                  │           └──────┬───────┘   │  • Scheduling│   └──────┬───────┘
└──────────────┘              │                  │                  │           │  • SAP PM    │          │
                               │                  │                  │           │    Simulation│          │
                               │                  │                  │           └──────┬───────┘          │
                               │                  │                  │                  │                  │
                               └──────────────────┴──────────────────┴──────────────────┴──────────────────┘
                                                          │
                                                          ▼
                                          ┌───────────────────────────────┐
                                          │  AI-Powered Data Services    │
                                          │  • Natural Language Queries   │
                                          │  • Autonomous Quality Monitoring│
                                          │  • Predictive Maintenance    │
                                          │  • Intelligent Analysis      │
                                          └───────────────────────────────┘
```

## Introduction

The data ingested comes from a XML file containing Technical Well Data (original source: EDM) and Production data from a csv file, both from the [Volve Dataset](https://www.equinor.com/news/archive/14jun2018-disclosing-volve-data), an open dataset which was disclosed in 2018 by Norwegian public company Equinor. <br />

A Batch-based python code, running every day on a docker container and managed by the Luigi package extracts this data and run transformations on it, such as making sure only valid Wells are ingested and cleaning production data measurements. <br />

After data transformation, Luigi, the package that manages the python batches while running on a standard Docker container, writes the transformed data into a PostgreSQL database which is running on another standard Docker container. <br />

For the visualization, a dashboard in Grafana (running on another standard Docker container) shows the Wells, Wellbores and their locations, and the Volumetric Data for Produced Oil, Water & Injected Water previously transformed and stored in the PostgreSQL database.

Additionally, the project includes four AI-powered services for database interaction, data quality, and predictive maintenance:

- **Model Context Protocol (MCP) Server**: Enables LLM integration, allowing AI assistants like Claude to query and analyze the Volve wells database through natural language. The MCP server exposes 8 database query tools and can be integrated with LLM clients for interactive data exploration. See the [MCP Server documentation](mcp_server/README.md) and [Learning Guide](mcp_server/LEARNING_GUIDE.md) for details.

- **Natural Language Query (NLQ) Service**: A REST API that converts natural language questions to SQL queries using LLMs, validates them for safety, and executes them against the database. Supports multiple LLM providers (OpenAI, Anthropic, Ollama) and provides query explanations. See the [NLQ Service documentation](nlq_service/README.md) and [Learning Guide](nlq_service/LEARNING_GUIDE.md) for details.

- **Intelligent Data Quality Agent**: An autonomous agentic AI system that monitors data quality, investigates issues using reasoning and tools, and generates comprehensive reports with actionable recommendations. Uses LLMs for root cause analysis and combines automated checks with intelligent investigation. See the [Data Quality Agent documentation](data_quality_agent/README.md) and [Learning Guide](data_quality_agent/LEARNING_GUIDE.md) for details.

- **Predictive Maintenance Agent**: An advanced agentic AI system that analyzes production data patterns to predict maintenance needs and automatically creates maintenance work orders. Simulates SAP Plant Maintenance integration by storing work orders in a database table. Uses predictive models (decline detection, anomaly detection, equipment age analysis) combined with LLM reasoning for strategic maintenance planning. See the [Predictive Maintenance Agent documentation](predictive_maintenance_agent/README.md) and [Learning Guide](predictive_maintenance_agent/LEARNING_GUIDE.md) for details.

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
3. Ollama service (optional, for local LLM models)
4. Luigi Python workflow (waits for PostgreSQL to be ready)
5. MCP Server (waits for PostgreSQL to be ready)
6. NLQ Service (waits for PostgreSQL and Ollama to be ready)
7. Data Quality Agent (waits for PostgreSQL and Ollama to be ready)
8. Predictive Maintenance Agent (waits for PostgreSQL and Ollama to be ready)

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

**Optional - Step 6:** The AI services are now running:
- **MCP Server**: Ready to accept connections. You can integrate it with LLM clients like Claude Desktop or Cursor. See the [MCP Server documentation](mcp_server/README.md) for setup instructions.
- **NLQ Service**: REST API available at http://localhost:8000. You can query the database using natural language. See the [NLQ Service documentation](nlq_service/README.md) for usage examples. **Note**: Set `LLM_API_KEY` environment variable for OpenAI/Anthropic, or use `LLM_PROVIDER=ollama` for local models.
- **Data Quality Agent**: REST API available at http://localhost:8001. Monitors data quality autonomously and generates reports. See the [Data Quality Agent documentation](data_quality_agent/README.md) for usage examples. **Note**: Set `LLM_API_KEY` for OpenAI/Anthropic, or use `LLM_PROVIDER=ollama` for local models.
- **Predictive Maintenance Agent**: REST API available at http://localhost:8003. Analyzes production data to predict maintenance needs and creates work orders. See the [Predictive Maintenance Agent documentation](predictive_maintenance_agent/README.md) for usage examples. **Note**: Set `LLM_API_KEY` for OpenAI/Anthropic, or use `LLM_PROVIDER=ollama` for local models.
- **Ollama Service**: Local LLM service available at http://localhost:11434. Supports models like llama3.1, mistral, and others. To use Ollama, set `LLM_PROVIDER=ollama` and `LLM_MODEL=<model-name>` (e.g., `llama3.1`). Pull models with: `docker exec -it <container-name> ollama pull llama3.1`

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
- **Port 8000 (NLQ Service):** Another service might be using this port
- **Port 8001 (Data Quality Agent):** Another service might be using this port
- **Port 8003 (Predictive Maintenance Agent):** Another service might be using this port
- **Port 11434 (Ollama):** Another Ollama instance might be running locally

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
- **NLQ Service API:** http://localhost:8000 (see [NLQ Service README](nlq_service/README.md) for API documentation)
  - Interactive API docs: http://localhost:8000/docs
  - Health check: http://localhost:8000/health
- **Data Quality Agent API:** http://localhost:8001 (see [Data Quality Agent README](data_quality_agent/README.md) for API documentation)
  - Interactive API docs: http://localhost:8001/docs
  - Health check: http://localhost:8001/health
- **Predictive Maintenance Agent API:** http://localhost:8003 (see [Predictive Maintenance Agent README](predictive_maintenance_agent/README.md) for API documentation)
  - Interactive API docs: http://localhost:8003/docs
  - Health check: http://localhost:8003/health
- **Ollama Service:** http://localhost:11434 (local LLM server, OpenAI-compatible API)
  - Pull models: `docker exec -it dev-ollama ollama pull llama3.1`
  - List models: `docker exec -it dev-ollama ollama list`
  - Use with services: Set `LLM_PROVIDER=ollama` and `LLM_MODEL=<model-name>`


## Components

The following containers are used to provide the functionality described above:

- **dev-postgres-db:** Container based on PostgreSQL 15 Docker image, with an initialization script that creates the tables `production_data`, `wells_data` and `wellbores_data`. Includes a healthcheck to ensure the database is ready before other services start.

- **dev-luigi-python:** Container based on Python 3.11 Docker image with the Luigi module used to build pipelines of batch jobs. Includes dependencies: luigi, psycopg2-binary, pandas, sqlalchemy, lxml, and requests. The workflow runs once on container startup and then exits.

- **dev-grafana:** Container based on Grafana Docker image, with a dashboard called "Wells" provisioned via Dockerfile. Accessible at http://127.0.0.1:8080

- **dev-mcp-server:** Container running the Volve Wells MCP (Model Context Protocol) server, which exposes database query tools for LLM integration. Allows AI assistants like Claude to interact with the Volve wells database through natural language queries. Provides 8 tools for querying production data, well statistics, geographic searches, anomaly detection, and more. See the [MCP Server README](mcp_server/README.md) for detailed documentation and the [Learning Guide](mcp_server/LEARNING_GUIDE.md) for an in-depth explanation of MCP servers.

- **dev-nlq-service:** Container running the Natural Language Query (NLQ) REST API service. Converts natural language questions to SQL queries using LLMs (OpenAI, Anthropic, or Ollama), validates them for safety, and executes them against the database. Provides REST endpoints for easy integration with web applications, mobile apps, or other services. Features SQL validation, query explanations, and support for multiple LLM providers. See the [NLQ Service README](nlq_service/README.md) for detailed documentation and the [Learning Guide](nlq_service/LEARNING_GUIDE.md) for an in-depth explanation of NLQ systems.

- **dev-data-quality-agent:** Container running the Intelligent Data Quality Agent, an autonomous agentic AI system that monitors data quality, investigates issues using reasoning and tools, and generates comprehensive reports. Combines automated quality checks (missing values, duplicates, data freshness, value ranges, referential integrity) with LLM-powered root cause analysis and actionable recommendations. Demonstrates agentic AI patterns including tool use, autonomous reasoning, and multi-step problem solving. See the [Data Quality Agent README](data_quality_agent/README.md) for detailed documentation and the [Learning Guide](data_quality_agent/LEARNING_GUIDE.md) for an in-depth explanation of agentic AI systems.

- **dev-predictive-maintenance-agent:** Container running the Predictive Maintenance Agent, an advanced agentic AI system that analyzes production data patterns to predict maintenance needs and automatically creates maintenance work orders. Simulates SAP Plant Maintenance integration by storing work orders in a database table. Uses predictive models (production decline detection, anomaly detection, equipment age analysis) combined with LLM reasoning for strategic maintenance planning. Demonstrates advanced agentic AI patterns including predictive analytics, autonomous scheduling, and enterprise system integration simulation. See the [Predictive Maintenance Agent README](predictive_maintenance_agent/README.md) for detailed documentation and the [Learning Guide](predictive_maintenance_agent/LEARNING_GUIDE.md) for an in-depth explanation of predictive maintenance and advanced agentic AI systems.

- **dev-ollama:** Container running Ollama, a local LLM server that provides OpenAI-compatible API endpoints. Supports running open-source models like llama3.1, mistral, and others locally without requiring external API keys. Accessible at http://localhost:11434. The NLQ Service, Data Quality Agent, and Predictive Maintenance Agent can use Ollama by setting `LLM_PROVIDER=ollama` and `LLM_MODEL=<model-name>`. Models can be pulled using: `docker exec -it dev-ollama ollama pull llama3.1`. This enables privacy-sensitive deployments and reduces API costs for development and testing.






