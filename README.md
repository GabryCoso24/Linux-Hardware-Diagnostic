# Linux Hardware Diagnostic

A lightweight Linux hardware diagnostic CLI for checking CPU and disk health.

## Features

- CPU diagnostic test
  - Core count validation
  - CPU usage thresholds
  - Per-core activity checks
  - Frequency anomaly detection
  - Temperature threshold checks (when available)
- Disk diagnostic test
  - Physical disk discovery via `lsblk`
  - Physical disk count
  - Disk usage status checks

## Requirements

- Linux
- Python 3.8+
- `lsblk` available in PATH

Python dependencies are listed in `requirements.txt`.

## Setup

### Option 1: Automatic setup (recommended)

```bash
python3 env_builder.py
source venv/bin/activate
```

### Option 2: Manual setup

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

```bash
python3 cli.py
```

The CLI runs CPU and disk tests and prints:

- test status
- test message
- collected diagnostic data

## Project Structure

- `cli.py`: CLI entry point
- `runner.py`: Test runners and status mapping
- `core/`: System information providers
  - `cpu_info.py`
  - `disks_info.py`
- `tests/`: Diagnostic test logic
  - `test_base.py`
  - `cpu_test.py`
  - `disks_test.py`

## Notes

- Some metrics (for example temperature sensors) depend on hardware and kernel support.
- Disk checks are currently based on usage metrics for detected physical disks.
