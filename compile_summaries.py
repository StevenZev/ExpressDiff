import pandas as pd
import re
import glob
from pathlib import Path

log_files = sorted(glob.glob("trim_logs/*.out"))
trim_pattern = re.compile(
    r"^\[START\] Trimming\s+(\S+).*?"
    r"Input Read Pairs:\s+(\d+)\s+"
    r"Both Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Forward Only Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Reverse Only Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Dropped:\s+(\d+)\s+\(([\d.]+)%\)",
    re.MULTILINE | re.DOTALL
)

trim_records = []
for f in log_files:
    txt = Path(f).read_text()
    for m in trim_pattern.finditer(txt):
        sample, total_pairs, both_cnt, both_pct, fwd_cnt, fwd_pct, rev_cnt, rev_pct, drop_cnt, drop_pct = m.groups()
        trim_records.append({
            "Sample": sample,
            "Total Pairs": int(total_pairs),
            "Both Surviving (count)": int(both_cnt),
            "Both Surviving (%)": float(both_pct),
            "Forward Only (count)": int(fwd_cnt),
            "Forward Only (%)": float(fwd_pct),
            "Reverse Only (count)": int(rev_cnt),
            "Reverse Only (%)": float(rev_pct),
            "Dropped (count)": int(drop_cnt),
            "Dropped (%)": float(drop_pct),
        })

trim_stats = pd.DataFrame.from_records(trim_records).set_index("Sample").sort_index()

star_files = sorted(glob.glob("STAR_out/*_Log.final.out"))
star_records = []
for f in star_files:
    txt = Path(f).read_text()
    sample = Path(f).name.replace("_Log.final.out", "")
    avg_in = re.search(r"Average input read length\s*\|\s*(\d+)", txt)
    uniq_num = re.search(r"Uniquely mapped reads number\s*\|\s*(\d+)", txt)
    uniq_pct = re.search(r"Uniquely mapped reads %\s*\|\s*([\d.]+)%", txt)
    avg_map = re.search(r"Average mapped length\s*\|\s*([\d.]+)", txt)
    sp_total = re.search(r"Number of splices: Total\s*\|\s*(\d+)", txt)
    multi = re.search(r"Number of reads mapped to multiple loci\s*\|\s*(\d+)", txt)
    too_many = re.search(r"Number of reads mapped to too many loci\s*\|\s*(\d+)", txt)
    unm_mis = re.search(r"Number of reads unmapped: too many mismatches\s*\|\s*(\d+)", txt)
    unm_short = re.search(r"Number of reads unmapped: too short\s*\|\s*(\d+)", txt)
    unm_other = re.search(r"Number of reads unmapped: other\s*\|\s*(\d+)", txt)
    chimeric = re.search(r"Number of chimeric reads\s*\|\s*(\d+)", txt)

    star_records.append({
        "Sample": sample,
        "Average Input Read Length": int(avg_in.group(1)) if avg_in else None,
        "Uniquely Mapped Reads Number": int(uniq_num.group(1)) if uniq_num else None,
        "Uniquely Mapped (%)": float(uniq_pct.group(1)) if uniq_pct else None,
        "Average Mapped Length": float(avg_map.group(1)) if avg_map else None,
        "Splices Total": int(sp_total.group(1)) if sp_total else None,
        "Multi-mapping Reads": int(multi.group(1)) if multi else None,
        "Too Many Loci Reads": int(too_many.group(1)) if too_many else None,
        "Unmapped: Mismatches": int(unm_mis.group(1)) if unm_mis else None,
        "Unmapped: Too Short": int(unm_short.group(1)) if unm_short else None,
        "Unmapped: Other": int(unm_other.group(1)) if unm_other else None,
        "Chimeric Reads": int(chimeric.group(1)) if chimeric else None
    })

star_stats = pd.DataFrame.from_records(star_records).set_index("Sample").sort_index()

full_stats = trim_stats.join(star_stats, how="outer")

summary_stats = full_stats.loc[:, [
    "Total Pairs",
    "Both Surviving (count)",
    "Both Surviving (%)",
    "Uniquely Mapped Reads Number",
    "Uniquely Mapped (%)"
]]

full_stats.to_csv("summary_matrix/full_trim_star_stats.csv")
summary_stats.to_csv("summary_matrix/trim_star_summary.csv")

print(full_stats.head())
print(summary_stats.head())




# Old code I don't want to delete yet...
'''import pandas as pd
import re
import glob
from pathlib import Path

log_files = sorted(glob.glob("trim_logs/*.out"))
pattern = re.compile(
    r"^\[START\] Trimming\s+(\S+).*?"
    r"Input Read Pairs:\s+(\d+)\s+"
    r"Both Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Forward Only Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Reverse Only Surviving:\s+(\d+)\s+\(([\d.]+)%\)\s+"
    r"Dropped:\s+(\d+)\s+\(([\d.]+)%\)",
    re.MULTILINE | re.DOTALL
)

records = []
for logfile in log_files:
    txt = Path(logfile).read_text()
    for m in pattern.finditer(txt):
        (
            sample,
            total_pairs,
            both_cnt, both_pct,
            fwd_cnt, fwd_pct,
            rev_cnt, rev_pct,
            drop_cnt, drop_pct
        ) = m.groups()

        records.append({
            "Sample": sample,
            "Total Pairs": int(total_pairs),
            "Both Surviving (count)": int(both_cnt),
            "Both Surviving (%)": float(both_pct),
            "Forward Only (count)": int(fwd_cnt),
            "Forward Only (%)": float(fwd_pct),
            "Reverse Only (count)": int(rev_cnt),
            "Reverse Only (%)": float(rev_pct),
            "Dropped (count)": int(drop_cnt),
            "Dropped (%)": float(drop_pct),
        })

full_stats = pd.DataFrame.from_records(records).set_index("Sample").sort_index()

map_df = (
    pd.read_csv("featureCounts_out/counts.txt.summary", sep="\t", index_col=0)
      .T[["Assigned"]]
      .rename(columns={"Assigned": "Mapped Reads"})
)

map_df.index = (
    map_df.index
      .str.replace(r"^.*?/", "", regex=True)
      .str.replace(r"_.*$", "", regex=True)
)

full_stats = full_stats.join(map_df, how="left")
full_stats["% Mapped"] = (full_stats["Mapped Reads"] / full_stats["Total Pairs"] * 100).round(2)

summary_stats = full_stats.loc[:, [
    "Total Pairs",
    "Both Surviving (count)",
    "Both Surviving (%)",
    "Mapped Reads",
    "% Mapped"
]]

full_stats.to_csv("summary_matrix/full_trim_map_stats.csv")
summary_stats.to_csv("summary_matrix/trim_map_summary.csv")

print(full_stats.head())
print(summary_stats.head())
'''