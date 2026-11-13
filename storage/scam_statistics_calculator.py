"""ScamStatisticsCalculator: summary numbers for a list of ScamRecords."""

import phonenumbers
from phonenumbers import geocoder

from app.models.record import Record

class ScamStatisticsCalculator:
    """Calculates percentages and most-common results.
 
    It never opens a file. It is given a list of Record objects, works on
    them, and gives back numbers. It does not keep the records afterwards
    (association: it uses ScamRecords without owning them).
    """

    def __init__(self, decimal_places: int = 2) -> None:
        # How many decimal places percentages are rounded to (Phase 1 used 2).
        self._decimal_places = decimal_places
 
    # ------------------------------------------------------------------
    # Main method: the summary used by io_manager.print_message_summary()
    # ------------------------------------------------------------------

    def summary(self, records: list[Record]) -> dict:
        """Return the summary dictionary with the same keys as Phase 1."""
        risk_counts = self.count_by(records, "risk_level")
        scam_counts = self.count_by(records, "scam_type")
        origin_counts = self.count_by(records, "country_code")
 
        most_common_scam = self.most_common(records, "scam_type")
 
        labels = {}
        for country_code in origin_counts:
            labels[country_code] = self.country_label(country_code)
 
        return {
            "total_messages": len(records),
            "risk_level_breakdown": risk_counts,
            "scam_category_breakdown": scam_counts,
            "origin_country_breakdown": origin_counts,
            "risk_level_percentage": self.percentages(risk_counts),
            "scam_category_percentage": self.percentages(scam_counts),
            "origin_country_percentage": self.percentages(origin_counts),
            "most_common_scam": most_common_scam[0] if most_common_scam else "Unknown",
            "most_common_scam_percentage": most_common_scam,
            "most_common_origin": self.most_common(records, "country_code"),
            "origin_country_labels": labels,
        }

   # ------------------------------------------------------------------
    # Building blocks (each one can be tested on its own)
    # ------------------------------------------------------------------
 
    @staticmethod
    def count_by(records: list[Record], field: str) -> dict[str, int]:
        """Count how many records have each value of `field`.
 
        e.g. count_by(records, "risk_level") -> {"HIGH": 3, "LOW": 1}
        Empty values are counted as "Unknown". Anything that is not a
        Record is ignored.
        """
        counts: dict[str, int] = {}
        for record in records:
            if not isinstance(record, Record):
                continue
            value = getattr(record, field)
            if not isinstance(value, str) or value.strip() == "":
                value = "Unknown"
            else:
                value = value.strip()
            counts[value] = counts.get(value, 0) + 1
        return counts
 
    def percentages(self, counts: dict[str, int]) -> dict[str, float]:
        """Turn counts into percentages of the total.
 
        e.g. {"A": 3, "B": 1} -> {"A": 75.0, "B": 25.0}
        """
        total = sum(counts.values())
        if total == 0:
            return {}
 
        result: dict[str, float] = {}
        for name, count in counts.items():
            result[name] = round(count / total * 100, self._decimal_places)
        return result
 
    def most_common(self, records: list[Record], field: str) -> tuple[str, float] | None:
        """Return (value, percentage) for the most common value of `field`.
 
        e.g. ("Phishing", 50.0). Ties are broken alphabetically, so the result
        is the same every run. Returns None when there are no records.
        """
        percentages = self.percentages(self.count_by(records, field))
        if not percentages:
            return None
 
        top_name = ""
        top_percent = -1.0
        for name in sorted(percentages):
            if percentages[name] > top_percent:
                top_name = name
                top_percent = percentages[name]
        return top_name, top_percent
 
    # ------------------------------------------------------------------
    # Country names (for display labels)
    # ------------------------------------------------------------------
 
    @staticmethod
    def country_name(country_code: str) -> str:
        """Convert a calling code to its main country, e.g. "+65" -> "Singapore".
 
        Shared codes such as "+1" return the main country (United States).
        Returns "Unknown" if the code is not real.
        """
        if not isinstance(country_code, str) or not country_code.lstrip("+").isdigit():
            return "Unknown"
        region = phonenumbers.region_code_for_country_code(int(country_code.lstrip("+")))
        example = phonenumbers.example_number(region)
        if example is None:
            return "Unknown"
        return geocoder.country_name_for_number(example, "en") or "Unknown"
 
    def country_label(self, country_code: str) -> str:
        """Return the code with its country, e.g. "+65" -> "+65 (Singapore)"."""
        return f"{country_code} ({self.country_name(country_code)})"