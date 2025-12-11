import copy
import json
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Helpers
def expand_project_path(input: str) -> Path:
  return Path(__file__).parent.parent / input


def expand_home_path(input: str) -> Path:
  return Path('~', input).expanduser()


# Constants
CONFIG_FILE_NAME = 'karabiner.json'
CONFIG_FILE_PATH = expand_home_path(f'.config/karabiner/{CONFIG_FILE_NAME}')
OUTPUT_FILE_PATHS = [
  CONFIG_FILE_PATH,
  expand_project_path(f'.output/{CONFIG_FILE_NAME}'),
]
KEYBOARD_IDENTIFIERS = {
  'arm64': {},
  'x86_64': {
    'product_id': 832,
    'vendor_id': 1452,
  },
}


# System validation
def validate_system() -> bool:
  checks = [
    (platform.system(), {'Darwin'}),
    (platform.machine(), {'arm64', 'x86_64'}),
  ]

  for actual, supported in checks:
    if actual not in supported:
      print(f'This script is for {", ".join(supported)}, not: {actual}')
      return False

  return True


# I/O functions
def load_karabiner_config() -> Optional[Dict[str, Any]]:
  try:
    with open(CONFIG_FILE_PATH) as _f:
      return json.load(_f)
  except FileNotFoundError:
    print(f'Error: Karabiner config file not found: {CONFIG_FILE_PATH}')
    return None
  except json.JSONDecodeError as e:
    print(f'Error parsing JSON file {CONFIG_FILE_PATH}: {e}')
    return None


def write_config_files(config: Dict[str, Any]) -> bool:
  karabiner_json = json.dumps(config, indent=2)

  for output_path in OUTPUT_FILE_PATHS:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
      with open(output_path, 'w') as _f:
        _f.write(karabiner_json)
      print(f'Successfully updated: {output_path}')
    except IOError as e:
      print(f'Error writing file {output_path}: {e}')
      return False

  return True


# Building blocks
def build_conditions(mod: Dict[str, Any]) -> List[Dict[str, Any]]:
  conditions = []
  for condition_type in ['include', 'exclude']:
    if condition_type in mod and mod[condition_type]:
      conditions.append(
        {
          'bundle_identifiers': mod[condition_type],
          'type': (
            'frontmost_application_if'
            if condition_type == 'include'
            else 'frontmost_application_unless'
          ),
        }
      )
  return conditions


def build_manipulator(
  conditions: List[Dict[str, Any]], from_: Dict[str, Any], to_: Dict[str, Any]
) -> Dict[str, Any]:
  if 'key_code' not in from_:
    raise ValueError('from_ must contain a valid key_code')

  to = (
    {'shell_command': to_['shell_command']}
    if 'shell_command' in to_
    else {
      'key_code': to_.get('key_code', from_['key_code']),
      'modifiers': to_.get('modifiers', []),
    }
  )

  return {
    'conditions': conditions,
    'from': {
      'key_code': from_['key_code'],
      'modifiers': from_.get('modifiers', {}),
    },
    'to': [to],
    'type': 'basic',
  }


def build_reverse_manipulator(manipulator: Dict[str, Any]) -> Dict[str, Any]:
  if 'to' not in manipulator or not manipulator['to']:
    raise ValueError('Manipulator must have valid "to" field')

  if 'mandatory' not in manipulator['from'].get('modifiers', {}):
    raise ValueError('Manipulator must have mandatory modifiers for reversal')

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


def build_simple_modification(mod: Dict[str, Any]) -> List[Dict[str, Any]]:
  from_config = mod['from']
  to_config = mod['to']

  mods = [{'from': from_config, 'to': [to_config]}]
  if mod.get('reverse'):
    mods.append({'from': to_config, 'to': [from_config]})

  return mods


def process_add_manipulators(
  manipulators: List[Dict[str, Any]],
  conditions: List[Dict[str, Any]],
  from_config: Dict[str, Any],
  to_config: Dict[str, Any],
  reverse: bool,
) -> None:
  m = build_manipulator(conditions, from_config, to_config)
  manipulators.append(m)
  if reverse:
    manipulators.append(build_reverse_manipulator(m))


# Processors
def process_modification_list(mods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  result = []
  for mod in mods:
    result.extend(build_simple_modification(mod))
  return result


def process_complex_modifications(profile_file: Dict[str, Any]) -> Dict[str, Any]:
  if 'complex_modifications' not in profile_file:
    return {}

  complex_mods = []
  for mod in profile_file['complex_modifications']:
    if 'manipulators' not in mod or not mod['manipulators']:
      continue

    conditions = build_conditions(mod)
    manipulators = []

    for manipulator in mod['manipulators']:
      from_config = manipulator['from']
      to_config = manipulator['to']
      reverse = manipulator.get('reverse', False)
      key_codes = manipulator.get('key_codes') or [None]

      for key_code in key_codes:
        from_cfg = from_config.copy()
        to_cfg = to_config.copy()
        if key_code:
          from_cfg['key_code'] = key_code
          to_cfg['key_code'] = key_code
        process_add_manipulators(manipulators, conditions, from_cfg, to_cfg, reverse)

    complex_mods.append(
      {'description': mod['description'], 'manipulators': manipulators}
    )

  return {'complex_modifications': {'rules': complex_mods}}


def process_simple_modifications(profile_file: Dict[str, Any]) -> Dict[str, Any]:
  if 'simple_modifications' not in profile_file:
    return {}

  return {
    'simple_modifications': process_modification_list(
      profile_file['simple_modifications']
    )
  }


def process_device_modifications(profile_file: Dict[str, Any]) -> Dict[str, Any]:
  if 'devices' not in profile_file:
    return {}

  device_mods = []
  for dev in profile_file['devices']:
    if 'simple_modifications' not in dev:
      continue

    device_mods.append(
      {
        'identifiers': {
          **dev['identifiers'],
          **KEYBOARD_IDENTIFIERS[platform.machine()],
        },
        'simple_modifications': process_modification_list(dev['simple_modifications']),
      }
    )

  return {'devices': device_mods}


# Profile management
def update_profile(
  config: Dict[str, Any], profile_name: str, profile_updates: Dict[str, Any]
) -> None:
  for p in config['profiles']:
    if p['name'] == profile_name:
      p.update(profile_updates)
      return

  print(f'Warning: Profile "{profile_name}" not found in config')


# Main orchestrator
def main() -> None:
  if not validate_system():
    return

  profiles_dir = expand_project_path('profiles')
  profile_files = list(profiles_dir.glob('*.yaml'))

  if not profile_files:
    print('No profile YAML files found')
    return

  config = load_karabiner_config()
  if not config:
    return

  for profile_path in profile_files:
    profile_name = profile_path.stem
    print(f'Processing profile: {profile_name}')

    try:
      with open(profile_path) as _f:
        profile_data = yaml.safe_load(_f)
    except yaml.YAMLError as e:
      print(f'Error parsing YAML file {profile_path}: {e}')
      return

    profile_updates = {}
    processors = [
      process_complex_modifications,
      process_simple_modifications,
      process_device_modifications,
    ]

    for processor in processors:
      result = processor(profile_data)
      if result:
        profile_updates.update(result)

    update_profile(config, profile_name, profile_updates)

  write_config_files(config)


if __name__ == '__main__':
  main()
