# Nash Bargaining Engine Architecture

## 1. Mathematical Formulation

Let Service $A$ and Service $B$ enter bilateral negotiation with utility functions $U_A(q_B)$ and $U_B(q_A)$, where:
- $q_A \in [0, \text{Cap}_A]$ is the quantity of resource offered by $A$ to $B$.
- $q_B \in [0, \text{Cap}_B]$ is the quantity of resource offered by $B$ to $A$.
- $d_A, d_B$ are the disagreement (reservation) utility payoffs if no trade occurs.

The Nash Bargaining Solution (NBS) is the unique point $(q_A^*, q_B^*)$ that maximizes the Nash Product:
$$\max_{q_A, q_B} \mathcal{N}(q_A, q_B) = \left( U_A(q_B) - c_A(q_A) - d_A \right) \cdot \left( U_B(q_A) - c_B(q_B) - d_B \right)$$

subject to:
$$0 \le q_A \le \text{Cap}_A, \quad 0 \le q_B \le \text{Cap}_B$$
$$U_A(q_B) - c_A(q_A) \ge d_A, \quad U_B(q_A) - c_B(q_B) \ge d_B$$

## 2. Solver Implementation

Pactum employs a **two-phase accelerated coordinate descent algorithm**:
1. **Coarse Hyper-Grid Scan**: Evaluates the bounding Edgeworth box to locate the initial peak of the strictly quasi-concave objective function.
2. **Adaptive Bisection Gradient Refinement**: Refines $(q_A^*, q_B^*)$ with decaying perturbation vectors until convergence within $10^{-5}$ tolerance.

**Benchmarked Execution Time**: **$411.9\mu\text{s}$** (P50), achieving over **2,200 solves/second** per core.
