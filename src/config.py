# config.py

# Define formats for each tier or category
FORMATS = {
    "LC": "gen1lc",
    "ZU": "gen1uu",
    "PU": "gen1uu",
    "NU": "gen1uu",
    "UU": "gen1uu",
    "OU": "gen1ou",
    "Uber": "gen1ubers",
}

# Default format if tier not found
DEFAULT_FORMAT = "gen1ou"


def get_format(tier: str) -> str:
    """
    Returns the battle format string based on the tier.
    
    Args:
        tier (str): The tier name (e.g., 'OU', 'Uber', 'LC', etc.)
        
    Returns:
        str: Corresponding format string for battle simulator
    """
    return FORMATS.get(tier, DEFAULT_FORMAT)
