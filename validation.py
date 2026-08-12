from typing import List, Tuple
from src.schemas import ReactionRecord, QualityMetrics, ChemicalRole


class QualityControlEngine:
    """Performs deterministic sanity checks and calculates quality metrics for extracted reaction records."""

    def evaluate_record(self, record: ReactionRecord) -> QualityMetrics:
        flags: List[str] = []

        # Metric 1: Provenance Completeness
        prov_score = self._verify_provenance(record, flags)

        # Metric 2: Chemical Validity
        chem_score = self._verify_chemistry(record, flags)

        # Metric 3: Stoichiometric Consistency
        stoich_score = self._verify_stoichiometry(record, flags)

        # Metric 4: Text Matching Verification
        text_score = self._verify_text_support(record, flags)

        # Aggregate Quality Score Calculation
        overall_score = (prov_score * 0.25) + (chem_score * 0.35) + (stoich_score * 0.25) + (text_score * 0.15)

        requires_review = overall_score < 7.0 or len(flags) > 0

        return QualityMetrics(
            provenance_completeness=round(prov_score, 2),
            chemical_validity=round(chem_score, 2),
            stoichiometric_consistency=round(stoich_score, 2),
            overall_score=round(overall_score, 2),
            validation_flags=flags,
            requires_human_review=requires_review
        )

    def _verify_provenance(self, record: ReactionRecord, flags: List[str]) -> float:
        total_entities = len(record.materials)
        if total_entities == 0:
            flags.append("NO_MATERIALS_EXTRACTED")
            return 0.0

        valid_provenance_count = sum(
            1 for m in record.materials if m.provenance and len(m.provenance.exact_quote) > 0
        )
        score = (valid_provenance_count / total_entities) * 10.0
        if score < 10.0:
            flags.append("MISSING_MATERIAL_PROVENANCE")
        return score

    def _verify_chemistry(self, record: ReactionRecord, flags: List[str]) -> float:
        if not record.materials:
            return 0.0

        has_substrate_or_reactant = any(
            m.role in [ChemicalRole.SUBSTRATE, ChemicalRole.REACTANT] for m in record.materials
        )
        has_product = any(m.role == ChemicalRole.PRODUCT for m in record.materials)

        score = 10.0
        if not has_substrate_or_reactant:
            flags.append("NO_SUBSTRATE_OR_REACTANT_IDENTIFIED")
            score -= 4.0
        if not has_product:
            flags.append("NO_PRODUCT_IDENTIFIED")
            score -= 4.0

        resolved_count = sum(1 for m in record.materials if m.canonical_smiles is not None)
        resolution_ratio = resolved_count / len(record.materials)
        score *= resolution_ratio

        return max(score, 0.0)

    def _verify_stoichiometry(self, record: ReactionRecord, flags: List[str]) -> float:
        """Verifies mass, molecular weight, and mole relations (Mass = MW * Moles)."""
        score = 10.0
        for mat in record.materials:
            if mat.mw and mat.mass and mat.moles and mat.mass.normalized and mat.moles.normalized:
                calculated_moles = mat.mass.normalized.si_value / mat.mw
                reported_moles = mat.moles.normalized.si_value

                # Check for >20% mismatch between reported mass/MW and moles
                if abs(calculated_moles - reported_moles) / max(reported_moles, 1e-6) > 0.2:
                    flags.append(f"STOICHIOMETRIC_MISMATCH_FOR_{mat.raw_name}")
                    score -= 3.0

        return max(score, 0.0)

    def _verify_text_support(self, record: ReactionRecord, flags: List[str]) -> float:
        """Validates that extracted verbatim quotes actually exist within source text."""
        source_text = record.procedure_text
        mismatches = 0
        total_quotes = 0

        for mat in record.materials:
            if mat.provenance and mat.provenance.exact_quote:
                total_quotes += 1
                if mat.provenance.exact_quote not in source_text:
                    mismatches += 1

        if total_quotes == 0:
            return 0.0

        if mismatches > 0:
            flags.append(f"VERBATIM_QUOTE_MISMATCH_COUNT_{mismatches}")

        return max(0.0, ((total_quotes - mismatches) / total_quotes) * 10.0)