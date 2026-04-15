# Linux Hardware Diagnostic

A lightweight Linux hardware diagnostic tool with both CLI and TUI interfaces.

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
- GPU diagnostic test
  - GPU discovery via `lspci`
  - Vendor detection (NVIDIA, AMD, Intel)
- Network diagnostic test
  - Active interface checks
  - Packet errors and drop counters
- USB diagnostic test
  - USB device discovery via `lsusb` (with `/sys` fallback)
- Realtime resource monitor
  - Live CPU, RAM, swap, disk, and network throughput
  - Top processes by CPU and memory (task-manager style)
- Interactive terminal UI (TUI)
  - Menu-driven test execution
  - Live result panel
  - Built-in realtime monitor view
  - Report export

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
python3 cli.py --help
```

Examples:

```bash
# Single tests
python3 cli.py --cpu
python3 cli.py --disks
python3 cli.py --gpu
python3 cli.py --network
python3 cli.py --usb

# All tests
python3 cli.py --all

# Save report (auto timestamp)
python3 cli.py --report

# Save report (custom base name)
python3 cli.py --report my_report.json

# Launch interactive TUI
python3 cli.py --tui

# Launch realtime monitor directly
python3 cli.py --monitor
```

The CLI prints:

- test status
- test message
- collected diagnostic data

## Project Structure

- `cli.py`: CLI entry point
- `runner.py`: Test runners and status mapping
- `core/`: System information providers
  - `cpu_info.py`
  - `disks_info.py`
  - `gpu_info.py`
  - `system_monitor.py`
  - `report.py`
- `tests/`: Diagnostic test logic
  - `test_base.py`
  - `cpu_test.py`
  - `disks_test.py`
  - `gpu_test.py`
  - `network_test.py`
  - `usb_test.py`
- `tui.py`: Interactive curses TUI

## Notes

- Some metrics (for example temperature sensors) depend on hardware and kernel support.
- Disk checks are currently based on usage metrics for detected physical disks.
