import parsl
import os
import time,sys

from parsl.app.app import python_app, bash_app
from parsl.data_provider.files import File

from parslpw import pwconfig,pwargs

@bash_app
def sort_numbers_4 (inputs=[], outputs=[]):
    return '''
        if1=%s
        if2=%s
        of=%s
        echo $(date) $(hostname) $(/bin/pwd) $0: $if1 $if2 $of >> /pworks/bash_app.log
        cat $if1 $if2 |
        sort -n > $of
    ''' % (inputs[0].filename, inputs[1].filename, outputs[0].filename)

def main():
    prefix = 'file://parslhost/' # + os.getcwd() + '/'
    unsorted_file_1 = File(prefix+pwargs.sort1)
    unsorted_file_2 = File(prefix+pwargs.sort2)
    out_file        = File(prefix+pwargs.sorted)

    f = sort_numbers_4(inputs=[unsorted_file_1, unsorted_file_2], outputs=[out_file])
    
    print (f.result())
    print("test of PW Coasters done")

parsl.load(pwconfig)

main()
#====================================
# Setup ====> START HERE
#====================================

import parsl
from parsl.app.app import python_app, bash_app
from parsl.data_provider.files import File
from path import Path
from parsl.configs.local_threads import config
import numpy as np
import os
import logging # Needed for parsl.set_file_logger
import subprocess

# Is this script being run with PW-Parsl?
# (Usually, only False for testing or if
# not running from the PW platform.)
USE_PWCONFIG = True
# Only applies if USE_PWCONFIG=False
USE_SLURM = True

if USE_PWCONFIG:
    from parslpw import pwconfig,pwargs
    config = pwconfig
    config.executors[0].worker_debug = True
else:
    # Without PW, we manually configure compute resources.
    from parsl.config import Config

    if USE_SLURM:
        #--------------------------------------------------
        # Glenn's examples for SLURM resource config:
        #--------------------------------------------------
        # CPU: srun --nodes 1 --tasks-per-node 40 --cpus-per-task 1 -t 1:00:00 --mem 20GB  --pty /bin/bash
        # GPU: srun --gres=gpu:1 --nodes 1 --tasks-per-node 1 --cpus-per-task 6 -t 2:00:00 --mem 20GB  --pty /bin/bash
        #
        #--------------------------------------------------
        # Troubleshooting:
        #--------------------------------------------------
        # If you are having trouble with the resource config, a good place
        # to look for error messages is the most recent directory in ./parsllogs
        # Another place to look at the actual SLURM submit scripts is ./runinfo/XXX/
        # On Greene, if you have lots of RAM per #CPU, change cs to cm.
        #
        #--------------------------------------------------
        # Cores per worker inconsistency:
        #--------------------------------------------------
        # Based on: parsl/providers/slurm/slurm.py submit(cmd, ntasks_per_node)
        # and /parsl/executors/high_throughput/executor.py "job_id = self.provider.submit(launch_cmd, 1)"
        # I think in Parsl, --ntask-per-node is not passed through SBATCH but only through process_pool.py -c.
        # See cores_per_worker and cores_per_node, below, which are INDEPENDENTLY used by Parsl and SLURM, respectively.
        # If cores_per_worker > cores_per_node then Parsl fails b/c SLURM rejects the job?
        # If cores_per_worker < cores_per_node then Parsl runs, but resource underprovisioned (e.g. OpenMP tasks fighting over cores)
        #
        from parsl.executors import HighThroughputExecutor
        from parsl.providers import SlurmProvider
        from parsl.launchers import SrunLauncher
        config = Config(
            executors=[
                HighThroughputExecutor(
                    label='slurm',
                    worker_debug=True,             # Default False for shorter logs
                    cores_per_worker=int(1),       # DOES NOT correspond to --cpus-per-task 1 per Parsl docs.  Rather BYPASSES SLURM opts and is process_pool.py -c cores_per_worker, but IS NOT CORES ON SLURM - sets number of workers
                    working_dir = '/tmp/pworks/',
                    worker_logdir_root = os. getcwd() + '/parsllogs',
                    provider = SlurmProvider(
                        #========GPU RUNS=============
                        #partition = 'rtx8000',         # For GPU runs! Or v100.  gr,gv,cr,cv on NYU HPC site does not work
                        #scheduler_options = '#SBATCH --gres=gpu:1', # For GPU runs!
                        #========CPU RUNS============
                        #scheduler_options = '#SBATCH --ntasks-per-node=40',  # DO NOT USE! Conflicts with cores_per_worker where Parsl sets --ntasks-per-node on separate SBATCH command, see note above.
                        partition = 'cs',          # Cluster specific! Needs to match GPU availability, and RAM per CPU limits specified for partion.
                        #===========================
                        mem_per_node = int(20),
                        nodes_per_block = int(1),
                        cores_per_node = int(6),   # Corresponds to --cpus-per-task
                        min_blocks = int(0),
                        max_blocks = int(10),
                        parallelism = 1,           # Was 0.80, 1 is "use everything you can NOW"
                        exclusive = False,         # Default is T, hard to get workers on shared cluster
                        walltime='02:00:00',       # Will limit job to this run time, 10 min default Parsl
                        launcher=SrunLauncher() # defaults to SingleNodeLauncher() which seems to work, experiment later?
                    )
                )
            ]
        )
    else:
        from parsl.executors.threads import ThreadPoolExecutor
        config = Config(
            executors=[ThreadPoolExecutor(max_threads = 2)]
        )

print(config)
parsl.load(config)
print("Config loaded")

#=================================
# Bash app
#=================================

