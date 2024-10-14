# Illustates the first example from the README.md page
# Should work if run from the directory containing this file
# in the tomlparams repo.


from datetime import date, datetime

from tomlparams import TOMLParams

defaults = {
    'start_date': date(2024, 1, 1),
    'run_days': 366,
    'tolerance': 0.0001,
    'log': True,
    'locale': 'en_GB',
    'critical_event_time': datetime(2024, 7, 31, 3, 22, 22),
    'logging': {'format': '.csv', 'events': ['financial', 'telecoms']},
}


params = TOMLParams(defaults=defaults, name='defaults')

print(repr(params.run_days))  # type: ignore [attr-defined]
print(repr(params['start_date']))
print(repr(params.logging.format))  # type: ignore [attr-defined]
print(repr(params['logging']['events']))

params.write_consolidated_toml('defaults.toml')
