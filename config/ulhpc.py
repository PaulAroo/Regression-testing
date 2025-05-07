
# ReFrame configuration for ULHPC cluster

site_configuration = {
  'systems': [
    {
      'name': 'iris',
      'descr': 'Iris cluster',
      'hostnames': [r'iris-[0-9]{3}'],
      'modules_system': 'lmod',
      'partitions': [
        {
          'name': 'batch',
          'descr': 'Iris Skylake compute nodes via batch partition',
          'scheduler': 'slurm',
          'launcher': 'srun', # Use srun to launch MPI jobs
          'access': ['--partition=batch', '-C skylake'],
          'environs': ['foss-2023b'], #software environments usable on these nodes
          'max_jobs': 8, # 8? probably should be a diff number
        },
      ]
    },
    # We can add the 'aion' system later
  ],

  'environments': [
    {
      'name': 'foss-2023b',
      'modules': [
        'env/testing/2023b', 
        'toolchain/foss/2023b' 
      ],
      
      # compilers for this environment
      'cc': 'mpicc',
      'cxx': 'mpicxx',
      'ftn': 'mpifort',
    },
    # We can add other environments later (e.g., EESSI)
  ],
}