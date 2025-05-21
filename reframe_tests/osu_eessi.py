
import reframe as rfm
import reframe.utility.sanity as sn

# ============================================================================
#  Part 1: Compilation Test for OSU Micro-Benchmarks using EESSI
# ============================================================================

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
    # benchmark_info: tuple(executable_name_suffix, metric_name)
    benchmark_info = parameter([
        ('osu_bw', 'bandwidth'),
        ('osu_latency', 'latency')
    ], fmt=lambda x: x[0], loggable=True) # Log only the executable name suffix

    @run_before('run')
    def set_executable_path(self):
        '''Load required modules and set the full path to the executable'''

        self.prerun_cmds += [
            'module load EESSI',
            'module load OSU-Micro-Benchmarks/7.2-gompi-2023b'
        ]

        exec_name = self.benchmark_info[0]
        self.executable = exec_name

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

        self.executable_opts = ['-m', f'{self.message_size}:{self.message_size}', '-x', '100', '-i', '1000']
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
class EESSIOsuSameNumaNode(OsuBwLatencyBenchmarkBase):
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
    @run_before('performance')
    def set_references(self):
      # This method overrides the default set in the base class
      metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
      references = {
        'latency': {
          'aion:batch': {'latency': (2.3, -0.1, 0.5, 'us')},
          'iris:batch': {'latency': (5.5, -0.1, 0.5, 'us')},
        },
        'bandwidth': {
          'aion:batch': {'bandwidth': (12000.0, -0.1, None, 'MB/s')},
          'iris:batch': {'bandwidth': (15000.0, -0.1, None, 'MB/s')},
        }
      }
      self.reference = references[metric]

# ============================================================================
# Test Case: Same Physical Socket, Different NUMA Nodes (Targeted for Aion)
# ============================================================================
@rfm.simple_test
class EESSIOsuSameSocketDifferentNuma(OsuBwLatencyBenchmarkBase):
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

    # --- Set specific reference values ---
    @run_before('performance')
    def set_references(self):
      # This method overrides the default set in the base class
      metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
      references = {
        'latency': {
          'aion:batch': {'latency': (3.8, -0.1, 0.5, 'us')},
        },
        'bandwidth': {
          'aion:batch': {'bandwidth': (12000.0, -0.1, None, 'MB/s')},
        }
      }
      self.reference = references[metric]

# ============================================================================
# Test Case: Same Compute Node, Different Physical Sockets
# ============================================================================

@rfm.simple_test
class EESSIOsuDifferentSockets(OsuBwLatencyBenchmarkBase):
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

    # --- Set specific reference values ---
    @run_before('performance')
    def set_references(self):
      # This method overrides the default set in the base class
      metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
      references = {
        'latency': {
          'aion:batch': {'latency': (3.8, -0.1, 0.5, 'us')},
          'iris:batch': {'latency': (8, -0.1, 0.5, 'us')},
        },
        'bandwidth': {
          'aion:batch': {'bandwidth': (12000.0, -0.1, None, 'MB/s')},
          'iris:batch': {'bandwidth': (15000.0, -0.1, None, 'MB/s')},
        }
      }
      self.reference = references[metric]

# ============================================================================
# Test Case: 2 processes are running on different nodes.
# ============================================================================

@rfm.simple_test
class EESSIOsuDifferentNodes(OsuBwLatencyBenchmarkBase):
    descr = 'OSU Pt2Pt: Same Node, Different Sockets'

    num_tasks_per_node = 1

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):

        self.job.launcher.options += [
            '--nodes=2'
        ]

    # --- Set specific reference values ---
    @run_before('performance')
    def set_references(self):
      # This method overrides the default set in the base class
      metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
      references = {
        'latency': {
          'aion:batch': {'latency': (4.0, -0.1, 0.5, 'us')},
          'iris:batch': {'latency': (10, -0.1, 0.5, 'us')},
        },
        'bandwidth': {
          'aion:batch': {'bandwidth': (12000.0, -0.1, None, 'MB/s')},
          'iris:batch': {'bandwidth': (8000.0, -0.1, None, 'MB/s')},
        }
      }
      self.reference = references[metric]