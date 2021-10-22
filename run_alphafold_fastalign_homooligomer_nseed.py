#@title Import libraries
# setup the model
use_templates = False

# Taken from: http://shallowsky.com/blog/programming/python-tee.html
class tee :
    def __init__(self, _fd1, _fd2) :
        self.fd1 = _fd1
        self.fd2 = _fd2

    def __del__(self) :
        if self.fd1 != sys.stdout and self.fd1 != sys.stderr :
            self.fd1.close()
        if self.fd2 != sys.stdout and self.fd2 != sys.stderr :
            self.fd2.close()

    def write(self, text) :
        self.fd1.write(text)
        self.fd2.write(text)

    def flush(self) :
        self.fd1.flush()
        self.fd2.flush()

def tee_logfile( output_prefix ):
    logfile = output_prefix+'.log'
    fh = open(logfile,'w',buffering=1)
    stdout_sv = sys.stdout
    stderr_sv = sys.stderr
    sys.stdout = tee( stdout_sv, fh )
    sys.stderr = tee( stderr_sv, fh )

if "model" not in dir():

  # hiding warning messages
  import warnings
  from absl import logging
  import os
  import tensorflow as tf
  warnings.filterwarnings('ignore')
  logging.set_verbosity("error")
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
  tf.get_logger().setLevel('ERROR')

  import sys
  import numpy as np
  import pickle
  from alphafold.common import protein
  from alphafold.data import pipeline
  from alphafold.data import templates
  from alphafold.model import data
  from alphafold.model import config
  from alphafold.model import model
  from alphafold.data.tools import hhsearch
  from alphafold.relax import relax

  RELAX_MAX_ITERATIONS = 0
  RELAX_ENERGY_TOLERANCE = 2.39
  RELAX_STIFFNESS = 10.0
  RELAX_EXCLUDE_RESIDUES = []
  RELAX_MAX_OUTER_ITERATIONS = 20
  amber_relaxer = relax.AmberRelaxation(
        max_iterations=RELAX_MAX_ITERATIONS,
        tolerance=RELAX_ENERGY_TOLERANCE,
        stiffness=RELAX_STIFFNESS,
        exclude_residues=RELAX_EXCLUDE_RESIDUES,
        max_outer_iterations=RELAX_MAX_OUTER_ITERATIONS)


  # plotting libraries
  #import py3Dmol
  #import matplotlib.pyplot as plt
  #import ipywidgets
  #from ipywidgets import interact, fixed

def mk_mock_template(query_sequence):
  # since alphafold's model requires a template input
  # we create a blank example w/ zero input, confidence -1
  ln = len(query_sequence)
  output_templates_sequence = "-"*ln
  output_confidence_scores = np.full(ln,-1)
  templates_all_atom_positions = np.zeros((ln, templates.residue_constants.atom_type_num, 3))
  templates_all_atom_masks = np.zeros((ln, templates.residue_constants.atom_type_num))
  templates_aatype = templates.residue_constants.sequence_to_onehot(output_templates_sequence,
                                                                    templates.residue_constants.HHBLITS_AA_TO_ID)
  template_features = {'template_all_atom_positions': templates_all_atom_positions[None],
                       'template_all_atom_masks': templates_all_atom_masks[None],
                       'template_sequence': [f'none'.encode()],
                       'template_aatype': np.array(templates_aatype)[None],
                       'template_confidence_scores': output_confidence_scores[None],
                       'template_domain_names': [f'none'.encode()],
                       'template_release_date': [f'none'.encode()]}
  return template_features

def mk_template(jobname):
  template_featurizer = templates.TemplateHitFeaturizer(
      mmcif_dir="templates/",
      max_template_date="2100-01-01",
      max_hits=20,
      kalign_binary_path="kalign",
      release_dates_path=None,
      obsolete_pdbs_path=None)

  hhsearch_pdb70_runner = hhsearch.HHSearch(binary_path="hhsearch",databases=[jobname])

  a3m_lines = "\n".join(open(f"{jobname}.a3m","r").readlines())
  hhsearch_result = hhsearch_pdb70_runner.query(a3m_lines)
  hhsearch_hits = pipeline.parsers.parse_hhr(hhsearch_result)
  templates_result = template_featurizer.get_templates(query_sequence=query_sequence,
                                                       query_pdb_code=None,
                                                       query_release_date=None,
                                                       hhr_hits=hhsearch_hits)
  return templates_result.features

def set_bfactor(pdb_filename, bfac, idx_res, chains):
  I = open(pdb_filename,"r").readlines()
  O = open(pdb_filename,"w")
  for line in I:
    if line[0:6] == "ATOM  ":
      seq_id = int(line[22:26].strip()) - 1
      seq_id = np.where(idx_res == seq_id)[0][0]
      O.write(f"{line[:21]}{chains[seq_id]}{line[22:60]}{bfac[seq_id]:6.2f}{line[66:]}")
  O.close()

