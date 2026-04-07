# helpers related to profiles

COUNTRY_CURRENCY_MAP = {
    "Nigeria": "NGN",
    "United States": "USD",
    "United Kingdom": "GBP",
    "European Union": "EUR",
    "India": "INR",
    "Canada": "CAD",
    "Australia": "AUD",
    "South Africa": "ZAR",
    "Mexico": "MXN",
    "Brazil": "BRL",
    "Italy": "EUR",
    "Germany": "EUR",
    "FRANCE": "EUR",
    "Argentina": "ARS",
    "Japan": "JPY",
    "China": "CNY",
    "Ghana": "GHS",
    "Peru": "PEN",
    "Nepal": "NPR", 
    "Egypt": "EGP",
    # extend as needed
}


def currency_for_nationality(nationality: str) -> str | None:
    """Return a default currency code for a given nationality/country code.
    Nationality may come in as full country name or ISO code; this helper
    uses a simple lookup and uppercases the input. Extend mapping for more countries.
    """
    if not nationality:
        return None
    key = nationality.strip().upper()
    return COUNTRY_CURRENCY_MAP.get(key)
