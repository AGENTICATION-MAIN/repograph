"""
Bilateral Negotiation Coordinator for Pactum.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

from pactum.bargaining.nash import NashBargainingSolver
from pactum.bargaining.pareto import ParetoValidator
from pactum.core.exceptions import BargainingError, NoMutuallyBeneficialTradeError
from pactum.core.types import BargainingAgreement, BarterOffer
from pactum.resources.capability import CapabilityVault

logger = logging.getLogger("pactum.negotiation")


class NegotiationCoordinator:
    """
    Coordinates bilateral negotiation sessions between trading peers.
    """

    def __init__(self, solver: Optional[NashBargainingSolver] = None):
        self.solver = solver or NashBargainingSolver()
        self._lock = threading.RLock()
        self._agreements: Dict[str, BargainingAgreement] = {}

    def negotiate(
        self,
        offer_a: BarterOffer,
        offer_b: BarterOffer,
        vault_a: CapabilityVault,
        vault_b: CapabilityVault,
    ) -> BargainingAgreement:
        """
        Executes bilateral bargaining negotiation between party A and party B:
        1. Queries available capacity from vaults.
        2. Solves for Nash Bargaining Equilibrium.
        3. Validates Pareto optimality.
        4. Returns ratified BargainingAgreement.
        """
        with self._lock:
            avail_a = vault_a.get_available_quantity(offer_a.offered_resource_type)
            avail_b = vault_b.get_available_quantity(offer_b.offered_resource_type)

            agreement = self.solver.solve(
                offer_a=offer_a,
                offer_b=offer_b,
                available_cap_a=avail_a,
                available_cap_b=avail_b,
            )

            # Validate Pareto optimality
            is_pareto, welfare = ParetoValidator.verify_pareto_optimality(
                agreement=agreement,
                u_a=offer_a.proposer_utility_profile,
                u_b=offer_b.proposer_utility_profile,
                max_q_a=avail_a,
                max_q_b=avail_b,
            )
            agreement.is_pareto_optimal = is_pareto

            self._agreements[agreement.agreement_id] = agreement
            return agreement

    def get_agreement(self, agreement_id: str) -> Optional[BargainingAgreement]:
        with self._lock:
            return self._agreements.get(agreement_id)

    def list_agreements(self) -> List[BargainingAgreement]:
        with self._lock:
            return list(self._agreements.values())
