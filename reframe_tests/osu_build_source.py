# reframe_tests/osu_tests.py
import reframe as rfm
import reframe.utility.sanity as sn
import os # Needed for path joining

# ============================================================================
#  Part 1: Compilation Test for OSU Micro-Benchmarks from Source
# ============================================================================

class OsuBuildSource(rfm.CompileOnlyRegressionTest):
    '''Fixture for building the OSU benchmarks'''

    descr = 'Build OSU Micro-Benchmarks 7.2 from source using foss/2023b'

    # valid_systems = ['iris:batch']
    # valid_prog_environs = ['foss-2023b']

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
      # self.build_system.config_opts = ['CC=mpicc', 'CXX=mpicxx']
      # self.build_system.make_opts = ['-C', 'mpi']
      self.build_system.max_concurrency = 8

    @sanity_function
    def validate_build(self):
      # If build fails, the test will fail before reaching this point.
      return True

# --- Simplified Base Class for Point-to-Point OSU Benchmarks ---
#       It's meant to be inherited by actual test classes.
class OsuBenchmarkBase(rfm.RunOnlyRegressionTest):
    '''Base class for OSU Point-to-Point benchmark tests (osu_latency, osu_bw).'''

    # --- Common Configurable Variables ---
    # num_warmup_iters = variable(int, value=10, loggable=True)
    # num_iters = variable(int, value=1000, loggable=True)
    # message_size will be set based on the specific benchmark (latency/bw)
    message_size = variable(int, loggable=True)

    num_tasks = 2 # Point-to-point benchmarks always use 2 tasks
    num_tasks_per_node = 2
    num_cpus_per_task = 1

    # --- Parameter to select the specific pt2pt benchmark ---
    # benchmark_info: tuple(executable_name_suffix, metric_name)
    benchmark_info = parameter([
        ('osu_bw', 'bandwidth'),
        ('osu_latency', 'latency')
    ], fmt=lambda x: x[0], loggable=True) # Log only the executable name suffix

    # --- Fixture Dependency ---
    osu_binaries = fixture(OsuBuildSource, scope='environment')

    @run_before('run')
    def set_executable_path(self):
        '''Sets the full path to the executable using the build fixture.'''
        # Assumes the build fixture follows a structure like mpi/pt2pt/osu_latency
        # Extract the last part of the name (e.g., 'osu_latency')
        exec_name = self.benchmark_info[0]
        # Construct path relative to the build fixture's output
        # The build_osu_benchmarks fixture uses build_prefix for the extracted dir name
        # and puts binaries under 'mpi/pt2pt/' within that.
        # build_stage_dir = self.osu_binaries.stagedir
        # base_source_dir_name = os.path.basename(self.osu_binaries.sourcesdir).replace('.tar.gz', '')
        self.executable = os.path.join(self.osu_binaries.stagedir,
                                       self.osu_binaries.build_prefix, 'c',
                                       'mpi', 'pt2pt', 'standard', exec_name)
        # Verify the constructed path exists (optional sanity check)
        if not os.path.exists(self.executable):
             raise RuntimeError(f"Executable not found at: {self.executable}")

    @run_before('setup')
    def setup_executable_options_and_perf(self):
        '''Sets executable options and performance variables based on benchmark type.'''
        exec_name, bench_metric = self.benchmark_info

        if bench_metric == 'latency':
            self.message_size = 8192 # Use 8KB for latency as per project spec
            unit = 'us'
        elif bench_metric == 'bandwidth':
            self.message_size = 1048576 # Use 1MB for bandwidth as per project spec
            unit = 'MB/s'
        else:
            # Should not happen with the restricted parameter list
            raise ValueError(f'Unknown benchmark metric: {bench_metric}')

        # Common options
        self.executable_opts = ['-m', f'{self.message_size}:{self.message_size}']
        self.reference_unit = unit # Store unit for reference setting

        # --- Define Performance Variables CORRECTLY ---
        # Define the regex to capture the performance value
        metric_regex = rf'^{self.message_size}\s+(?P<metric_val>\S+)'

        # Create the performance variable dictionary
        self.perf_variables = {
            # The key is the metric name ('latency' or 'bandwidth')
            bench_metric: sn.make_performance_function(
                # The first argument is the extraction logic
                sn.extractsingle(metric_regex, self.stdout, 'metric_val', float),
                # The second argument provides the unit
                unit=self.reference_unit
            )
        }

    @sanity_function
    def validate_test(self):
        '''Basic sanity check: Look for the output line of the tested message size.'''
        # We don't check for "Pass" as OSU pt2pt doesn't always print it reliably
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


# --- Example of how to use the base class ---
@rfm.simple_test
class OsuSameNumaSource(OsuBenchmarkBase):
    descr = 'OSU Point-to-Point Benchmark Run'

    # --- Specify system and environment ---
    valid_systems = ['*'] 
    valid_prog_environs = ['*']


    # --- Override placement for intra-node test if needed ---
    # For an intra-node test:
    # num_tasks_per_node = 2

    # --- MPI Binding ---
    @run_before('run')
    def set_mpi_binding(self):
      # Remove the direct srun options:
      # self.job.launcher.options = ['--map-by', 'numa', '--bind-to', 'core']

      # Set OpenMPI environment variables instead
      self.env_vars['OMPI_MCA_rmaps_base_mapping_policy'] = 'numa' # Corresponds to --map-by numa
      self.env_vars['OMPI_MCA_hwloc_base_binding_policy'] = 'core' # Corresponds to --bind-to core

      #make OpenMPI report bindings:
      # self.env_vars['OMPI_MCA_hwloc_base_report_bindings'] = '1'

      # Optional: For more verbose output from OpenMPI about mapping/binding
      self.env_vars['OMPI_MCA_rmaps_base_verbose'] = '10'
      self.env_vars['OMPI_MCA_hwloc_base_verbose'] = '10'



    # --- Set specific reference values ---
    @run_before('performance')
    def set_references(self):
      # This method overrides the default set in the base class
      metric = self.benchmark_info[1] # 'latency' or 'bandwidth'
      # (ADJUST THESE BASED ON YOUR SYSTEM)
      references = {
        'latency': {
          '*': {'latency': (1.8, -0.1, 0.5, 'us')} # Placeholder for latency
        },
        'bandwidth': {
          '*': {'bandwidth': (15000.0, -0.1, None, 'MB/s')} # Placeholder for bandwidth
        }
      }
      self.reference = references[metric]




# # OSU MPI Bandwidth Test v7.2
# # Size      Bandwidth (MB/s)
# # Datatype: MPI_CHAR.
# 1048576             17234.23



