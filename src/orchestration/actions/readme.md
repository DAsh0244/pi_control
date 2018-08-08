# Actions
Put actions you will call via the [yaml][yaml] configuration files here.
They will be automatically found and added provided the module file name contains a function matching the same name.


## Overview

### What are Actions?
Actions are the basic unit of operation in a full procedure.
At their basis they are an optionally parametrized call to a function/method that accomplishes a small task.

For the more technically inclined they are a partial implementation of a finite state machine that is completed with actions, with the other half being accomplished by [routines](../routines/readme.md). While actions can be likened to states, routines are analogous to transition tables.

Examples of some actions are:

- Moving the actuator to a certain position
- Resetting actuator position
- Applying load up to an amount
- Waiting a certain amount of time

Many times an action will want to be executed multiple times with different criteria.
These criteria are referred to as parameters, and are defined in the routine's [definition](#implementation).

### How are they used?
Actions are used in the [yaml][yaml] based configuration files as a part of a [routine](../routines) container.

Basic syntax for use is:
```yaml
# would be defined in a configuration block
lower_limit: &LIMIT_LOW 0
upper_limit: &LIMIT_HIGH 20000

ROUTINES: &ROUTINES
  - !Routine
    name: reset_min
    units: raw
    actions:
      - !Action
          name: CLEANUP
      - !Action
          # name is the specific action to call
          name: RESET_MIN
          # dictionary of params to pass to the desired action
          params:
            low: *LIMIT_LOW
            high: *LIMIT_HIGH
      - !Action
      	  name: RESET_MAX
          params:
            low: *LIMIT_LOW
            high: *LIMIT_HIGH
    transistions:
      RESET_MAX:
        success: RESET_MIN
        error: ERR
      RESET_MIN:
        success: CLEANUP
        error: ERR
      CLEANUP:
        success: END
```

## Technical Details:
Procedures are implemented as asynchronous [finite state machines](https://en.wikipedia.org/wiki/Finite-state_machine). i.e. States are only changed when actions trigger a transition either upon completion or as specified. This implementation provides a very flexible and intuitive method of designing arbitrary procedures.


### Implementation

#### Basics:
Actions are implemented as python function calls. These are then passed to a master controller that executes a full procedure.

Conventions for actions are:

- One action per module/file
- Import said module into [\_\_init\_\_.py][init.py]
- You can now use the routine in your [yaml][yaml] configuration files via the `!Action` directive

All actions share a few elements in their declaration:

```python
def some_action(interface: obj, params: dict) -> str:
    """
    Action description

    :param interface: base interface abstraction layer that is performing an action.
    :param params: dictionary of the form
    	{'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
    """
    condition = None
    # stuff happens here -- eval and assign the desired value for condition
    ...

    return condition
```

As we can see, all actions return an end status `str` to be checked for the next state transition to be executed by the controller (should be the key to a mapping type object like a `dict`).
Internally the controller operates on a sentinel terminated sequence based approach that can be roughly visualized as the following:

```python
# initialize machine
current_action = Action
# run until sentinel is hit
# error cconditions generally break the loop by convention.
while current_action is not end_action:
	current_action = transition(current_action(), transistion_table)
```

For a more concrete example. Consider the following `cleanup` action:

```python
def cleanup(interface=None, params=None):
    """
    runs hal_cleanup() to safely reset pin configurations made over the course of usage.
    does not require any passed parameters.
    """
    hal_cleanup()
    return 'success'
```

This is the simplest `Action` that can exist. There is only a single possible exit status of `success` and no input parameters are needed. This can be called in a file as demonstrated below:

```yaml
!Action &CLEANUP
  name: CLEANUP
```

A more complicated `Action` is demonstrated with the `oscillate` action:

```python
def oscillate(interface=actuator, params=None):
    """
    Moves from thresholds described in params dict with keys of 'low_pos', 'high_pos'.
    Movement speed is optionally defined in params dict with the 'speed' key.
    Adaptive controller is optionally specified with the 'controller' key.
    The ability to end oscillation at the closest threshold (low or high) is available with the 'reset_closest' key,
        which expects a boolean True or False value. If not specified, defaults to False
    Mutually exclusive number of oscillations and timeout are also optional params. if both are specified,
    it will stop at whatever comes first.
        - timeout is specified with the 'timeout' key and expects a float, defaults to inf
        - repetitions is specified with the 'repetitions' key and expects an int, defaults to inf

    depending on the conditions, four possible return values are possible plus an error condition:
        - 'timeout_stopped'  - broke on a timeout and left actuator where it was
        - 'repeats_stopped'  - broke on a repeat and left actuator where it was
        - 'timeout_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'repeats_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'error'            - triggers on any failure during oscillations
    """
    condition = 'stopped'
    low_pos = params['low_pos']
    high_pos = params['high_pos']
    timeout = params.get('timeout', float('inf'))
    repetitions = params.get('repetitions', float('inf'))
    controller = params.get('controller', None)
    old_speed = interface.speed_controller.default_val
    speed = params.get('speed', interface.speed_controller.default_val)

    interface.speed_controller.default_val = speed
    interface.mount_controller(controller)
    repeats = 0
    start = perf_counter()
    try:
        while ((perf_counter() - start) < timeout) or (repeats < repetitions):
            interface.set_position(low_pos)
            interface.set_position(high_pos)
            repeats += 1
        if params.get('reset_closest', False):
            condition = 'reset'
            # is closer to lower spot than higher spot
            if abs(interface.position - low_pos) > abs(interface.position - high_pos):
                interface.set_position(low_pos)
            else:
                interface.set_position(high_pos)
        interface.speed_controller.default_val = old_speed
        return '_'.join(('timeout' if repeats < repetitions else 'repeats', condition))
    except Exception:
        interface.set_out_speed(interface.speed_controller.stop)
        interface.speed_controller.default_val = old_speed
        return 'error'
```

This `Action` can be used in the following manner:
```yaml
!Action
  name: oscillate
  params:
    low: *LIMIT_LOW
    high: *LIMIT_HIGH
    speed: 2048
    repeats: 12
    timeout: 10000
```

Due to the required generic interface of the `Action` type,
the docstring of an action should always be present with a
description of keys that should exist in `params`
and information on each associated value and usage information.
In addition, `Action` docstrings
**should contain information on the return status strings**.
This helps ensure ease of use by future users.


[//]:#(refs)

[yaml]: https://learnxinyminutes.com/docs/yaml/
[init.py]: __init__.py
