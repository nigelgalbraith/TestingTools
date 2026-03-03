# TestingTools

A small collection of terminal-based testing utilities built around a **shared, reusable tool loader** and a **pipeline-style state machine**.

The main goal:
- keep tools modular
- keep logic reusable
- keep execution predictable (pre → plan → confirm → exec)
- avoid “one-off scripts” that turn into spaghetti

---

## What’s included

### WiFiScanner
A Wi-Fi utility that can:
- list wireless interfaces
- scan for nearby networks
- show detailed information for a selected network (BSS details)

**Config:** `config/WiFiConfig.json`
**Constants:** `constants/WiFiConstants.py`
**Docs:** `doc/WiFiDoc.json`

#### Notes
Some USB Wi-Fi adapters can intermittently return:
- `Device or resource busy (-16)` from `iw scan`

This is usually a transient driver / supplicant / NetworkManager contention issue.
The tool still works fine — it may just require retrying a scan occasionally on that adapter.

A future improvement may add a small “busy check / retry backoff” step before scanning.

---

### NetworkScanner
A network utility that can:
- list network interfaces
- analyze a selected interface
- show ARP neighbors (from `ip neigh`)
- run a TCP port scan against a chosen host

**Config:** `config/NetworkConfig.json`
**Constants:** `constants/NetworkConstants.py`
**Docs:** `doc/NetworkDoc.json`

---

## How it works (architecture)

Each tool is defined mainly by a **constants module**:
- config path + schema validation
- dependency list
- menu actions
- pipeline states
- reusable step blocks for `pre` and `exec`

The loader/state machine handles:
1. dependency check/install
2. config loading + validation
3. tool status summary
4. action menu selection
5. pipeline execution:
   - **pre-phase** steps (selection / preparation / data gathering)
   - optional plan display
   - confirmation prompt
   - **exec-phase** steps

---

## Run

### Interactive selection
```bash
python3 tool_loader.py
