# alphafold
Alphafold template workflow

# Setup

## Code

To pull this code directly from Github onto
the Parallel Works platform,
1. create a new workflow on the platform,
2. navigate into the new workflow's directory in `/pw/workflows/`,
3. delete any default/sample files that were created,
4. Run the following command in that directory:
```bash
git clone https://github.com/parallelworks/alphafold .
```
(Don't forget the . at the end of the command!)

## Resource configuration

For NYU's Greene cluster, create the default SLURM resource
in the PW GUI and add the following options in the custom
arguments field:
--ntasks-per-node=1 --cpus-per-task=8 --mem=30GB  --job-name=get_af_models --nodes=1 --gres=gpu:1 --tasks-per-node=1
Leave the partition blank, select your stored key,
and choose your jump box connection specifics.

# Run

Navigate to the compute tab and select the workflow
from the column on the left side.  The options on
the resulting form are controlled by `workflow.xml`
in the workflow folder.  The .fasta files should
autopopulate in the workflow form.  The other fields
are not used by the current config of the workflow
but they are present as examples to build more
complicated workflows.
