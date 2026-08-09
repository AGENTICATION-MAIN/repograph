# Cryptographic Merkle Provenance Ledger

AegisKernel maintains an append-only Merkle DAG where every evaluated intent is recorded as a leaf node.

## Mathematical Formulation

1. **Leaf Hashing**:
   $$L_i = \text{SHA-256}(\text{CanonicalJSON}(\text{Index}_i, \text{IntentHash}_i, \text{Decision}_i, \text{PrevHash}_{i-1}))$$

2. **Node Pairing**:
   $$N_{\text{parent}} = \text{SHA-256}(N_{\text{left}} \parallel N_{\text{right}})$$

3. **Inclusion Proofs**:
   For any record at index $k$, AegisKernel extracts the sibling hashes along the logarithmic path to the root. An auditor can verify inclusion in $O(\log N)$ time without inspecting any other ledger records.
