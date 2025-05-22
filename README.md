# Regression tests for UNILU HPC clusters

The objective of this project is the creation of ReFrame regression tests that measure intranode and internode latency and bandwidth. The tests will use OSU Micro-Benchmarks, a set of utilities designed to test the communication performance of a cluster for various parallel programming frameworks. This project will focus on testing MPI communication primitives.

## Test design

The 2 main tests in OSU Micro-Benchmarks that evaluate communication latency and bandwidth are:

*   `osu_latency`, and
*   `osu_bw`

respectively. By default, the benchmarks evaluate the performance of the system for a set of messages of different length, as the length of the message affects both the latency and the throughput of the communication.

The following cases can be distinguished:

*   both processes are running on the same NUMA node,
*   both processes are running on the same physical socket but different NUMA nodes,
*   both processes are running on the same compute node but different sockets, and
*   the 2 processes are running on different nodes.

Extract more information about the system architecture by using the `system/hwloc` module.

[see full project description here](./project_description.md)

## Running Tests

1. Login to ulhpc cluster
```sh
ssh iris-cluster
```
2. Moves files to the cluster (clone repo, push files, or whichever other way you prefer). Further instructions assume you are in the root directory of the project on the hpc cluster.
```sh
git clone git@github.com:PaulAroo/Regression-testing.git
```
```sh
cd Regression-testing
```

3. Get on a compute node. Use `si` or `salloc` with the appropriate options.
```sh
si
```

4. Load the reframe module
```sh
module load devel/ReFrame/4.7.4-GCCcore-13.2.0
```
- if that module is not found, search for what is available (`module avail '/reframe/'`) and load it

5. Run the test
```sh
reframe --config-file config/ulhpc.py --checkpath reframe_tests/osu_build_source.py --run --performance-report
```
```sh
reframe --config-file config/ulhpc.py --checkpath reframe_tests/osu_build_easybuild.py --run --performance-report
```
```sh
reframe --config-file config/ulhpc.py --checkpath reframe_tests/osu_eessi.py --run --performance-report
```

### Relevant docs
- [EESSI-OSU-Micro-Benchmarks](https://www.eessi.io/docs/available_software/detail/OSU-Micro-Benchmarks/)
- [Reframe - (Testing Framework)](https://reframe-hpc.readthedocs.io/en/stable/index.html)

### Performance Report (sample)
![performance report sample](/sample_perf_report.png)