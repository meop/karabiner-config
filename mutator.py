import json
import os

import yaml


config_file = "~/.config/karabiner/karabiner.json"
config_profile_name = "pc style"

complex_rules_file = "complex_rules.yml"
device_rules_file = "device_rules.yml"


with open(complex_rules_file) as _f:
    complex_rules = yaml.load(_f.read(), Loader=yaml.Loader)


with open(device_rules_file) as _f:
    device_rules = yaml.load(_f.read(), Loader=yaml.Loader)


def _safe_prefix(input, prefix):
    return input if input.startswith(prefix) else prefix + input


def _get_modifiers(input, outbound=False):
    modifiers = []
    if "modifiers" in input and input["modifiers"]:
        for modifier in input["modifiers"]:
            modifiers.append(modifier)
    if outbound:
        for i in range(0, len(modifiers)):
            modifiers[i] = _safe_prefix(modifiers[i], "left_")
    return modifiers


def _build_manipulator(conditions, from_, to_):
    if "shell_command" in to_:
        to = {
            "shell_command": to_["shell_command"],
        }
    else:
        to = {
            "key_code": to_["key_code"] if "key_code" in to_ else from_["key_code"],
            "modifiers": _get_modifiers(to_, outbound=True),
        }

    manipulator = {
        "conditions": conditions,
        "from": {
            "key_code": from_["key_code"],
            "modifiers": {
                "mandatory": _get_modifiers(from_),
            },
        },
        "to": [to],
        "type": "basic",
    }
    return manipulator


_complex_rules = []
for rule in complex_rules:
    _manipulators = []
    if "manipulators" not in rule or not rule["manipulators"]:
        continue

    _conditions = []
    for _condition in ["include", "exclude"]:
        if _condition in rule and rule[_condition]:
            _conditions.append(
                {
                    "bundle_identifiers": rule[_condition],
                    "type": (
                        "frontmost_application_if"
                        if _condition == "include"
                        else "frontmost_application_unless"
                    ),
                }
            )

    for manipulator in rule["manipulators"]:
        _from = manipulator["from"]
        _to = manipulator["to"]

        _pairs = [(_from, _to)]
        if "reverse" in manipulator and manipulator["reverse"]:
            _pairs.append((_to, _from))

        for _from, _to in _pairs:
            if "key_codes" in manipulator and manipulator["key_codes"]:
                for key_code in manipulator["key_codes"]:
                    _from["key_code"] = key_code
                    _manipulators.append(_build_manipulator(_conditions, _from, _to))
            else:
                _manipulators.append(_build_manipulator(_conditions, _from, _to))

    _complex_rules.append(
        {"description": rule["description"], "manipulators": _manipulators}
    )


_device_rules = []
for rule in device_rules:
    _simple_modifications = []
    if "simple_modifications" not in rule or not rule["simple_modifications"]:
        continue

    for simple_modification in rule["simple_modifications"]:
        _from = simple_modification["from"]
        _to = simple_modification["to"]

        _pairs = [(_from, _to)]
        if "reverse" in simple_modification and simple_modification["reverse"]:
            _pairs.append((_to, _from))

        for _from, _to in _pairs:
            _simple_modifications.append({
                "from": _from,
                "to": [_to]
            })

    _device_rules.append(
        {
            "identifiers": rule["identifiers"],
            "simple_modifications": _simple_modifications,
        }
    )


config_file = os.path.expanduser(config_file)
with open(config_file) as _f:
    config = json.loads(_f.read())


def _find_device_modifications(device):
    if "identifiers" not in device:
        return None

    for device_rule in _device_rules:
        match = True
        for key, value in device_rule["identifiers"].items():
            if (
                key not in device["identifiers"] or
                device["identifiers"][key] != value
            ):
                match = False
        if match:
            return device_rule["simple_modifications"]


for p in config["profiles"]:
    if config_profile_name in p["name"].lower():
        p["complex_modifications"]["rules"] = _complex_rules

        for device in p["devices"]:
            modifications = _find_device_modifications(device)
            if not modifications:
                continue

            device["simple_modifications"] = modifications


with open(config_file, "w") as _f:
    _f.write(json.dumps(config, indent=4))