@bash_app
def run_gromacs(
    stdout='run_gromacs.stdout',
    stderr='run_gromacs.stderr',
    inputs=[], outputs=[]):

    import os
    gromacs_run = os.path.basename(inputs[0])
    run_file = os.path.basename(inputs[1])
    run_script = os.path.basename(inputs[2])

    out_file = os.path.splitext(os.path.basename(inputs[1]))[0]+'.log'

    # This works for remote runs with parslpw but
    # it confuses regular Parsl because there is
    # a change in the path.  With regular Parsl,
    # it will still create output, but it will be
    # local (to this directory) and it won't be
    # mapped back to the larger-scale dir/file
    # tracking system.
    #out_dir = os.path.basename(outputs[0])

    # This works for local runs with regular Parsl
    # because the path is preserved.
    out_dir = outputs[0]

    run_command = "/bin/bash " + gromacs_run + " " + run_file + " " + run_script + " > " + out_file

    # The text here is interpreted by Python (hence the %s string substitution
    # using strings in the tuple at the end of the long text string) and then
    # run as a bash app.
    return '''
        echo User is: `whoami`
        echo Host is: $HOSTNAME
        echo Start file listing........................
        ls
        %s
        wait
        echo Done file listing.........................
        ls
        outdir=%s
        outfile=%s
#        mkdir -p $outdir
        mv $outfile $outdir
    ''' % (run_command,out_dir,out_file)

@bash_app
def get_date(
    stdout='get_date.stdout',
    stderr='get_date.stderr',
    inputs=[], outputs=[]):

    run_command = "echo Input: "+inputs[0].filepath+" Output: "+outputs[0].filepath+" and date is: `date` > " + outputs[0].filepath

    return '''
        %s
        ''' % (run_command)

#=================================
# Start the run here
#=================================

@bash_app
def run_alphafold(inputs=[],outputs=[],wrapper_name="get_alphafold_models.sh"):
    run_command = f"bash {wrapper_name} {inputs[0]}"
    return run_command

if __name__ == "__main__":
    import glob
    parsl.set_file_logger('main.py.log', level=logging.DEBUG)

    # Set default paths if they are not specified
    # on the command line (see HELLO_WORLD_TEST which
    # for case that bypasses command line args).
    if USE_PWCONFIG:
        output_dir = '/pw/storage/test-outputs'
        input_dir = '/pw/workflows/dev'
    else:
        input_dir = os.getcwd()
        output_dir = input_dir+'/test-outputs'

    HELLO_WORLD_TEST = False
    if HELLO_WORLD_TEST:
        import argparse
        pwargs = argparse.Namespace()
        pwargs.out_dir = output_dir

        pwargs.run_files = input_dir+'/test_01.tgz'
        for ii in np.arange(2,99):
            pwargs.run_files += '---'+input_dir+'/test_'+str(ii).zfill(2)+'.tgz'

        # Really simple case
        wrapper = Path("wrapper_test.sh")
        run_script = Path("runner_test.sh")

        # Create the output dir.  This is not
        # strictly necessary since run_gromacs
        # will also try mkdir -p.  However,
        # get_date will NOT and so it fails
        # unless this directory already exists.
        bash_command = 'mkdir -p '+output_dir
        subprocess.run(bash_command.split())

    else:
        if USE_PWCONFIG:
            # Command line args are passed from platform;
            print('Command line args already set')

        else:
            # Command line args must be specified
            import argparse
            parser = argparse.ArgumentParser(description='Run Alphafold on Fasta files')
            parser.add_argument('--out_dir',metavar='/tmp/data',type=str,help='output directory')
            #parser.add_argument('--cpu_or_gpu',metavar='/tmp/data',type=str,help='CPU or GPU runner')
            #parser.add_argument('--mem_or_sol',metavar='/tmp/data',type=str,help='Membrane or Solvate wrapper')
            parser.add_argument('--run_files',metavar='/tmp/data',type=str,help='Input files separated by ---, eg. /path/file1---/path/file2')
            pwargs = parser.parse_args()

        # Select one wrapper, paired with input data:
        #if pwargs.mem_or_sol == "True":
        #    wrapper = Path("run_equil_charmmgui_membrane_gromacs.sh")
        #else:
        #    wrapper = Path("run_equil_charmmgui_solvate_gromacs.sh")
        #wrapper = Path("./get_alphafold_models.sh")

        # Select one run_script, CPU or GPU
        #if pwargs.cpu_or_gpu == "True":
        #    run_script = Path("gromacs.greene.sh")
        #else:
        #    run_script = Path("gromacs.greene.gpu.sh")

    # List of run_files is from the PW platform form or above
    run_files = pwargs.run_files.split('---')

    runs=[]
    send_files = [Path(f) for f in glob.glob("*.sh")+glob.glob("*.py")]
    out_dir = Path('predictions/')
    for run_file_name in run_files:
        #========Run workflow with Path objects=========
        run_file = Path(run_file_name)
        #out_dir = Path(pwargs.out_dir)
        #out_path = os.path.join('outputs',os.path.splitext(os.path.basename(run_file_name))[0])
        #out_dir = Path(out_path+'/')

        r = run_alphafold(
            #inputs=[wrapper,run_file,run_script],
            inputs = [run_file]+send_files,
            outputs=[out_dir])
        runs.append(r)

        #=========Test workflow with File objects=============
        #run_file = File(run_file_name)
        #out_file_basename = os.path.splitext(os.path.basename(run_file_name))[0]+'.log'
        #out_file = File(pwargs.out_dir+"/date-"+out_file_basename)
        #r = get_date(
        #    inputs=[run_file],
        #    outputs=[out_file])
        #runs.append(r)

    print("Running",len(runs),"alphafold executions...")
    [r.result() for r in runs]
