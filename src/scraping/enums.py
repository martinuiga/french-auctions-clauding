from enum import Enum


class Technology(Enum):
    WIND = "Wind"
    SOLAR = "Solar"
    HYDRO = "Hydro"
    THERMAL = "Thermal"

    @classmethod
    def from_string(cls, text: str) -> "Technology | None":
        aliases = {
            "wind": cls.WIND,
            "eolien": cls.WIND,
            "eolien onshore": cls.WIND,
            "eolien offshore": cls.WIND,
            "solar": cls.SOLAR,
            "solaire": cls.SOLAR,
            "hydro": cls.HYDRO,
            "hydraulique": cls.HYDRO,
            "thermal": cls.THERMAL,
            "thermique": cls.THERMAL,
        }
        text_lower = text.lower().strip()

        if text_lower in aliases:
            return aliases[text_lower]

        for key, tech in aliases.items():
            if key in text_lower:
                return tech

        return None


class Region(Enum):
    AUVERGNE_RHONE_ALPES = "Auvergne-Rhône-Alpes"
    BOURGOGNE_FRANCHE_COMTE = "Bourgogne-Franche-Comté"
    BRETAGNE = "Bretagne"
    CENTRE_VAL_DE_LOIRE = "Centre-Val de Loire"
    CORSE = "Corse"
    GRAND_EST = "Grand Est"
    HAUTS_DE_FRANCE = "Hauts-de-France"
    ILE_DE_FRANCE = "Île-de-France"
    NORMANDIE = "Normandie"
    NOUVELLE_AQUITAINE = "Nouvelle-Aquitaine"
    OCCITANIE = "Occitanie"
    PAYS_DE_LA_LOIRE = "Pays de la Loire"
    PROVENCE_ALPES_COTE_DAZUR = "Provence-Alpes-Côte d'Azur"

    @classmethod
    def from_string(cls, text: str) -> "Region | None":
        text_lower = text.lower().strip()

        for region in cls:
            if region.value.lower() in text_lower or text_lower in region.value.lower():
                return region

        return None
