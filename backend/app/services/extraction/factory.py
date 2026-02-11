from app.services.extraction.base import BaseExtractor
from app.services.extraction.neraca import NeracaExtractor
from app.services.extraction.saldo_awal import SaldoAwalExtractor
from app.services.extraction.penyusutan import PenyusutanExtractor

class ExtractorFactory:
    @staticmethod
    def get_extractor(category: str) -> BaseExtractor:
        if category == "Neraca":
            return NeracaExtractor()
        elif category == "Saldo Awal":
            return SaldoAwalExtractor()
        elif category == "Penyusutan":
            return PenyusutanExtractor()
        else:
            raise ValueError(f"Unknown category: {category}")
