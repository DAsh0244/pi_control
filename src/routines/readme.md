# Routines
Put routines you will call via the yaml config files here.

Ensure that you add the routines to the `__init__.py` file.

## What are routines?
Routines are a sequence of [actions](../actions) combined that accomplish a task.
Many times an routine will want to be executed multiple times with different criteria.
These criteria are referred to as parameters, and are defined in the routine's [definition](#implementation-details).

## How are they used?
Routines are used in the `yaml` based configuration files that are used to define
global configurations and experimental procedures.

Basic syntax for use is:
```yaml
ROUTINES: &ROUTINES
  - !Routine
    name: reset_min
    units: raw
    actions:
      - !Action
          name: RESET_MIN
          params:
            low: *LIMIT_LOW
            high: *LIMIT_HIGH
      - !Action
          name: CLEANUP
```

## Implementation details:

Routines are implemented as python function calls. The convention is
- one routine in a module/file
- import said module into the `__init_.py` file
- you can now use the routine in your `yaml` configuration files via the `!Routine` directive
[docs]: ../../docs/routines.md

