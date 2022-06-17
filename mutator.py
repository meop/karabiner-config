import json
import os

import yaml

complex_rules_file = "complex_rules.yml"
config_file = "~/.config/karabiner/karabiner.json"
config_profile_name = "pc style"

with open(complex_rules_file) as _f:
    desired_rules = yaml.load(_f.read(), Loader=yaml.Loader)


def _safe_prefix(input, prefix):
    return (
        input
        if input.startswith(prefix)
        else prefix + input
    )


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


_rules = []
for rule in desired_rules:
    _manipulators = []
    if not "manipulators" in rule or not rule["manipulators"]:
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

    _rules.append({"description": rule["description"], "manipulators": _manipulators})


config_file = os.path.expanduser(config_file)
with open(config_file) as _f:
    config = json.loads(_f.read())

for p in config["profiles"]:
    if config_profile_name in p["name"].lower():
        p["complex_modifications"]["rules"] = _rules

with open(config_file, "w") as _f:
    _f.write(json.dumps(config, indent=4))
