#====================================
# Setup
#====================================

# General requirements
import numpy as np
import os
import logging # Needed for parsl.set_file_logger
import subprocess

# Parsl requirements
import parsl
from parsl.app.app import python_app, bash_app
from parsl.data_provider.files import File
from parsl.configs.local_threads import config

# Parallel Works requirements
from path import Path
from parslpw import pwconfig,pwargs
pwconfig.executors[0].worker_debug = True

# Load config
print("======================")
print("PW config:")
print("======================")
print(pwconfig)
parsl.load(pwconfig)
print("PW config loaded")

#=================================
# Parsl Apps
#=================================
# Parsl apps are functions that are
# decorated with @bash_app or @python_app.
# Parsl apps' execution is directed
# by Parsl and in parallel.

@bash_app
def run_alphafold(inputs=[],outputs=[],wrapper_name="get_alphafold_models.sh"):
    # Use Python 3.6+ f-strings for concise
    # construction of command to run, see:
    # https://realpython.com/python-f-strings/
    run_command = f"bash {wrapper_name} {inputs[0]}"
    return run_command

#=================================
# Start the run here
#=================================

if __name__ == "__main__":
    import glob
    parsl.set_file_logger('main.py.log', level=logging.DEBUG)

    output_dir = '/pw/storage/test-outputs'

    # Create output dir if not already present
    bash_command = 'mkdir -p '+output_dir
    subprocess.run(bash_command.split())

    # List of run_files is from the PW platform form
    run_file_names = pwargs.run_files.split('---')

    # Initialize list of Parsl app futures
    runs=[]

    send_files = [Path(f) for f in glob.glob("*.sh")+glob.glob("*.py")]
    out_dir_name = pwargs.out_dir
    out_dir = Path(out_dir_name)

    for run_file_name in run_file_names:

        run_file = Path(run_file_name)

        r = run_alphafold(
            inputs = [run_file]+send_files,
            outputs=[out_dir])
        runs.append(r)

    print("Running",len(runs),"alphafold executions...")
    [r.result() for r in runs]