def predict_structure(prefix, feature_dict, Ls, model_params, use_model, do_relax=False, random_seed=0):
  """Predicts structure using AlphaFold for the given sequence."""

  # Minkyung's code
  # add big enough number to residue index to indicate chain breaks
  idx_res = feature_dict['residue_index']
  L_prev = 0
  # Ls: number of residues in each chain
  for L_i in Ls[:-1]:
      idx_res[L_prev+L_i:] += 200
      L_prev += L_i
  chains = list("".join([ascii_uppercase[n]*L for n,L in enumerate(Ls)]))
  feature_dict['residue_index'] = idx_res

  # Run the models.
  plddts,paes = [],[]
  unrelaxed_pdb_lines = []
  relaxed_pdb_lines = []
  relaxed_amber_data = []

  for model_name, params in model_params.items():
    if model_name in use_model:
      print(f"running {model_name}, seed {random_seed}")
      # swap params to avoid recompiling
      # note: models 1,2 have diff number of params compared to models 3,4,5
      if any(str(m) in model_name for m in [1,2]): model_runner = model_runner_1
      if any(str(m) in model_name for m in [3,4,5]): model_runner = model_runner_3
      model_runner.params = params

      processed_feature_dict = model_runner.process_features(feature_dict, random_seed=random_seed)
      prediction_result = model_runner.predict(processed_feature_dict)
      unrelaxed_protein = protein.from_prediction(processed_feature_dict,prediction_result)
      unrelaxed_pdb_lines.append(protein.to_pdb(unrelaxed_protein))
      plddts.append(prediction_result['plddt'])
      paes.append(prediction_result['predicted_aligned_error'])

      if do_relax:
        # Relax the prediction.
        amber_relaxer = relax.AmberRelaxation(max_iterations=0,tolerance=2.39,
                                              stiffness=10.0,exclude_residues=[],
                                              max_outer_iterations=20)
        relaxed_pdb_str, relax_data, _ = amber_relaxer.process(prot=unrelaxed_protein)
        relaxed_pdb_lines.append(relaxed_pdb_str)
        relaxed_amber_data.append(relax_data)
        print(relax_data)

  ## rerank models based on predicted lddt
  #lddt_rank = np.mean(plddts,-1).argsort()[::-1]
  out = {}
  #print("reranking models based on avg. predicted lDDT")
  lddt_rank = range(len(np.mean(plddts,-1)))
  for n,r in enumerate(lddt_rank):
    print(f"model_{n+1} seed_{random_seed} {np.mean(plddts[r])}")

    unrelaxed_pdb_path = f'{prefix}_unrelaxed_model_{n+1}_seed{random_seed}.pdb'
    with open(unrelaxed_pdb_path, 'w') as f: f.write(unrelaxed_pdb_lines[r])
    set_bfactor(unrelaxed_pdb_path, plddts[r]/100, idx_res, chains)

    if do_relax:
      relaxed_pdb_path = f'{prefix}_relaxed_model_{n+1}_seed{random_seed}.pdb'
      with open(relaxed_pdb_path, 'w') as f: f.write(relaxed_pdb_lines[r])
      set_bfactor(relaxed_pdb_path, plddts[r]/100, idx_res, chains)

      relaxed_amber_path = f'{prefix}_relaxed_model_{n+1}_seed{random_seed}.amberdata.pickle'
      pickle.dump(relaxed_amber_data[r],open(relaxed_amber_path,'wb'))

    out[f"model_{n+1}"] = {"plddt":plddts[r], "pae":paes[r]}
  return out

