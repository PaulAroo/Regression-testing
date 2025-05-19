# Regression tests for HPC clusters

🚧 WIP - Work In Progress 👨🏽‍💻

- [ ] Set references for each test
- [ ] FIX: INCORRECT BINDINGS (OsuSameSocketDifferentNuma)
- [ ] Merge tests into a single script? (use a parameter for the different compilation options)

see [project description](./project_description.md)

## Running Tests

1. Login to ulhpc cluster
```sh
ssh iris-cluster
```
2. Moves files to the cluster (clone repo, push files, or whichever other way you prefer). Further instructions assume you are in the root directory of the project on the hpc cluster.
```sh
git clone git@github.com:PaulAroo/Regression-testing.git
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