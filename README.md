

# Fully Automated Uniware Business Reporting Crew

Automate Uniware report downloads, transform the CSVs into polished Excel summaries, email the results to Troveas stakeholders, and clean up leftover artifacts—all through a four-agent [CrewAI](https://www.crewai.com/) workflow designed for unattended execution.

## Table of Contents

- [Overview](#overview)
- [Highlights](#highlights)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Crew](#running-the-crew)
- [Agents, Tasks, and Tools](#agents-tasks-and-tools)
- [Helper Scripts](#helper-scripts)
- [Preparing for a Public Release](#preparing-for-a-public-release)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

## Overview

The crew orchestrates daily sales reporting by chaining four specialized agents. They authenticate against the Uniware API, download the latest sales export (daily + month-to-date), aggregate the data with Pandas, email the finished Excel workbook, and then delete any transient files. Although the automation targets Windows + PowerShell, it runs on any OS that can satisfy Python 3.10–3.13 and the required APIs.

## Highlights

- **End-to-end automation**: download → analyze → email → cleanup with shared memory between agents.
- **Tenant-aware Uniware tooling**: password-grant auth, export polling, CSV download, and resilient error capture for the `priyankdesigns` tenant.
- **Data hygiene**: eliminates cancelled/unfulfillable orders, normalizes channels, and appends summary totals in `Troveas_Report_<date>.xlsx`.
- **Email fan-out**: reads primary/CC recipients from `knowledge/user_preference.txt`, attaches the newest Excel artifact, and delivers via SMTP (defaults to Gmail).
- **Operational helpers**: `record_api_error.py` traps failing payloads for Uniware support, while `debug_encoding.py` reveals encoding issues that can break SMTP auth.

## Architecture

### Repository Map

```
.
├── agents.py                 # Agent factory wiring LLM + specialized tools
├── crew.py                   # Crew assembly and sequential task orchestration
├── tasks.py                  # Task templates that reference config/tasks.yaml
├── tools/custom_tool.py      # Uniware API, analysis, email, and cleanup tools
├── config/
│   ├── agents.yaml           # Roles, goals, and backstories for each agent
│   └── tasks.yaml            # Natural-language instructions & outputs
├── knowledge/user_preference.txt  # Primary recipient (line 1) + CC addresses
├── main.py / run.py          # Entry points (`python run.py` or `crewai run`)
├── record_api_error.py       # Script to reproduce/report Uniware 500 errors
├── debug_encoding.py         # Utility to inspect credential/filename encoding
├── requirements.txt          # Minimal pip requirements
├── pyproject.toml            # Poetry metadata and dependency pins
└── uv.lock                   # uv resolver lockfile (opt-in dependency manager)
```

### Execution Flow

1. `ReportingCrew` instantiates the four agents from `agents.py` using the YAML configs.
2. Each agent receives a task definition from `config/tasks.yaml`, enforcing consistent prompts.
3. `Crew.kickoff()` executes sequentially, sharing context and files between agents.
4. Logs trace Uniware export polling, Pandas aggregation, SMTP delivery, and cleanup.

## Prerequisites

- Python 3.10–3.13 (match `pyproject.toml`).
- An OpenAI (or Azure OpenAI) API key compatible with `langchain-openai`.
- Valid Uniware API credentials for the `priyankdesigns` tenant.
- SMTP credentials for the mailbox that will send the report.
- Windows PowerShell, Command Prompt, or any POSIX shell.

## Setup

1. **Clone the repo**.
2. **Create and activate** a virtual environment (recommended):
   - Windows: `python -m venv venv && venv\Scripts\activate`
   - POSIX: `python -m venv venv && source venv/bin/activate`
3. **Install dependencies** using one of the supported managers:
   - `pip install -r requirements.txt`
   - `poetry install`
   - `uv sync`
4. **Review the repo** for sample config files and update them with your tenant/mailbox details.

## Configuration

Create a `.env` file (already gitignored) with the required secrets:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required by `ChatOpenAI` for every agent run. |
| `MODEL` (optional) | Override the default `gpt-4o` with another alias. |
| `UNIWARE_USERNAME`, `UNIWARE_PASSWORD` | Used by `UniwareAPITools` via password grant. |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | SMTP credentials for the sending mailbox. |

> Keep `.env` ASCII-only; `debug_encoding.py` highlights hidden characters that can corrupt credentials.

Recipient routing lives in `knowledge/user_preference.txt`:

- Line 1 = `To` recipient.
- Lines 2+ = CC list (comma, semicolon, or newline delimited).
- For public repos, commit only placeholders (e.g., `primary@example.com`) and keep real addresses outside git.

## Running the Crew

- Quick start: `python run.py`
- Poetry: `poetry run python run.py`
- CrewAI CLI: `crewai run`

Windows Task Scheduler or cron can invoke the same commands for unattended execution. Logs (stdout/stderr) show Uniware polling status, Pandas summaries, SMTP responses, and cleanup confirmations.

## Agents, Tasks, and Tools

- **Downloader (`Uniware API Specialist`)** – `UniwareAPITools` authenticates via password grant, creates a “Sale Orders” export for yesterday + month-to-date, polls for completion, and downloads the CSV.
- **Analyst (`Data Analyst`)** – `DataAnalysisTools` locates the newest CSV, filters cancelled/returned orders, groups by channel, appends totals, and writes `Troveas_Report_<date>.xlsx`.
- **Communicator (`Communications Officer`)** – `EmailTools` reads the recipient file, attaches the latest Excel workbook, and sends it with subject `Troveas Daily Business Report`. Default SMTP host: `smtp.gmail.com:587`.
- **Cleanup (`File Cleanup Specialist`)** – `CleanupTools` removes any `uniware_sales_*.csv` and `Troveas_Report_*.xlsx` files once email delivery succeeds.

## Helper Scripts

- `record_api_error.py` – Replays the Uniware auth + export process with verbose logging so you can capture payloads that return HTTP 500s for vendor support.
- `debug_encoding.py` – Shows byte-level representations of environment variables and filenames to uncover hidden characters (e.g., non-breaking spaces) that often break SMTP logins on Windows.

## Preparing for a Public Release

- **Scrub secrets**: never commit `.env`, access tokens, or production mailbox credentials. Replace `knowledge/user_preference.txt` with placeholders or a `.sample` file before pushing.
- **Document required steps**: ensure this README plus inline comments explain how to recreate the environment without private context.
- **Validate dependency manifests**: confirm `requirements.txt`, `pyproject.toml`, and `uv.lock` are in sync (`pip list --outdated`, `poetry lock`, or `uv pip compile` as needed).
- **Run a dry run**: execute `python run.py` with dummy credentials to confirm imports, config loading, and task wiring succeed (expect Uniware auth to fail when using placeholders, but the crew should still initialize cleanly).
- **Check licensing**: MIT License (included) is appropriate for public distribution; update `LICENSE` if you need a different grant.
- **Optional polish**: add badges/screenshots, create an `examples/` folder with sanitized sample CSV/Excel files, and open-source issues/PR templates for community contributions.

## Troubleshooting

- **Authentication failures** – Confirm `.env` paths and strip hidden characters (Word often inserts non-breaking spaces). `record_api_error.py` prints masked credential lengths to help debug.
- **No CSV downloaded** – Verify `UNIWARE_*` credentials and the tenant slug (`priyankdesigns`). The downloader polls up to 10 times (≈100 seconds); increase the retry loop if your exports are slower.
- **Pandas errors** – Uniware occasionally changes column headers. Update the normalization logic in `DataAnalysisTools` whenever the schema shifts.
- **Email not sent** – Ensure the SMTP account allows programmatic access. For Gmail with 2FA, create an App Password. Logs show the exact `smtplib` exception.
- **Files not removed** – Run the crew inside a directory with delete permissions. Cleanup only triggers after a successful email send, so earlier failures leave artifacts for inspection.

## Roadmap

- Add automated tests (mocking Uniware responses + Pandas transformations).
- Parameterize tenant/facility instead of hardcoding `priyankdesigns`.
- Externalize SMTP host/port into config to support multiple providers per environment.

## License

Released under the [MIT License](LICENSE). Feel free to adapt the configs, tasks, and helper scripts for other reporting cadences or downstream systems.
