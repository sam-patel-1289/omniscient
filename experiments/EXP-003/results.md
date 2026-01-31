# EXP-003 Results: Concurrency Stress Test

## Overview
We implemented two counters:
1.  **VulnerableStore**: Reads state, waits (simulating work), then writes state. No locking.
2.  **OptimisticStore**: Reads state (with version), waits, then attempts to write using `fcntl` based atomic check-and-set (verifying version matches). Clients retry on `VersionConflict`.

We ran a concurrency test with **50 threads** attempting to increment the counter simultaneously.

## Findings

### 1. Vulnerable Store
*   **Target Count**: 50
*   **Actual Count**: 1
*   **Observation**: Massive data loss. Almost all threads read the initial value `0` during the simulated processing window, and overwrote each other's work, resulting in a final count of `1`. This confirms the "lost update" anomaly.

### 2. Optimistic Store
*   **Target Count**: 50
*   **Actual Count**: 50
*   **Total Retries**: ~679
*   **Observation**: Data integrity was strictly preserved. While contention was high (causing many retries), every successful increment was based on the latest version of the data. No updates were lost.

## Conclusion
Optimistic locking is an effective strategy for preventing lost updates in concurrent environments, forcing clients to handle contention explicitly (via retries) rather than failing silently or corrupting data.
