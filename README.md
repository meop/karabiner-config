# About

Karabiner-Elements in a nice tool for overriding MacOS keyboard shortcuts.

My personal use-case is the desire to have more PC Style controls in place.

This project exists because the desktop UI is not very flexible for "Complex modifications":

- No easy editing of "Complex modifications" from the UI itself
- Include / exclude rules are per individual manipulator, not "group of" manipulators
- Modifiers are per key code, not "group of" key codes
- No simple way to just "reverse" modifiers but keep same key codes
- No convenience of appending "left_" to "to" modifier list
- No convenience of just simple key code rules, instead only array-based macro "to" key code rules

Enhancing the UI seems like a larger task.. but for now:

- this Python script can mutate the Karabiner config file
- Karabiner-Elements reloads the file at runtime automatically already!

## Requirements

Karabiner-Elements is installed and contains a named profile ready for modification.

This project only modifies an existing profile, does not create a new one.. for now.

## Usage

Edit complex.yml

Edit the top of mutator.py file to set config_profile_name if needed


Run:

```bash
uv run mutator.py
```

## Future

Make the system more portable.

Or one day help update the Karabiner-Elements UI??
