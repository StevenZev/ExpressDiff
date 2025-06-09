import streamlit as st
from pathlib import Path
import os

import subprocess
import shutil

import getpass

import re
import pandas as pd




import pickle as pkl

from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats
from pydeseq2.utils import load_example_data



 
#st.set_page_config(layout="wide")
st.set_page_config(layout="centered")

# Define the target directory for saving uploaded files
RAW_READS_DIR = Path("raw_reads")
RAW_READS_DIR.mkdir(parents=True, exist_ok=True)


done_flag = Path("qc_logs/fastqc_multiqc_done.flag")


def is_job_running(job_name_substring):
    user = getpass.getuser()
    result = subprocess.run(
        ["squeue", "-u", user, "-o", "%.18i %.9P %.25j %.50u %.2t %.10M %.6D %R"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if job_name_substring in line:
                return True
    return False


def any_job_running(): #I don't think the print statement is handled well...
    job_list = ["BatchTrim", "STAR", "FastQC", "featureCounts"]
    for name in job_list:
        if is_job_running(name):
            #print(f"Detected running job: {name}")
            return True, name
    return False, ""

#def any_job_running():
#    return any(is_job_running(name) for name in ["BatchTrim", "STAR", "FastQC", "featureCounts"])

def get_valid_accounts():
    try:
        result = subprocess.run(["allocations"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()

        # Skip header liness
        data_lines = lines[2:]

        accounts = []
        for line in data_lines:
            parts = line.split()
            if len(parts) == 4 and parts[0] != "run:":
                accounts.append(parts[0])
        return accounts
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return []
    
def extract_sample_name(col_name):
    match = re.search(r'/([^/]+)_Aligned\.sortedByCoord\.out\.bam', col_name)
    return match.group(1) if match else col_name


def extract_counts(path):
    # Load the raw counts.txt file from featureCounts
    raw_counts = pd.read_csv(path, sep='\t', comment='#')

    # Drop non-count columns (feature metadata)
    count_data = raw_counts.drop(columns=["Chr", "Start", "End", "Strand", "Length"])

    # Set gene IDs as the index
    count_data = count_data.set_index("Geneid")

    # Save cleaned counts to CSV
    #!mkdir counts_matrix  << Not necessary hopefully
    
    Path("counts_matrix").mkdir(parents=True, exist_ok=True)
    
      
    count_data.columns = [extract_sample_name(col) for col in count_data.columns]
    
    #print(count_data)
    
    count_data.to_csv("counts_matrix/deseq_counts_matrix.csv")

    #print("Cleaned count matrix saved as 'deseq_counts_matrix.csv'")
    return count_data




def main():
    st.title("RNA-seq Adapter Selection and Report Viewer")
    
    
    
    st.subheader("Select Allocation To Charge:")
    accounts = get_valid_accounts()
    if accounts:
        selected_account = st.selectbox("allocations",accounts, label_visibility="hidden")
    else:
        st.error("Could not fetch SLURM accounts.")
        
    #selected_account

    
    '''
    ##### Working(ish) code for efficiency improvement:
    st.subheader("SLURM Allocation")
    use_custom_allocation = st.checkbox("Change Allocation (select an account)", True)

    if use_custom_allocation:
        accounts = get_valid_accounts()
        if accounts:
            selected_account = st.selectbox("Select SLURM account to charge:", accounts)
        else:
            st.error("Could not retrieve SLURM account list.")
            selected_account = default_account
    #else:
        #selected_account = default_account
        #st.text(f"Using default account: {default_account}")
    '''
    
    

    # File upload widget for raw reads
    st.subheader("Upload Raw Reads")
    st.markdown("Ensure Pairs Are Labeled: readName_1, readName_2")
    uploaded_files = st.file_uploader("Select your .fq.gz files", 
                                      type=[".fq.gz"], 
                                      accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            save_path = RAW_READS_DIR / file.name
            with open(save_path, "wb") as f:
                f.write(file.read())
        st.success(f"{len(uploaded_files)} file(s) saved to /raw_reads/")

 
    
    raw_reads_dir = Path("raw_reads")
    if st.button("Clear All Files in raw_reads/"):
        deleted = 0
        if raw_reads_dir.exists():
            for file in raw_reads_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    deleted += 1
        st.success(f"Deleted {deleted} file(s) from mapping_in/")
        st.rerun()  # Refresh file listing

    # Show updated list of files
    files_now = [f.name for f in raw_reads_dir.glob("*") if f.is_file()]
    st.subheader("Current Files in raw_reads:")
    if files_now:
        for f in files_now:
            st.write(f"- {f}")
    else:
        st.info("No reference files found in raw_reads/")
        
    st.markdown("---")

    
    # Button to run initial QC
    if st.button("Run Initial QC"):
        is_running_job, name = any_job_running()
        if is_running_job:
            st.warning("Job " + name + " is already running, please wait for it to finish.")
        else:
            script_path = Path("qc_raw.slurm")
            qc_logs_dir = Path("qc_logs")

            # Clean old logs/flag (before job starts)
            if qc_logs_dir.exists():
                for file in qc_logs_dir.glob("*"):
                    if file.is_file():
                        file.unlink()

            if script_path.exists():
                st.info("Submitting FastQC + MultiQC SLURM job...")
                result = subprocess.run(["sbatch", f"--account={selected_account}", str(script_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success(f"SLURM job submitted: {result.stdout.strip()}")
                else:
                    st.error(f"Error submitting job: {result.stderr}")
            else:
                st.error(f"SLURM script not found at {script_path}")
    
    
    

    
    if st.button("Check Initial QC Job Status"):
        if done_flag.exists():
            st.success("QC job completed successfully! ✅")
        else:
            st.info("QC job is still running or waiting to start.")
    

    #st.markdown("---")
    

    # Display an HTML report from disk
    st.subheader("Raw Reads Quality Control")
    

    html_path = Path("raw_multiqc_out/multiqc_report.html")

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            st.components.v1.html(html_content, height=800, scrolling=True)
         
        
        st.subheader("Open MultiQC Report")
        st.markdown(
            f'<a href="{html_path.resolve().as_uri()}" target="_blank">Open MultiQC Report in New Tab</a>',
            unsafe_allow_html=True
        )
        
        
    else:
        st.warning(f"No HTML report found at: {html_path}")        



    st.markdown("---")

    # Adapter selection dropdown
    st.subheader("Select Adapter Type")
    options = ["NexteraPE-PE",  "TruSeq2-PE",  "TruSeq2-SE",  
               "TruSeq3-PE-2",  "TruSeq3-PE",  "TruSeq3-SE"]
    selected_option = st.selectbox("Choose an option:", options)
    st.write(f"You selected: {selected_option}")

    
    
    st.markdown("---")
    
    # Trimmomatic job submission
    st.subheader("Run Trimmomatic Adapter Trimming")
    
    if st.button("Run Trimmomatic with Selected Adapter"):
        is_running_job, name = any_job_running()
        if is_running_job:
            st.warning("Job " + name + " is already running, please wait for it to finish.")
        else:
            adapter_path = Path("selected_adapter.txt")
            adapter_path.write_text(selected_option)

            trim_logs_dir = Path("trim_logs")

            # Clean old logs (before job starts)
            if trim_logs_dir.exists():
                for file in trim_logs_dir.glob("*"):
                    if file.is_file():
                        file.unlink()

            trimmomatic_script = Path("trimAdapters4.slurm")
            if trimmomatic_script.exists():
                st.info(f"Submitting Trimmomatic job using adapter: {selected_option}")
                result = subprocess.run(["sbatch", f"--account={selected_account}", str(trimmomatic_script)], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success(f"Trimmomatic job submitted: {result.stdout.strip()}")
                else:
                    st.error(f"Error submitting job: {result.stderr}")
            else:
                st.error(f"SLURM script not found at: {trimmomatic_script}")

        
    trim_done_flag = Path("trim_logs/trimming_done.flag")
    if st.button("Check Trimmomatic Job Status"):
        if trim_done_flag.exists():
            st.success("Trimmomatic job completed! ✅")
        else:
            st.info("Trimmomatic job is not started or still running.")


    st.markdown("---")
    
    # Button to run post-trimming QC
    if st.button("Run Post-Trimming QC"):
        is_running_job, name = any_job_running()
        if is_running_job:
            st.warning("Job " + name + " is already running, please wait for it to finish.")
        else:
            script_path = Path("qc_trimmed.slurm")
            qc_logs_dir = Path("qc_logs")

            # Clean old logs/flag (before job starts)
            if qc_logs_dir.exists():
                for file in qc_logs_dir.glob("*"):
                    if file.is_file():
                        file.unlink()

            if script_path.exists():
                st.info("Submitting FastQC + MultiQC SLURM job...")
                result = subprocess.run(["sbatch", f"--account={selected_account}", str(script_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success(f"SLURM job submitted: {result.stdout.strip()}")
                else:
                    st.error(f"Error submitting job: {result.stderr}")
            else:
                st.error(f"SLURM script not found at {script_path}")
    
    

    if st.button("Check Post-Trim QC Job Status"):
        if done_flag.exists():
            st.success("QC job completed successfully! ✅")
        else:
            st.info("QC job is still running or waiting to start.")
    

    #st.markdown("---")
    
    

    # Display an HTML report from disk
    st.subheader("Trimmed Reads Quality Control")
    

    html_path = Path("trimmed_multiqc_out/multiqc_report.html")

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            st.components.v1.html(html_content, height=800, scrolling=True)
            
        st.subheader("Open MultiQC Report")
        st.markdown(
            f'<a href="{html_path.resolve().as_uri()}" target="_blank">Open MultiQC Report in New Tab</a>',
            unsafe_allow_html=True
        )
            
            
    else:
        st.warning(f"No HTML report found at: {html_path}")      
        
    st.markdown("---")

    
    # Upload reference files
    st.subheader("Upload  **.gtf** and **.fa** files (GTF annotation and FASTA genome).")
    st.markdown("##### Note: To delete uploaded files they must first be removed from the upload box.")

    # Create mapping_in directory if it doesn't exist
    MAPPING_IN_DIR = Path("mapping_in")
    MAPPING_IN_DIR.mkdir(parents=True, exist_ok=True)

    reference_files = st.file_uploader(
        "Select your .gtf and .fa files",
        type=["gtf", "fa"],
        accept_multiple_files=True
    )

    if reference_files:
        saved_files = []
        for file in reference_files:
            save_path = MAPPING_IN_DIR / file.name
            with open(save_path, "wb") as f:
                f.write(file.read())
            saved_files.append(file.name)
        st.success(f"Uploaded: {', '.join(saved_files)}")

    


    st.subheader("Clear mapping_in")
    mapping_dir = Path("mapping_in")
    if st.button("Clear All Files in mapping_in/"):
        deleted = 0
        if mapping_dir.exists():
            for file in mapping_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    deleted += 1
        st.success(f"Deleted {deleted} file(s) from mapping_in/")
        st.rerun()  # Refresh file listing

    # Show updated list of files
    files_now = [f.name for f in mapping_dir.glob("*") if f.is_file()]
    st.subheader("Current Files in mapping_in:")
    if files_now:
        for f in files_now:
            st.write(f"- {f}")
    else:
        st.info("No reference files found in mapping_in/")

    
        
        
        
    st.markdown("---")
    st.subheader("Run STAR Alignment")

    # Run STAR only if mapping_in has exactly one .fa and one .gtf
    if st.button("Run STAR Alignment Job"):
        is_running_job, name = any_job_running()
        if is_running_job:
            st.warning("Job " + name + " is already running, please wait for it to finish.")
        else:
            mapping_dir = Path("mapping_in")
            fa_files = list(mapping_dir.glob("*.fa"))
            gtf_files = list(mapping_dir.glob("*.gtf"))
            all_files = list(mapping_dir.glob("*"))

            if len(fa_files) == 1 and len(gtf_files) == 1 and len(all_files) == 2:
                # Clear old STAR logs
                star_logs_dir = Path("STAR_logs")
                if star_logs_dir.exists():
                    for file in star_logs_dir.glob("*"):
                        if file.is_file():
                            file.unlink()

                slurm_script = Path("STAR.slurm")
                if slurm_script.exists():
                    result = subprocess.run(["sbatch", f"--account={selected_account}", str(slurm_script)], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.session_state.star_submitted = True
                        st.session_state.star_job_message = f"STAR job submitted: {result.stdout.strip()}"
                    else:
                        st.error(f"SLURM submission failed: {result.stderr}")
                else:
                    st.error("STAR.slurm script not found.")
            else:
                st.error("mapping_in/ must contain exactly 1 .fa file and 1 .gtf file — no more, no less.")

            
            
    star_done_flag = Path("STAR_logs/star_alignment_done.flag")
    if st.button("Check STAR Alignment Status"):
        if star_done_flag.exists():
            st.success("STAR alignment completed! ✅")
        else:
            st.info("STAR alignment job is still running or hasn't started yet.")


    log_files = list(Path("STAR_out").glob("*_Log.final.out"))
    if log_files:
        for log_path in log_files:
            #st.markdown(f"**{log_path.name}**")
            with open(log_path) as f:
                st.text_area(f"{log_path.name}", f.read(), height=300)
    else:
        st.info("No STAR Log.final.out files found.")
    
   
    st.markdown("#### Clear Generated Genome Index:")
    confirm_index_delete = st.checkbox("I understand the STAR genome index will need to be re-generated.")
            
    if confirm_index_delete:
        if st.button("Delete genome_index Directory"):
            genome_index_dir = Path("STAR_out/genome_index")
            if genome_index_dir.exists() and genome_index_dir.is_dir():
                shutil.rmtree(genome_index_dir)
                st.success("Deleted STAR_out/genome_index directory.")
            else:
                st.info("genome_index directory does not exist.")
    else:
        st.warning("Check the box above to enable deletion.")
        
        
    st.markdown("#### Clear Mapping Output:")
    if st.button("Clear Mapping Output"):
        star_out_dir = Path("STAR_out")
        deleted = 0
        if star_out_dir.exists():
            for item in star_out_dir.iterdir():
                if item.name == "genome_index":
                    continue  # Skip the index folder
                if item.is_file():
                    item.unlink()
                    deleted += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted += 1
            st.success(f"Deleted {deleted} file(s)/folder(s) from STAR_out/ (genome_index preserved).")
        else:
            st.info("STAR_out directory does not exist yet.")
       
        
        
        
    st.markdown("---")
    st.subheader("Run featureCounts Gene Quantification")

    # Button to run featureCounts
    if st.button("Run featureCounts Job"):
        is_running_job, name = any_job_running()
        if is_running_job:
            st.warning("Job " + name + " is already running, please wait for it to finish.")
        else:
            # Basic checks
            gtf_files = list(Path("mapping_in").glob("*.gtf"))
            bam_files = list(Path("STAR_out").glob("*Aligned.sortedByCoord.out.bam"))

            if len(gtf_files) == 0:
                st.error("No GTF file found in mapping_in/")
            elif len(bam_files) == 0:
                st.error("No aligned BAM files found in STAR_out/")
            else:
                # Optionally clear previous logs
                fc_logs = Path("featureCounts_logs")
                if fc_logs.exists():
                    for file in fc_logs.glob("*"):
                        if file.is_file():
                            file.unlink()

                # Submit SLURM job
                script_path = Path("featureCounts.slurm")
                if script_path.exists():
                    result = subprocess.run(["sbatch", f"--account={selected_account}", str(script_path)], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success(f"featureCounts job submitted: {result.stdout.strip()}")
                    else:
                        st.error(f"Error submitting job: {result.stderr}")
                else:
                    st.error("SLURM script 'run_featureCounts.slurm' not found.")


    st.subheader("Check featureCounts Job Status")

    fc_done_flag = Path("featureCounts_logs/featurecounts_done.flag")
    if st.button("Check featureCounts Status"):
        if fc_done_flag.exists():
            st.success("featureCounts job completed successfully! ✅")
        else:
            st.info("featureCounts job is still running or hasn't started.")
            
    st.subheader("Clear FeatureCounts output")
    FCOut_dir = Path("featureCounts_out")
    if st.button("Clear All Files in featureCounts_out/"):
        deleted = 0
        if FCOut_dir.exists():
            for file in FCOut_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    deleted += 1
        st.success(f"Deleted {deleted} file(s) from featureCounts_out/")
        st.rerun()  # Refresh file listing
            
    

    st.markdown("**featureCounts Output:**")
    counts_file = Path("featureCounts_out/counts.txt.summary")
    if counts_file.exists():
        with open(counts_file) as f:
            #lines = f.readlines()
            #st.text("".join(lines[:20]))  # Show first 20 lines
            st.text_area("test", f.read(), height=300, label_visibility="hidden")
    else:
        st.info("No output file found yet.")
        
        
    st.markdown("---")
    st.subheader("Extract counts from FeatureCounts output:")
    
    if st.button("Extract Counts Dataframe:"):
        counts_path = Path("featureCounts_out/counts.txt")
        if counts_path.exists():
            counts_df = extract_counts("featureCounts_out/counts.txt")
            #print(counts_df)
            st.success("Counts extracted succesfully!")
        else:
            st.info("No FeatureCounts output found yet.")
    st.markdown("##### Extracted Counts Matrix:")
    
    counts_path = Path("counts_matrix/deseq_counts_matrix.csv")
    if counts_path.exists():
        count_matrix = pd.read_csv(counts_path, index_col=0)

        #counts_matrix = pd.read_csv("counts_matrix/deseq_counts_matrix.csv")
        counts_matrix.columns = [extract_sample_name(col) for col in counts_matrix.columns]

        #counts_matrix = counts_matrix.T

        st.dataframe(counts_matrix)
        #print(counts_df)
    
    st.markdown("---")
    

    st.subheader("Upload Sample Metadata (Design Matrix)")

    metadata_file = st.file_uploader(
        "Upload a metadata CSV or TSV file with at least `sample` and `condition` columns.",
        type=["csv", "tsv"]
    )

    metadata_df = None

    if metadata_file is not None:
        try:
            # Detect file type and load
            if metadata_file.name.endswith(".tsv"):
                metadata_df = pd.read_csv(metadata_file, sep="\t")
            else:
                metadata_df = pd.read_csv(metadata_file)

            required_cols = {"sample", "condition"}
            if not required_cols.issubset(metadata_df.columns):
                st.error(f"Metadata must include the columns: {', '.join(required_cols)}")
            else:
                st.success("Metadata loaded.")
                st.dataframe(metadata_df)

                # Load count matrix
                counts_path = Path("counts_matrix/deseq_counts_matrix.csv")
                if counts_path.exists():
                    count_matrix = pd.read_csv(counts_path, index_col=0)

                    # Compare sample names
                    count_samples = set(count_matrix.columns)
                    meta_samples = set(metadata_df["sample"])

                    missing_in_counts = meta_samples - count_samples
                    extra_in_counts = count_samples - meta_samples

                    if missing_in_counts:
                        st.error(f"Samples in metadata but not in counts: {', '.join(missing_in_counts)}")
                    elif extra_in_counts:
                        st.warning(f"Samples in counts but not in metadata: {', '.join(extra_in_counts)}")
                    else:
                        st.success("✅ All sample names match between metadata and counts.")
                        
                        metadata_save_path = Path("metadata") / metadata_file.name
                        Path("metadata").mkdir(parents=True, exist_ok=True)

                        with open(metadata_save_path, "wb") as f:
                            f.write(metadata_file.getbuffer())

                        st.info(f"Metadata file saved to: {metadata_save_path}")

                else:
                    st.warning("Counts matrix not found. Please run featureCounts first.")
        except Exception as e:
            st.error(f"Error loading metadata: {e}")

            
    st.markdown("---")
    
    st.subheader("Differential Analysis with PyDESeq-2")
    
    
    if st.button("Run Differential Analysis (External Script)"):
        Path("deseq_results").mkdir(exist_ok=True)
        result = subprocess.run(["bash", "-c", "module load gcc/12.4.0 && python3 run_deseq2.py"])


        if result.returncode == 0:
            st.success("DESeq2 analysis complete!")
            top_degs_path = Path("deseq_results/top_degs.csv")
            full_results_path = Path("deseq_results/full_results.csv")
            if top_degs_path.exists():
                top_degs = pd.read_csv(top_degs_path, index_col=0)
                st.session_state["top_degs"] = top_degs
                st.dataframe(top_degs)
            if full_results_path.exists():
                with open(full_results_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Full DESeq2 Results (CSV)",
                        data=f,
                        file_name="full_results.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("Top DEGs file not found.")
        else:
            st.error("Error running DESeq2.")
            st.code(result.stderr)
            
    top_degs_path = Path("deseq_results/top_degs.csv")
    full_results_path = Path("deseq_results/full_results.csv")
    if top_degs_path.exists():
        top_degs = pd.read_csv(top_degs_path, index_col=0)
        st.session_state["top_degs"] = top_degs
        st.dataframe(top_degs)
    else:
        st.warning("Top DEGs file not found.")
    if full_results_path.exists():
            with open(full_results_path, "rb") as f:
                st.download_button(
                    label="📥 Download Full DESeq2 Results (CSV)",
                    data=f,
                    file_name="full_results.csv",
                    mime="text/csv"
                )



if __name__ == "__main__":
    main()
