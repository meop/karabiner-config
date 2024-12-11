import json
import os

import yaml


output_file = '.output/karabiner.json'
config_file = '~/.config/karabiner/karabiner.json'
config_profile_name = 'default'

complex_mods_file = 'modifications/complex.yml'
simple_mods_file = 'modifications/simple.yml'


with open(complex_mods_file) as _f:
  complex_mods = yaml.load(_f.read(), Loader=yaml.Loader)


with open(simple_mods_file) as _f:
  simple_mods = yaml.load(_f.read(), Loader=yaml.Loader)


def _build_manipulator(conditions, from_, to_):
  if 'shell_command' in to_:
    to = {
      'shell_command': to_['shell_command'],
    }
  else:
    to = {
      'key_code': to_['key_code'] if 'key_code' in to_ else from_['key_code'],
      'modifiers': to_['modifiers'] if 'modifiers' in to_ else [],
    }

  manipulator = {
    'conditions': conditions,
    'from': {
      'key_code': from_['key_code'],
      'modifiers': from_['modifiers'] if 'modifiers' in from_ else {},
    },
    'to': [to],
    'type': 'basic',
  }
  return manipulator


_complex_mods = []
for mod in complex_mods:
  _manipulators = []
  if 'manipulators' not in mod or not mod['manipulators']:
    continue

  _conditions = []
  for _condition in ['include', 'exclude']:
    if _condition in mod and mod[_condition]:
      _conditions.append(
        {
          'bundle_identifiers': mod[_condition],
          'type': (
            'frontmost_application_if'
            if _condition == 'include'
            else 'frontmost_application_unless'
          ),
        }
      )

  for manipulator in mod['manipulators']:
    _from = manipulator['from']
    _to = manipulator['to']

    _pairs = [(_from, _to)]
    if 'reverse' in manipulator and manipulator['reverse']:
      _pairs.append((_to, _from))

    for _from, _to in _pairs:
      if 'key_codes' in manipulator and manipulator['key_codes']:
        for key_code in manipulator['key_codes']:
          _from['key_code'] = key_code
          _manipulators.append(_build_manipulator(_conditions, _from, _to))
      else:
        _manipulators.append(_build_manipulator(_conditions, _from, _to))

  _complex_mods.append(
    {'description': mod['description'], 'manipulators': _manipulators}
  )


_simple_mods = []
for mod in simple_mods:
  _simple_modifications = []
  if 'simple_modifications' not in mod or not mod['simple_modifications']:
    continue

  for simple_modification in mod['simple_modifications']:
    _from = simple_modification['from']
    _to = simple_modification['to']

    _pairs = [(_from, _to)]
    if 'reverse' in simple_modification and simple_modification['reverse']:
      _pairs.append((_to, _from))

    for _from, _to in _pairs:
      _simple_modifications.append({'from': _from, 'to': [_to]})

  _simple_mods.append(
    {
      'identifiers': mod['identifiers'],
      'simple_modifications': _simple_modifications,
    }
  )


config_file = os.path.expanduser(config_file)
with open(config_file) as _f:
  config = json.loads(_f.read())


def _find_device_modifications(device):
  if 'identifiers' not in device:
    return None

  for mod in _simple_mods:
    match = True
    for key, value in mod['identifiers'].items():
      if key not in device['identifiers'] or device['identifiers'][key] != value:
        match = False
    if match:
      return mod['simple_modifications']


for p in config['profiles']:
  if config_profile_name in p['name'].lower():
    p['complex_modifications']['rules'] = _complex_mods

    for device in p['devices']:
      modifications = _find_device_modifications(device)
      if not modifications:
        continue

      device['simple_modifications'] = modifications


karabiner_file = json.dumps(config, indent=4)

if not os.path.exists(os.path.dirname(output_file)):
  os.makedirs(os.path.dirname(output_file))

with open(output_file, 'w') as _f:
  _f.write(karabiner_file)

with open(config_file, 'w') as _f:
  _f.write(karabiner_file)
