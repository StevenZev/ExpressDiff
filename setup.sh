python -m venv venv
source venv/bin/activate
pip install streamlit
pip install pydeseq2
python -m streamlit run expressdiff.py --server.maxUploadSize 1000000

