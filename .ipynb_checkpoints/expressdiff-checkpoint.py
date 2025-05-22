import streamlit as st
from pathlib import Path
import os

import subprocess
import shutil


#st.set_page_config(layout="wide")
st.set_page_config(layout="centered")

# Define the target directory for saving uploaded files
RAW_READS_DIR = Path("raw_reads")
RAW_READS_DIR.mkdir(parents=True, exist_ok=True)


done_flag = Path("qc_logs/fastqc_multiqc_done.flag")


def main():
    st.title("RNA-seq Adapter Selection and Report Viewer")

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

    # Show current files in /raw_reads
    st.subheader(".fq.gz files in raw_reads folder:")
    raw_files = sorted(RAW_READS_DIR.glob("*.fq.gz"))
    if raw_files:
        for f in raw_files:
            st.write(f"- {f.name}")
    else:
        st.info("No files currently in /raw_reads")

    st.markdown("---")

    
    # Button to run initial QC
    if st.button("Run Initial QC"):
        script_path = Path("qc_raw.slurm")
        qc_logs_dir = Path("qc_logs")

        # Clean old logs (before job starts)
        if qc_logs_dir.exists():
            for file in qc_logs_dir.glob("*"):
                if file.is_file():
                    file.unlink()

        if script_path.exists():
            st.info("Submitting FastQC + MultiQC SLURM job...")
            result = subprocess.run(["sbatch", str(script_path)], capture_output=True, text=True)
            if result.returncode == 0:
                st.success(f"SLURM job submitted: {result.stdout.strip()}")
            else:
                st.error(f"Error submitting job: {result.stderr}")
        else:
            st.error(f"SLURM script not found at {script_path}")
    
    
    
    st.markdown("---")
    
    if st.button("Check QC Job Status"):
        if done_flag.exists():
            st.success("QC job completed successfully! ✅")
        else:
            st.info("QC job is still running or waiting to start.")
    

    st.markdown("---")
    

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
            result = subprocess.run(["sbatch", str(trimmomatic_script)], capture_output=True, text=True)
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
                result = subprocess.run(["sbatch", str(slurm_script)], capture_output=True, text=True)
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
                result = subprocess.run(["sbatch", str(script_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success(f"featureCounts job submitted: {result.stdout.strip()}")
                else:
                    st.error(f"Error submitting job: {result.stderr}")
            else:
                st.error("SLURM script 'run_featureCounts.slurm' not found.")


                
    st.markdown("---")
    st.subheader("Check featureCounts Job Status")

    fc_done_flag = Path("featureCounts_logs/featurecounts_done.flag")
    if st.button("Check featureCounts Status"):
        if fc_done_flag.exists():
            st.success("featureCounts job completed successfully! ✅")
        else:
            st.info("featureCounts job is still running or hasn't started.")

    st.markdown("**featureCounts Output Preview:**")
    counts_file = Path("featureCounts_out/counts.txt.summary")
    if counts_file.exists():
        with open(counts_file) as f:
            lines = f.readlines()
            st.text("".join(lines[:20]))  # Show first 20 lines
    else:
        st.info("No output file found yet.")



if __name__ == "__main__":
    main()
