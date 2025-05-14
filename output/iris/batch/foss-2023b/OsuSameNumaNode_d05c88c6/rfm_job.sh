#!/bin/bash
#SBATCH --job-name="rfm_OsuSameNumaNode_d05c88c6"
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=rfm_job.out
#SBATCH --error=rfm_job.err
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --partition=batch
#SBATCH --qos=normal
#SBATCH -C skylake
#SBATCH --time=0-00:10:00
module load env/testing/2023b
module load toolchain/foss/2023b
module load tools/EasyBuild
export OMPI_MCA_hwloc_base_report_bindings=1
srun --cpus-per-task=1 --cpu-bind=verbose,cores --mem-bind=local --distribution=block:block /mnt/aiongpfs/users/paromolaran/project_playground/stage/iris/batch/foss-2023b/OsuBuildSource_d4a714f1/osu-micro-benchmarks-7.2/c/mpi/pt2pt/standard/osu_bw -m 1048576:1048576 -x 10 -i 100
