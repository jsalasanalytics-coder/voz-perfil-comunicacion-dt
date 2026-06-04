import os

# Evita warnings y contención de hilos de tokenizers de HuggingFace.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# Numba/UMAP (usado por BERTopic) no es thread-safe; además serializamos el
# cómputo pesado con un lock en profile.py.
os.environ.setdefault("NUMBA_THREADING_LAYER", "workqueue")
