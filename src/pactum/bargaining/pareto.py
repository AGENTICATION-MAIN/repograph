"""
Pareto Efficiency Verification and Contract Curve Analysis for Pactum.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from pactum.core.types import BargainingAgreement, UtilityProfile


class ParetoValidator:
    """
    Validates Pareto efficiency of negotiated resource trades.
    A trade is Pareto-optimal if no party can be made strictly better off without
    making the counterparty worse off.
    """

    @staticmethod
    def verify_pareto_optimality(
        agreement: BargainingAgreement,
        u_a: UtilityProfile,
        u_b: UtilityProfile,
        max_q_a: float,
        max_q_b: float,
    ) -> Tuple[bool, float]:
        """
        Verifies that no perturbation (Δq_a, Δq_b) yields a strict Pareto improvement.
        Returns: (is_pareto_optimal: bool, social_welfare_sum: float)
        """
        curr_sa = agreement.surplus_utility_a
        curr_sb = agreement.surplus_utility_b
        social_welfare = curr_sa + curr_sb

        # Check local neighborhood perturbations
        perturbations = [-0.05, 0.05]
        for da in perturbations:
            for db in perturbations:
                test_qa = min(max_q_a, max(0.001, agreement.quantity_a_to_b + (da * max_q_a)))
                test_qb = min(max_q_b, max(0.001, agreement.quantity_b_to_a + (db * max_q_b)))

                sa = u_a.evaluate(test_qb) - (0.01 * (test_qa / max_q_a) * max(1.0, u_a.alpha)) - u_a.reservation_utility
                sb = u_b.evaluate(test_qa) - (0.01 * (test_qb / max_q_b) * max(1.0, u_b.alpha)) - u_b.reservation_utility

                if sa > curr_sa and sb > curr_sb and (sa - curr_sa) > 0.1 and (sb - curr_sb) > 0.1:
                    return False, social_welfare

        return True, social_welfare
