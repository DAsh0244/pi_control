# Actions
Put actions you will call via the [yaml][yaml] configuration files here.

Ensure that you add the routines to the [\_\_init\_\_.py][init.py] file.
Using the `from <module> import <action>` syntax.

## Overview

### What are Actions?
Actions are the basic unit of operation in a full procedure.
At their basis they are an optionally parametrized call to a function/method that accomplishes a small task.

For the more technically inclined they are a partial implementation of a finite state machine that is completed with actions,
with the other half being accomplished by [routines](../routines/readme.md).
While actions can be likened to states, routines are analogous to transition tables.

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
          # name is the specific action to call
          name: RESET_MIN
          # dictionary of params to pass to the desired action
          params:
            low: *LIMIT_LOW
            high: *LIMIT_HIGH
          # next defines a transition dictionary describing state transitions
          next:
            True: CLEANUP
            False: RESET_MIN
      - !Action
      	  name: RESET_MAX
          params:
            low: *LIMIT_LOW
            high: *LIMIT_HIGH
          next:
            True: CLEANUP
            False: RESET_MAX
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
def some_action(interface: obj, params: dict, next: dict) -> Callable:
    """
    Action description

    :param interface: base interface abstraction layer that is performing an action.
    :param params: dictionary of the form
    	{'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
    :param next: dictionary of state transitions in the form
    	{<condition>:<action_func>, <condition>:<action_func>, None:<action_func>}
    """
    condition = None
    # stuff happens here -- eval and assign the desired value for condition
    ...

    return next[condition]
```

As we can see, all actions return the next state to be executed by the controller.
Internally the controller operates on a sentinel terminated sequence based approach
that can be visualized as the following:

```python
# initialize machine
current_action = action_func
# run until sentinel of None is found
while current_action is not None:
	current_action = current_action()
```

In General, it may be useful to think of actions as only understanding two parts about themselves:
1. What am I supposed to do?
2. Where am I supposed to go next?


#### Nuts-n-Bolts:

Above I mentioned that actions "understand...Where am I supposed to go next?". This is not exactly true. A more correct statement would be th say the `Action` knows which "path" to go down. What defines this path you ask? The _**writer**_ of the action function. Within the action function, you may change the `condition` variable's contents to a string matching a key in the `nxt` mapping to determine what the next action is. 

Let's look at (arguably) the simplest type of example to see `Action`. The `delay` action. 

```python
from time import sleep

def delay(interface=None, params=None, nxt=None):
    """
    action that simply delays for a perscribed amount of time, passed in the params dictionary from the key 'success'
    """
	if nxt is None:
        nxt = {'success': None}  # None as a value indicates a termination of the action chain.
    sleep(params['timeout'])
    return nxt['success'] # action completed successfully 
```
As we can see, this function returns the `success` action regardless of anything save an `Exception`.

Compare the `delay` action to the more complex `oscillate` action:
```python
from hal import actuator
from time import perf_counter

def oscillate(interface=actuator, params=None, nxt=None):
    """
    moves from thresholds described in params dict with keys of 'low_pos', 'high_pos'.
    movement speed is defined in params dict as well with the 'speed' key. 
    adaptive controller is optinoally specifed with the 'controller' key.
    the ability to end oscilation at a specified threshold is avaible with the 
    'reset_closest' key, which expects a boolean True or False value. If not specified, defaults to False
    mutually exlusive number of osillations and timeout are also optional params.
    if both are specified, it will stop at whatever comes first.
      - timeout is specified with the 'timeout' key and expects a float.
      - repititions is specified with the 'repititions' key and expects an int.
    
    """
    if nxt is None:
        nxt = {'success': None} 
    condition = 'success'
    low_pos = params['low_pos']
    high_pos = params['high_pos']
    timeout = params.get('timeout', None)
    repititions = params.get('repititions', None)
    repeats = 0
    start = perf_counter()
    while ((perf_conter() - start) < timeout) or (repeats < repititions):
        interface.set_position(low_pos)
        interface.set_position(high_pos)
	if params.get('reset_closest', False) and abs(interface.position - low_pos) > abs(interface.position - high_pos):  # is closer to lower spot than higher spot
        interface.set_position(low_pos)
    
    return nxt[condition]
```


[//]:#(refs)

[yaml]: https://learnxinyminutes.com/docs/yaml/
[init.py]: __init__.py