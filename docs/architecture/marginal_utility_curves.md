# Marginal Utility Curves & Urgency Functions

Pactum maps real-world software operational constraints to continuous, differentiable economic utility curves:

## 1. Logarithmic Concave Utility (Diminishing Marginal Returns)
$$U(x) = \alpha \cdot \ln(1 + \beta x)$$
- Used for API rate limits and memory allocations.
- Initial units provide massive utility (preventing HTTP 429 errors); subsequent units provide diminishing marginal value.

## 2. Exponential Urgency Profile (SLA Deadlines)
$$U(x) = \alpha \cdot (1 - e^{-\beta x}) + d$$
- Used for priority queue slots and CPU burst credits where latency SLA thresholds create extreme non-linear urgency.

## 3. Opportunity Cost Function
$$c(q) = 0.01 \cdot \left( \frac{q}{\text{Cap}} \right) \cdot \alpha$$
- Models the slight opportunity cost of relinquishing unconsumed idle capacity.
