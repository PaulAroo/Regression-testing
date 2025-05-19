#!/bin/bash
#SBATCH --job-name="rfm_EESSIOsuSameNumaNode_a396602f"
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=rfm_job.out
#SBATCH --error=rfm_job.err
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --partition=batch
#SBATCH --qos=normal
#SBATCH --time=0-00:10:00
module load env/testing/2023b
module load toolchain/foss/2023b
module load tools/EasyBuild
export OMPI_MCA_hwloc_base_report_bindings=1
module load EESSI
module load OSU-Micro-Benchmarks/7.2-gompi-2023b
srun --cpus-per-task=1 --cpu-bind=verbose,cores --mem-bind=local --distribution=block:block osu_latency -m 8192:8192 -x 10 -i 100
