# Flat state income tax rate lookup by two-letter US state abbreviation — V1 approximation; full bracket tables are a V2 refinement.
# States with no income tax are 0.0. Rates are rough effective approximations for a ~$80k income.
from decimal import Decimal

STATE_TAX_RATES = {
    'AL': Decimal('0.05'),  'AK': Decimal('0.00'),  'AZ': Decimal('0.025'),
    'AR': Decimal('0.049'), 'CA': Decimal('0.093'), 'CO': Decimal('0.044'),
    'CT': Decimal('0.05'),  'DE': Decimal('0.066'), 'FL': Decimal('0.00'),
    'GA': Decimal('0.0549'),'HI': Decimal('0.079'), 'ID': Decimal('0.058'),
    'IL': Decimal('0.0495'),'IN': Decimal('0.0305'),'IA': Decimal('0.057'),
    'KS': Decimal('0.057'), 'KY': Decimal('0.04'),  'LA': Decimal('0.0425'),
    'ME': Decimal('0.0715'),'MD': Decimal('0.0475'),'MA': Decimal('0.05'),
    'MI': Decimal('0.0425'),'MN': Decimal('0.0785'),'MS': Decimal('0.047'),
    'MO': Decimal('0.048'), 'MT': Decimal('0.059'), 'NE': Decimal('0.0584'),
    'NV': Decimal('0.00'),  'NH': Decimal('0.00'),  'NJ': Decimal('0.0637'),
    'NM': Decimal('0.049'), 'NY': Decimal('0.0685'),'NC': Decimal('0.045'),
    'ND': Decimal('0.0204'),'OH': Decimal('0.0275'),'OK': Decimal('0.0475'),
    'OR': Decimal('0.0875'),'PA': Decimal('0.0307'),'RI': Decimal('0.0475'),
    'SC': Decimal('0.064'), 'SD': Decimal('0.00'),  'TN': Decimal('0.00'),
    'TX': Decimal('0.00'),  'UT': Decimal('0.0465'),'VT': Decimal('0.066'),
    'VA': Decimal('0.0575'),'WA': Decimal('0.00'),  'WV': Decimal('0.051'),
    'WI': Decimal('0.053'), 'WY': Decimal('0.00'),  'DC': Decimal('0.085'),
}


def rate_for(state: str) -> Decimal:
    return STATE_TAX_RATES.get((state or '').upper(), Decimal('0.05'))
