# Docker deploy: daily research-report reader

The Compose file in the repo root runs two different commands from one image:

- `tradingagents` — interactive CLI (unchanged entrypoint)
- `report-reader` — `schedule_report_reader.py`, which runs `run_report_reader.py` on a cron schedule

The reader service is on the Compose profile `reader`. `docker compose up -d report-reader` starts it. A plain `docker compose up` still starts only the CLI.

Secrets stay in `.env`, which is gitignored. `.env.example` has empty placeholders. Do not commit API keys or tokens.

## What the timer does

`report-reader` stays up and sleeps until `REPORT_READER_SCHEDULE` matches, then runs `run_report_reader.py` in a child process. The default is `30 8 * * 1-5`: 08:30 Monday–Friday in `REPORT_READER_TZ` (default `Asia/Shanghai`). That timezone is also how the reader decides "today".

A failed read (no files yet, missing key) is logged. The scheduler keeps waiting for the next tick. `restart: unless-stopped` brings it back after a VM reboot once Docker itself is running.

Override the schedule or timezone in `.env` (uncomment the `REPORT_READER_*` lines) or in the shell before you run Compose. The five cron fields are minute, hour, day-of-month, month, and day-of-week (`0` or `7` is Sunday, `1-5` is Monday–Friday).

## Data the reader expects

Reports live at `{REPORT_READER_ROOT}/{YYYY-MM-DD}/{category}/*.txt`. The category folder names are:

- `宏观研究`
- `行业研报`
- `个股研报`
- `策略报告`
- `券商晨报`

Inside the container the root is `/data/report_data` (named volume `report_data`). Summaries and `contradictions.db` go to `/data/reports` (named volume `report_reader_output`).

The image also contains `docker/sample_report_data/2026-01-01/` with one placeholder `.txt` per category. That tree is for the smoke check only. It is not Spider output.

Spider data is not in this image. When that data is available, replace the `report_data` volume with a bind mount and leave the rest of the service as it is:

```yaml
volumes:
  - /path/to/report_data:/data/report_data:ro
  - report_reader_output:/data/reports
```

Until that mount has a date folder, a real run exits non-zero. The smoke check does not need it.

## Secrets

```bash
cp .env.example .env
```

Fill the LLM key for the provider you use (`OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, and the others already listed in `.env.example`). Select the provider with `TRADINGAGENTS_LLM_PROVIDER` when it should not be the default `openai`. Blank keys are enough for the smoke check. A real scheduled read needs a key and report files.

`.env` is listed in `.gitignore`. Keep it on the machine that runs Compose.

## Docker Desktop

Install Docker Desktop and start it. From the repo root:

```bash
cp .env.example .env
docker compose build report-reader
docker compose run --rm report-reader --smoke
```

Success:

- The command exits 0.
- Logs include a line that starts with `report reader smoke OK`.
- With an empty data volume the same line includes `source=bundled-sample`, `date=2026-01-01`, `categories=5`, and `loaded=5`.
- There is no API-key error and no call out to an LLM.

An empty date folder you mounted yourself is also enough. If `/data/report_data/{today}/` contains the category directories (even with no `.txt` files), the line says `source=input` instead of using the bundled sample.

Then start the timer:

```bash
docker compose up -d report-reader
docker compose ps
docker compose logs report-reader
```

Success:

- `report-reader` is `running`.
- Logs include `report reader scheduler started schedule='30 8 * * 1-5' tz=Asia/Shanghai`.
- Logs include `next report reader run at` and a timestamp at 08:30 with a `+08:00` offset, on a weekday.

That command starts `report-reader` only. Stop the timer with `docker compose stop report-reader`.

On the morning the timer fires before any Spider files are mounted, the child logs `No category folders found` or `Root directory not found` and exits non-zero. The scheduler process stays up. That is the expected gap until report files are mounted.

A one-shot real read, once a key and files are in place:

```bash
docker compose run --rm report-reader --once
```

Leave `REPORT_READER_SMOKE` unset in the `.env` used by `docker compose up -d report-reader`. The smoke command passes `--smoke` on `docker compose run`. Setting the variable makes the process exit after the check, and the restart policy starts it again.

`docker compose run report-reader` with no arguments runs the scheduler in the foreground. A bad `REPORT_READER_SCHEDULE` exits 1; Docker then restarts the container, and the log line is the parse error. Fix the expression and start it again.

## Cloud VM

Use the same Compose file. On a Debian or Ubuntu VM, install Docker Engine and the Compose plugin, and start Docker on boot:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

Clone the repo onto the VM, then run the same commands as on Desktop:

```bash
cp .env.example .env
# edit .env on the VM when you want a real read; leave keys blank for smoke
docker compose build report-reader
docker compose run --rm report-reader --smoke
docker compose up -d report-reader
docker compose logs report-reader
```

Success is the same pair of signals: smoke exits 0 with `report reader smoke OK`, and `docker compose ps` shows `report-reader` running with a next-run line in the logs.

`systemctl enable docker` plus `restart: unless-stopped` brings the timer back after a reboot. The container is the timer. A host crontab is a separate option: stop the long-running service first so the read does not run twice:

```bash
docker compose stop report-reader
# crontab: 30 8 * * 1-5  cd /path/to/repo && docker compose run --rm report-reader --once
```

## Later

Chinese daily summaries are what `run_report_reader.py` already writes when a real run succeeds. Spider data (including `D:\WORKS\all_data`), the web API, the Vue frontend, an @elonmusk summary, and group-chat push stay for a later change.
