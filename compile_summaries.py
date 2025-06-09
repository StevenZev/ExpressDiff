import pandas as pd
import re
import glob

# Read the trimming log
with open(glob.glob("trim_logs/*.out")[0]) as f:
    log = f.read()

# Updated regex pattern to include raw counts
pattern = re.compile(
    r"Processing file pair: .*?/(\S+)_1\.fq\.gz and .*?_2\.fq\.gz.*?"
    r"Input Read Pairs: (\d+) Both Surviving: (\d+) \(([\d.]+)%\) "
    r"Forward Only Surviving: \d+ \(([\d.]+)%\) "
    r"Reverse Only Surviving: \d+ \(([\d.]+)%\) "
    r"Dropped: \d+ \(([\d.]+)%\)",
    re.DOTALL
)

# Parse trimming log
data = []
for match in pattern.finditer(log):
    sample, input_pairs, both_count, both_pct, forward_pct, reverse_pct, dropped_pct = match.groups()
    data.append({
        "Sample": sample,
        "Input Read Pairs": int(input_pairs),
        "Both Surviving (count)": int(both_count),
        "Both Surviving %": float(both_pct),
        "Forward Only Surviving %": float(forward_pct),
        "Reverse Only Surviving %": float(reverse_pct),
        "Dropped %": float(dropped_pct)
    })

trim_data = pd.DataFrame(data)
trim_data["Sample"] = trim_data["Sample"].str[10:]
trim_data.index = trim_data.Sample
trim_data = trim_data.sort_index()

# Read featureCounts summary
map_data = pd.read_csv("featureCounts_out/counts.txt.summary", sep="\t", index_col=0)
map_data = map_data.T
#map_data['Total'] = map_data[:].sum(axis=1)
map_data = map_data[["Assigned"]]
map_data.index = map_data.index.str[9:].str[:-30]

# Merge and calculate mapping percentage
trim_map_data = pd.concat([trim_data, map_data.sort_index()], axis=1)
#trim_map_data["% Assigned"] = round(trim_map_data["Assigned"] / trim_map_data["Total"] * 100, 2)

# Output result
trim_map_data.to_csv("summary_matrix/trim_map_summary.csv")
