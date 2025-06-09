# run_deseq2.py
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats

counts_df = pd.read_csv("counts_matrix/deseq_counts_matrix.csv", index_col=0).T
metadata = pd.read_csv("metadata/metadata.csv", index_col=0)

dds = DeseqDataSet(
    counts=counts_df,
    metadata=metadata,
    design="~condition",
    refit_cooks=True
)

dds.deseq2()

ds = DeseqStats(dds, contrast=["condition", "b", "a"])
ds.summary()

results_df = ds.results_df
results_df.to_csv("deseq_results/full_results.csv")

degs = results_df.dropna(subset=["padj"]).copy()
degs = degs[(degs["padj"] < 0.05) & (abs(degs["log2FoldChange"]) > 1)]
degs.sort_values("padj").head(15).to_csv("deseq_results/top_degs.csv")
