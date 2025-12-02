import copy
import json
import os

import yaml


profile_name = 'Default'
output_file = '.output/karabiner.json'
config_file = '~/.config/karabiner/karabiner.json'

with open(f'profiles/{profile_name}.yaml') as _f:
  profile_file = yaml.load(_f.read(), Loader=yaml.Loader)


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


def _build_reverse_manipulator(manipulator):
  reverse_manipulator = copy.deepcopy(manipulator)
  reverse_manipulator['from']['key_code'] = manipulator['to'][0]['key_code']
  reverse_manipulator['from']['modifiers']['mandatory'] = manipulator['to'][0][
    'modifiers'
  ]

  reverse_manipulator['to'][0]['key_code'] = manipulator['from']['key_code']
  reverse_manipulator['to'][0]['modifiers'] = manipulator['from']['modifiers'][
    'mandatory'
  ]

  return reverse_manipulator


profile = {}

if 'complex_modifications' in profile_file:
  _complex_mods = []
  for mod in profile_file['complex_modifications']:
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

      if 'key_codes' in manipulator and manipulator['key_codes']:
        for key_code in manipulator['key_codes']:
          _from['key_code'] = key_code
          _to['key_code'] = key_code
          _m = _build_manipulator(_conditions, _from, _to)
          _manipulators.append(_m)
          if 'reverse' in manipulator and manipulator['reverse']:
            _manipulators.append(_build_reverse_manipulator(_m))
      else:
        _m = _build_manipulator(_conditions, _from, _to)
        _manipulators.append(_m)
        if 'reverse' in manipulator and manipulator['reverse']:
          _manipulators.append(_build_reverse_manipulator(_m))

    _complex_mods.append(
      {'description': mod['description'], 'manipulators': _manipulators}
    )
  profile['complex_modifications'] = {'rules': _complex_mods}

if 'simple_modifications' in profile_file:
  _simple_mods = []
  for mod in profile_file['simple_modifications']:
    _from = mod['from']
    _to = mod['to']

    _simple_mods.append({'from': _from, 'to': [_to]})
    if 'reverse' in mod and mod['reverse']:
      _simple_mods.append({'from': _to, 'to': [_from]})
  profile['simple_modifications'] = _simple_mods

if 'devices' in profile_file:
  _device_mods = []
  for dev in profile_file['devices']:
    if 'simple_modifications' in dev:
      _simple_mods = []
      for mod in dev['simple_modifications']:
        _from = mod['from']
        _to = mod['to']

        _simple_mods.append({'from': _from, 'to': [_to]})
        if 'reverse' in mod and mod['reverse']:
          _simple_mods.append({'from': _to, 'to': [_from]})
      _device_mods.append(
        {'identifiers': dev['identifiers'], 'simple_modifications': _simple_mods}
      )
  profile['devices'] = _device_mods


config_file = os.path.expanduser(config_file)
with open(config_file) as _f:
  config = json.loads(_f.read())

for p in config['profiles']:
  if p['name'] == profile_name:
    if 'complex_modifications' in profile:
      p['complex_modifications'] = profile['complex_modifications']
    if 'simple_modifications' in profile:
      p['simple_modifications'] = profile['simple_modifications']
    if 'devices' in profile:
      p['devices'] = profile['devices']

karabiner_file = json.dumps(config, indent=4)

if not os.path.exists(os.path.dirname(output_file)):
  os.makedirs(os.path.dirname(output_file))

with open(output_file, 'w') as _f:
  _f.write(karabiner_file)

with open(config_file, 'w') as _f:
  _f.write(karabiner_file)
