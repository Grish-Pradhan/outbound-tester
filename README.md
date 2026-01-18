# Outbound Connection Tester

## Overview

Outbound Connection Tester is a Python-based GUI tool that evaluates outbound TCP connectivity from a host to a specified target across multiple ports. It is designed for **network security analysis**, **firewall egress testing**, and **educational use in ethical hacking environments**.

The tool attempts TCP connections and classifies results as **open**, **closed**, **filtered**, or **error**, while measuring connection latency.

---

## Features

* GUI built with **Tkinter**
* Multi-port outbound TCP testing
* Configurable timeout
* Real-time progress tracking
* Color-coded, structured results
* Threaded execution (non-blocking UI)
* Clear test summary with statistics
* Safe-use warning integrated into UI

---

## How It Works (First Principles)

1. For each port, a TCP socket is created.
2. `connect_ex()` is used to attempt a connection.
3. Result codes are mapped to network states:

   * `0` → Open (connection successful)
   * Non-zero → Closed (connection refused)
   * Timeout → Filtered (likely firewall)
   * DNS/socket errors → Error
4. Elapsed time is measured per port in milliseconds.
5. Execution runs in a separate thread to avoid GUI freezing.

No packet crafting, no raw sockets, no privilege escalation—pure outbound TCP connect logic.

---

## Requirements

* Python **3.8+**
* Standard Library only:

  * `tkinter`
  * `socket`
  * `threading`
  * `datetime`
  * `time`

No third-party dependencies.

---

## Installation

```bash
git clone https://github.com/Grish-Pradhan/outbound-connection-tester.git
cd outbound-connection-tester
python outbound_tester.py
```

---

## Usage

1. Enter a **target hostname or IP**
2. Enter **comma-separated ports**
3. Set a **timeout value (seconds)**
4. Click **Start Test**
5. View real-time results and final summary

---

## Output Legend

| Symbol | Meaning  |
| ------ | -------- |
| ✓      | Open     |
| ✗      | Closed   |
| ◐      | Filtered |
| !      | Error    |

---

## Example Use Cases

* Firewall egress rule validation
* Network segmentation testing
* Security lab demonstrations
* Blue-team visibility testing
* Ethical hacking coursework

---

## Security & Legal Notice

This tool performs **active network connections**.

**Only test systems you own or have explicit permission to test.**
Unauthorized scanning may violate laws or policies.

---

## Limitations

* TCP only (no UDP)
* Sequential scanning (no parallel sockets)
* No service fingerprinting
* No encryption or authentication (by design)

---


## License

MIT License

---

## Author

Developed for **educational and defensive security purposes**.


