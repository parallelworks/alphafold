def gen_table(outcsv, outhtml):
    import glob
    import os
    def get_af_csv_line(pdbfile):
        import os
        import pickle
        label, _, _, model, seed = os.path.splitext(os.path.basename(pdbfile))[0].split("_")
        relaxed = not( os.path.basename(pdbfile).find('unrelaxed')>0 )
        job_dir = os.path.dirname(pdbfile)
        seed = seed.replace("seed","")
        image = pdbfile.replace('pdb','jpg')
        picklefile = os.path.join(job_dir,f"{label}_seed{seed}.result.pickle")
    
        result_data = pickle.load(open(picklefile,'rb'))
        plddt_data = result_data[f"model_{model}"]['plddt']
        mean_plddt = plddt_data.mean()
    
        return f"{label},{model},{seed},{relaxed},{image},{mean_plddt},{pdbfile}"
    
    rows = ['label, model, seed, is_relaxed, img:model, out:plddt, out:pdbfile']
    pdb_files = glob.glob("predictions/*/*relaxed*.pdb")
    for pdb_file in pdb_files:
        rows.append( get_af_csv_line(os.path.abspath(pdb_file) ))
    #    rows.append( get_af_csv_line(pdb_file))
    
    with open(outcsv,'w') as file:
        file.write("\n".join(rows))
    
    with open(outhtml, 'w') as html:
        html.write("""<html style="overflow-y:hidden;background:white">
        <a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="/preview/DesignExplorer/index.html?datafile={}&colorby={}" target="_blank">Open in New Window</a>
        <iframe width="100%" height="100%" src="/preview/DesignExplorer/index.html?datafile={}&colorby={}" frameborder="0"></iframe>
    </html>""".format(outcsv,'plddt',outcsv, 'plddt'))

if __name__ == "__main__":
    import os
    outcsv = os.path.abspath("test.csv")
    outhtml = os.path.abspath("test.html")
    gen_table(outcsv, outhtml)
