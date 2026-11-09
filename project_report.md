# EF101-P04: Computer Hardware Stress Testing and Resource Analysis

**Group Size:** 3 students

**Submission Date:** 9 November 2026

**Group Members:** \[Insert Name 1\], \[Insert Name 2\], \[Insert Name 3\]

## 1. Mandatory Experimental Setup

### Test-Machine Specifications

* **Laptop/Desktop Form Factor:** \[e.g., Laptop\]

* **Operating System:** \[e.g., Windows 11 Home\]

* **CPU Model:** \[e.g., Intel Core i7-1165G7\]

* **Core/Thread Count:** \[e.g., 4 Cores / 8 Threads\]

* **Installed RAM:** \[e.g., 16 GB DDR4\]

* **RAM Capacity used by OS:** \[e.g., 11.8 GB usable physical RAM\]

* **GPU Model:** Intel Iris Xe (Integrated)

* **Storage Type:** Kingston SSD \[Insert exact model if known\]

### Tools Used

* **Monitoring Tools:** HWiNFO64 (used to automatically log CPU/RAM/GPU utilization, temperatures, and disk throughput to a CSV file every \[Insert interval, e.g., 2\] seconds) and PresentMon (for framerate).

* **Stress-Testing Tools:** \[Insert the tools you used here, e.g., Cinebench for CPU, CrystalDiskMark for Storage, FurMark for GPU\].

## 2. Required Analysis

### A. Idle vs. Stress Comparisons

*(See the `images/` folder for all generated graphs)*


As shown in the graph above, we established an idle baseline for each component before applying the stress test. For example, the CPU rested at 35% usage before hitting 100% under stress, and the GPU rested at 4% before hitting 100%.

### B. Hardware Bottlenecks


Based on our collected data, the limiting resource (bottleneck) for each workload was:

* **CPU Test:** The CPU (100% usage).

* **Storage Test:** The SSD (100% active time).

* **GPU Test:** The GPU (100% usage).

* **Mixed Workload (Tabs + Video + Zipping):** The SSD was the primary bottleneck at 86% average active time (frequently spiking to 100%), followed by RAM at 77% and CPU at 72%.

### C. Utilization vs. Performance


Our data highlights a critical difference between utilization and performance. During the CPU test, CPU *usage* was pegged at 100% (meaning it was constantly busy). However, the actual *utility* (work done relative to base speed) fluctuated around 49%. This shows that a component can be 100% utilized, but if it is running hot and at a slowed clock speed, it is not performing at 100% of its maximum capacity.

### D. RAM Pressure and Virtual Memory


During our mixed workload, physical RAM reached roughly 80% capacity (\~9.5 GB used out of 11.8 GB). As RAM pressure increased, the operating system utilized virtual memory to prevent crashes, evidenced by the page file on the SSD growing from 1.77 GB to 2.02 GB. The OS moves lower-priority background data from physical RAM to this slower SSD page file to free up space for active tasks.

### E. Clock Changes, Thermal Throttling, and Power Limits

* **CPU:** During the CPU stress test, the package temperature sat at \~90°C. Upon reaching 100% load, thermal throttling engaged immediately, causing the clock speed to drop from \~3000 MHz to between 1000-2000 MHz (well below the 2800 MHz base speed).

* **GPU:** During the GPU stress test, temperatures reached the low 90s (°C). This sustained load caused the clock speed to throttle heavily, mostly hovering around 600 MHz and causing the desktop frame rate to plummet to \~2 FPS.

### F. Comparing Two Different Stress Tasks

When comparing the CPU stress test and the Storage stress test, the system behaves very differently. The CPU test relies entirely on processing power, generating massive heat and triggering thermal throttling, but requires very little data transfer from the drive. Conversely, the Storage test requires moving data at up to 692 MB/s, pinning the SSD's active time at 100%, but only required 65% RAM usage and did not heavily tax the CPU's compute capabilities.

### G. Why a System Feels Slow Below 100% CPU

A system can feel incredibly sluggish even if the CPU is not at 100%. This is usually due to a storage bottleneck. As seen in our storage test, the SSD active time was at 100% even when moving only 1-20 MB/s of small files. When the drive is 100% busy fielding a queue of requests, the CPU has to wait for data to arrive, making the entire user interface feel unresponsive despite the CPU having plenty of available processing power.

## 3. Submission Evidence & Limitations

* **Test Durations:** Isolated tests were run for roughly \[Insert Duration, e.g., 60 to 120\] seconds each, and the mixed workload was logged for over 140 seconds.

* **Raw Data:** All raw logs and cleaned CSV data can be found in the `/data/` directory of this repository.

* **Limitations:** \[Insert a brief sentence or two here about any limitations you faced. For example: "Because the test laptop was on battery power and already running warm (\~90°C), thermal throttling occurred almost instantly, which prevented us from capturing peak non-throttled performance data."\]