if __name__ == "__main__":
    import tempfile
    import shutil
    import argparse

    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    parser = argparse.ArgumentParser(description='Process some command line arguments',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('fasta_file',metavar='fasta_file',type=str,help="Input fasta file")
    parser.add_argument('--alignment_file',type=str,help="Input pre-calculated alignment file in a3m format")
    parser.add_argument('--n_models',type=int,default=5,help="Number of alpha fold models to use (1-5)")
    parser.add_argument('--seed',type=int,default=1,help="Random seed to use")
    parser.add_argument('--homo_oligomer_copies',type=int,default=1,help="Number of repeats of this sequence in oligomer")
    parser.add_argument('--use_amber',default=False,action='store_true',help="Use openmm/amber for relax")
    parser.add_argument('--no_msa',default=False,action='store_true',help="Don't get an MSA prediction, just use single sequence")

    args = parser.parse_args()
    fasta_file = args.fasta_file
    fasta_dir = os.path.dirname(fasta_file)
    homooligomer=args.homo_oligomer_copies
    seed = args.seed

    name = os.path.splitext(os.path.basename(fasta_file))[0]
    assert os.path.exists(fasta_file), "Fasta file must exist"
    assert args.n_models>=1 and args.n_models<=5, "--n_models must be in [1-5]"
#    out_dir = os.path.join(script_dir,'temp_outputs')
    out_dir = fasta_dir

    os.makedirs(out_dir,exist_ok=True)
    #run_dir = tempfile.mkdtemp(prefix=name+'_',dir=out_dir)
    run_dir = os.path.join(out_dir,f"alphafold_{name}")
    if args.no_msa is True:
        run_dir = run_dir+'_noMSA'
    os.makedirs(run_dir,exist_ok=True)
    tee_logfile( os.path.join(run_dir,os.path.basename(run_dir)))

    temp_file = os.path.join(run_dir,os.path.basename(fasta_file))
    shutil.copyfile(fasta_file,temp_file)

    a3m_file = None
    if args.alignment_file is not None:
        a3m_file = args.alignment_file
        assert os.path.exists(a3m_file), "alignment file must exist if given"
        temp_a3m_file = os.path.join(run_dir,os.path.basename(a3m_file))
        shutil.copyfile(a3m_file,temp_a3m_file)

    if args.no_msa is True:
        print("Using only a single sequence")
        temp_a3m_file = temp_file.replace('.fasta','.a3m')
        a3m_file = temp_a3m_file
        shutil.copyfile(temp_file,temp_a3m_file)

    query_sequence = "".join(open(fasta_file,'r').readlines()[1:]).strip()


    from string import ascii_uppercase

    # collect model weights
    use_model = {}
    if "model_params" not in dir(): model_params = {}
    for model_name in ["model_1","model_2","model_3","model_4","model_5"][:args.n_models]:
      use_model[model_name] = True
      if model_name not in model_params:
        model_params[model_name] = data.get_model_haiku_params(model_name=model_name+"_ptm", data_dir=".")
        if model_name == "model_1":
          model_config = config.model_config(model_name+"_ptm")
          model_config.data.eval.num_ensemble = 1
          model_runner_1 = model.RunModel(model_config, model_params[model_name])
        if model_name == "model_3":
          model_config = config.model_config(model_name+"_ptm")
          model_config.data.eval.num_ensemble = 1
          model_runner_3 = model.RunModel(model_config, model_params[model_name])

    if a3m_file is None:
        print(f"Starting msa on file {temp_file}")
        os.system(f"{script_dir}/get_msa_mmseqs2.sh {temp_file}")
        msa, deletion_matrix = pipeline.parsers.parse_a3m("".join(open(f"{run_dir}/{name}.a3m","r").readlines()))
    else:
        print(f"Starting using msa from file {temp_a3m_file}")
        print(temp_a3m_file)
        msa, deletion_matrix = pipeline.parsers.parse_a3m("".join(open(f"{temp_a3m_file}","r").readlines()))

    # parse TEMPLATES
    if use_templates and os.path.isfile(f"{jobname}_hhm.ffindex"):
        template_features = mk_template(jobname)
    else:
        template_features = mk_mock_template(query_sequence * homooligomer)

    #parse msa
    if homooligomer == 1:
        msas = [msa]
        deletion_matrices = [deletion_matrix]
    else:
        # make multiple copies of msa for each copy
        # AAA------
        # ---AAA---
        # ------AAA
        #
        # note: if you concat the sequences (as below), it does NOT work
        # AAAAAAAAA
        msas = []
        deletion_matrices = []
        Ln = len(query_sequence)
        for o in range(homooligomer):
            L = Ln * o
            R = Ln * (homooligomer-(o+1))
            msas.append(["-"*L+seq+"-"*R for seq in msa])
            deletion_matrices.append([[0]*L+mtx+[0]*R for mtx in deletion_matrix])

    # gather features
    print("Running prediction on",query_sequence)
    feature_dict = {
        **pipeline.make_sequence_features(sequence=query_sequence*homooligomer,
                                          description="none",
                                          num_res=len(query_sequence)*homooligomer),
        **pipeline.make_msa_features(msas=msas,deletion_matrices=deletion_matrices),
        **template_features
    }

    outs = predict_structure(os.path.join(run_dir,name), feature_dict,
        Ls=[len(query_sequence)]*homooligomer,
        model_params=model_params, use_model=use_model,
        do_relax=args.use_amber, random_seed=seed)
    pickle.dump(outs, open(os.path.join(run_dir,name)+f'_seed{seed}.result.pickle','wb'))

