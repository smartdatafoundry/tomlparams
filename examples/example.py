import os
from xparams import XParams

defaults = {
    'locale': {
        'code': 'us',
        'utc_tzs': [-8, -7, -6, -5],
    },
    'banks': {
        'currency': 'usd',
        'has_depositor_insurance': True,
        'depositor_insurer': 'fdic',
        'account_types': ['current', 'savings', 'ira', 'roth_ira']
    },
    'demographics': {
        'age_range': ['18', '45'],
        'working_hours': ['ft', 'pt', 'none'],
        'benefits': {
            'pension': {
                'active': False,
                'types': ['state', 'private']
            },
            'income_support': {
                'active': True
            },
            'child_support': {
                'active': True
            }
        }
    }

}

if __name__ == '__main__':
    THISDIR = os.path.dirname(os.path.abspath(__file__))
    params_dir = os.path.join(THISDIR, 'in_params')
    output_toml = os.path.join(THISDIR, 'out_params', 'final.toml')
    # this should throw a warning of a type mismatch for demographics.benefits.pension.active
    config = XParams(
        defaults,
        base_params_stem='uk_retirees',
        user_params_dir=params_dir,
        check_types=XParams.WARN
    )

    config.write_consolidated_toml(output_toml)