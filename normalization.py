import re
from typing import Optional
from pint import UnitRegistry
from src.schemas import ExtractedQuantity, NormalizedQuantity

ureg = UnitRegistry()


class QuantityNormalizer:
    @staticmethod
    def normalize_quantity(quantity_text: str) -> Optional[NormalizedQuantity]:
        """Converts raw quantity string into standardized Pint SI units."""
        if not quantity_text:
            return None

        try:
            # Parse text into magnitude and unit using regex
            match = re.match(r"([\d\.\,\-]+)\s*([a-zA-Z°%]+)", quantity_text.strip())
            if not match:
                return None

            val_str, unit_str = match.groups()
            val = float(val_str.replace(',', ''))

            # Map chemical unit variations
            unit_map = {
                "C": "degC", "°C": "degC", "h": "hour", "hr": "hour",
                "hrs": "hour", "min": "minute", "mins": "minute",
                "equiv": "dimensionless", "eq": "dimensionless"
            }
            clean_unit = unit_map.get(unit_str, unit_str)

            qty = val * ureg(clean_unit)

            # Base SI conversion
            if qty.dimensionality == ureg.gram.dimensionality:
                si_qty = qty.to(ureg.gram)
                si_unit = "g"
            elif qty.dimensionality == ureg.mole.dimensionality:
                si_qty = qty.to(ureg.mole)
                si_unit = "mol"
            elif qty.dimensionality == ureg.liter.dimensionality:
                si_qty = qty.to(ureg.liter)
                si_unit = "L"
            elif qty.dimensionality == ureg.degC.dimensionality:
                si_qty = qty.to(ureg.kelvin)
                si_unit = "K"
            elif qty.dimensionality == ureg.second.dimensionality:
                si_qty = qty.to(ureg.second)
                si_unit = "s"
            else:
                si_qty = qty
                si_unit = str(qty.units)

            return NormalizedQuantity(
                value=val,
                unit=unit_str,
                si_value=float(si_qty.magnitude),
                si_unit=si_unit
            )
        except Exception:
            return None