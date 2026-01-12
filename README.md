# About

Karabiner-Elements in a nice tool for overriding MacOS keyboard shortcuts

My personal use-case is the desire to have more PC Style controls in place

This project mainly exists because the desktop UI is not very flexible, especially for "Complex modifications":

- No easy editing of "Complex modifications" from the UI itself
- Include / exclude rules are per individual manipulator, not "group of" manipulators
- Modifiers are per key code, not "group of" key codes
- No simple way to just "reverse" modifiers but keep same key codes
- No convenience of appending "left\_" to "to" modifier list
- No convenience of just simple key code rules, instead only array-based macro "to" key code rules

Enhancing the UI seems like a larger task.. but for now:

- this Python script can mutate the Karabiner config file
- Karabiner-Elements reloads the file at runtime automatically already!

## Prerequisites

Karabiner-Elements is installed and contains a named profile that matches a profile in this project

Usually this means renaming the default profile from "Default profile" to "Default"

Then you must create a dummy simple modification entry for any Apple keyboard devices in that profile

This will populate a device entry in the profile in the config file, which will be found and mutated by this script

## Usage

Edit any profiles you would like

Run:

```bash
uv run src/main.py
```

## Future

One day help simplify the Karabiner-Elements UI, so this project need not exist
