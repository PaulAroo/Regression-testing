
import reframe as rfm
import reframe.utility.sanity as sn
import os

# ============================================================================
#  Part 1: Compilation Test for OSU Micro-Benchmarks from Source
# ============================================================================

class OsuBuildSource(rfm.CompileOnlyRegressionTest):
    '''Fixture for building the OSU benchmarks'''

    descr = 'Build OSU Micro-Benchmarks 7.2 from source using foss/2023b'

    # --- Build configuration ---
    build_system = 'Autotools'
    build_prefix = variable(str)
    version = variable(str, value='7.2')

    @run_before('compile')
    def prepare_build(self):
      osu_file_name = f'osu-micro-benchmarks-{self.version}.tar.gz'
      self.build_prefix = osu_file_name[:-7]
      self.prebuild_cmds += [
        f'curl -LJO http://mvapich.cse.ohio-state.edu/download/mvapich/{osu_file_name}',
        f'tar xzf {osu_file_name}',
        f'cd {self.build_prefix}'
      ]
      self.build_system.max_concurrency = 8

class OsuBwLatencyBenchmarkBase(rfm.RunOnlyRegressionTest):
    '''Base class for OSU Point-to-Point benchmark tests (osu_latency, osu_bw).'''

    # message_size will be set based on the specific benchmark (latency/bw)
    message_size = variable(int, loggable=True)

    valid_systems = ['*']
    valid_prog_environs = ['*']
    num_tasks = 2
    num_tasks_per_node = 2
    num_cpus_per_task = 1
    exclusive_access = True

    # --- Parameter to select the specific pt2pt benchmark ---
    benchmark_info = parameter([
        ('osu_bw', 'bandwidth'),
        ('osu_latency', 'latency')
    ], fmt=lambda x: x[0], loggable=True) # Log only the executable name suffix

    # --- Fixture Dependency ---
    osu_binaries = fixture(OsuBuildSource, scope='environment')

    @run_before('run')
    def set_executable_path(self):
        '''Sets the full path to the executable using the build fixture.'''
        exec_name = self.benchmark_info[0]
        self.executable = os.path.join(self.osu_binaries.stagedir,
                                       self.osu_binaries.build_prefix, 'c',
                                       'mpi', 'pt2pt', 'standard', exec_name)

        # export relevant OMPI MCA vars
        self.env_vars = {
            'OMPI_MCA_hwloc_base_report_bindings': '1'
        }

    @run_before('setup')
    def setup_executable_options_and_perf(self):
        '''Sets executable options and performance variables based on benchmark type.'''
        exec_name, bench_metric = self.benchmark_info

        if bench_metric == 'latency':
            self.message_size = 8192
            unit = 'us'
        elif bench_metric == 'bandwidth':
            self.message_size = 1048576
            unit = 'MB/s'
        else:
            raise ValueError(f'Unknown benchmark metric: {bench_metric}')

        self.executable_opts = ['-m', f'{self.message_size}:{self.message_size}', '-x', '10', '-i', '100']
        self.reference_unit = unit

        metric_regex = rf'^{self.message_size}\s+(?P<metric_val>\S+)'
        self.perf_variables = {
            # The key is the metric name ('latency' or 'bandwidth')
            bench_metric: sn.make_performance_function(
                # The first argument is the extraction logic
                sn.extractsingle(metric_regex, self.stdout, 'metric_val', float),
                unit=self.reference_unit
            )
        }

    @sanity_function
    def validate_test(self):
        '''Basic sanity check: Look for the output line of the tested message size.'''
        return sn.assert_found(rf'^{self.message_size}\s+\S+', self.stdout)

    # Default reference dictionary - subclasses should override or extend this
    @run_before('performance')
    def set_default_reference(self):
        if not self.reference: # Only set if not already set by subclass
            metric = self.benchmark_info[1]
            self.reference = {
                '*': {
                    metric: (0, None, None, self.reference_unit)
                }
            }

@rfm.simple_test
class OsuSameNumaNode(OsuBwLatencyBenchmarkBase):
    descr = 'OSU Point-to-Point Benchmark Run'

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):

      # These SLURM options are passed to srun
      self.job.launcher.options += [
          '--cpu-bind=verbose,cores',
          '--mem-bind=local',
          '--distribution=block:block'
      ]

    # --- Set specific reference values ---
    # @run_before('performance')
    # def set_references(self):
    #   # This method overrides the default set in the base class
    #   metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
    #   references = {
    #     'latency': {
    #       '*': {'latency': (1.8, -0.1, 0.5, 'us')} # Placeholder for latency
    #     },
    #     'bandwidth': {
    #       '*': {'bandwidth': (15000.0, -0.1, None, 'MB/s')} # Placeholder for bandwidth
    #     }
    #   }
    #   self.reference = references[metric]



# ============================================================================
# Test Case: Same Physical Socket, Different NUMA Nodes (Targeted for Aion)
# ============================================================================
@rfm.simple_test
class OsuSameSocketDifferentNuma(OsuBwLatencyBenchmarkBase):
    descr = 'OSU Pt2Pt: Same Socket, Different NUMA Nodes (Aion Specific)'

    # --- Target only Aion for this specific test ---
    valid_systems = ['aion:batch']

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):
        self.job.launcher.options += [
            '--cpu-bind=verbose,map_cpu:0,16',
            '--mem-bind=local',
        ]

    # @run_before('performance')
    # def set_references(self):
    #     metric = self.benchmark_info[1]
    #     if metric == 'latency':
    #         self.reference = {'*': {'latency': (1.5, -0.1, 0.5, 'us')}}
    #     elif metric == 'bandwidth':
    #         self.reference = {'*': {'bandwidth': (14000.0, -0.1, None, 'MB/s')}}

# ============================================================================
# Test Case: Same Compute Node, Different Physical Sockets
# ============================================================================

@rfm.simple_test
class OsuDifferentSockets(OsuBwLatencyBenchmarkBase):
    descr = 'OSU Pt2Pt: Same Node, Different Sockets'

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):
         # These SLURM options are passed to srun
        self.job.launcher.options += [
            '--ntasks-per-socket=1',
            '--cpu-bind=verbose,cores',
            '--mem-bind=local',
            '--distribution=cyclic:cyclic'
        ]

# ============================================================================
# Test Case: 2 processes are running on different nodes.
# ============================================================================

@rfm.simple_test
class OsuDifferentNodes(OsuBwLatencyBenchmarkBase):
    descr = 'OSU Pt2Pt: Same Node, Different Sockets'

    num_tasks_per_node = 1

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):

        self.job.launcher.options += [
            '--nodes=2'
        ]
