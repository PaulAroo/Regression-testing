

# TODO:
# - configure warmup runs
# - set references for each test
# - FIX: INCORRECT BINDINGS (OsuDifferentSockets, OsuSameSocketDifferentNuma)


import reframe as rfm
import reframe.utility.sanity as sn
import os

# ============================================================================
#  Part 1: Compilation Test for OSU Micro-Benchmarks from Source
# ============================================================================

_THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))

class OsuBuildEasyBuild(rfm.CompileOnlyRegressionTest):
    '''Fixture for building the OSU benchmarks'''

    descr = 'Build OSU Micro-Benchmarks 7.2 via EasyBuild using foss/2023b'

    valid_systems = ['*']
    valid_prog_environs = ['*']

    # --- Build configuration ---
    build_system = 'EasyBuild'

    def __init__(self):
        super().__init__()
        self.test_definition_dir = _THIS_FILE_DIR

    @run_before('compile')
    def setup_build_system(self):
        self.prebuild_cmds += [
          f'cp {self.test_definition_dir}/OSU-Micro-Benchmarks-7.2-foss-2023b.eb {self.stagedir}/',
        ]
        self.build_system.easyconfigs = ['OSU-Micro-Benchmarks-7.2-foss-2023b.eb']
        self.build_system.options = ['-f --detect-loaded-modules=purge']

    @sanity_function
    def validate_easybuild_build(self):
        # Basic check that EasyBuild finished
        return sn.assert_found(r'Build succeeded for 1 out of 1', self.stdout)
    
    @property
    def generated_modules(self):
        return self.build_system.generated_modules

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

    # --- Fixture Dependency ---
    osu_bins = fixture(OsuBuildEasyBuild, scope='environment')

    @run_before('run')
    def set_executable_path(self):
        '''Sets the full path to the executable using the build fixture.'''
        exec_name = self.benchmark_info[0]
        self.modules = self.osu_bins.generated_modules
        self.executable = exec_name

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

      # Optional: export relevant OMPI MCA vars
      self.env_vars = {
          # 'OMPI_MCA_rmaps_base_mapping_policy': 'numa',
          # 'OMPI_MCA_hwloc_base_binding_policy': 'core',
          # 'OMPI_MCA_hwloc_base_mem_bind_policy': 'bind',
          'OMPI_MCA_hwloc_base_report_bindings': '1'
      }

#     # --- Set specific reference values ---
#     # @run_before('performance')
#     # def set_references(self):
#     #   # This method overrides the default set in the base class
#     #   metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
#     #   references = {
#     #     'latency': {
#     #       '*': {'latency': (1.8, -0.1, 0.5, 'us')} # Placeholder for latency
#     #     },
#     #     'bandwidth': {
#     #       '*': {'bandwidth': (15000.0, -0.1, None, 'MB/s')} # Placeholder for bandwidth
#     #     }
#     #   }
#     #   self.reference = references[metric]



# # ============================================================================
# # Test Case: Same Physical Socket, Different NUMA Nodes (Targeted for Aion)
# # ============================================================================
# @rfm.simple_test
# class OsuSameSocketDifferentNuma(OsuBwLatencyBenchmarkBase):
#     descr = 'OSU Pt2Pt: Same Socket, Different NUMA Nodes (Aion Specific)'

#     # --- Target only Aion for this specific test ---
#     valid_systems = ['aion:batch']

#     # --- MPI Binding ---
#     @run_before('run')
#     def set_mpi_binding(self):
#         self.job.launcher.options += [
#             # '--cpu-bind=cores',
#             '--cpu-bind=verbose,cores',
#             # '--cpu-bind=map_ldom:0,0',
#             '--mem-bind=local',
#             '--distribution=block:block'
#         ]

#         self.env_vars['OMPI_MCA_hwloc_base_report_bindings'] = '1'

#     # @run_before('performance')
#     # def set_references(self):
#     #     metric = self.benchmark_info[1]
#     #     if metric == 'latency':
#     #         self.reference = {'*': {'latency': (1.5, -0.1, 0.5, 'us')}}
#     #     elif metric == 'bandwidth':
#     #         self.reference = {'*': {'bandwidth': (14000.0, -0.1, None, 'MB/s')}}


# # ============================================================================
# # Test Case: Same Compute Node, Different Physical Sockets
# # ============================================================================

# @rfm.simple_test
# class OsuDifferentSockets(OsuBwLatencyBenchmarkBase):
#     descr = 'OSU Pt2Pt: Same Node, Different Sockets'

#     # --- MPI Binding ---
#     @run_before('run')
#     def set_mpi_binding(self):
#          # These SLURM options are passed to srun
#         self.job.launcher.options += [
#             '--ntasks-per-socket=1',
#             '--cpu-bind=verbose,cores',
#             '--mem-bind=local',
#             '--distribution=cyclic:cyclic'
#         ]

#         # self.env_vars['OMPI_MCA_rmaps_base_mapping_policy'] = 'socket'
#         # self.env_vars['OMPI_MCA_hwloc_base_binding_policy'] = 'core'
#         self.env_vars['OMPI_MCA_hwloc_base_report_bindings'] = '1'



# # ============================================================================
# # Test Case: 2 processes are running on different nodes.
# # ============================================================================

# @rfm.simple_test
# class OsuDifferentNodes(OsuBwLatencyBenchmarkBase):
#     descr = 'OSU Pt2Pt: Same Node, Different Sockets'

#     num_tasks_per_node = 1

#     # --- MPI Binding ---
#     @run_before('run')
#     def set_mpi_binding(self):

#         self.job.launcher.options += [
#             '--nodes=2'
#         ]

#         self.env_vars['OMPI_MCA_hwloc_base_report_bindings'] = '1'