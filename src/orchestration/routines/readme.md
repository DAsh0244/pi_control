# Routines

## What are routines?
Routines are a description of a sequence of [actions](../actions) combined that accomplish a task.

## How are they used?

### Overview
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
            low: 750
            high: 20000
      - !Action
          name: CLEANUP
    transitions:
      START:
        *: RESET_MIN
      CLEANUP:
        *: END
      RESET_MIN:
        success: CLEANUP
        error: ERR
```

By default there are always at least three (3) actions in every procedure:
1. `Start` Action  -- referred as `START`,`Start`
2. `End` Action -- referred as `END`,`End`
3. `Error` Action -- referred as `ERR`,`ERROR`,`Error`


As the name implies, all `Routines` begin at their `Start` Action. From here the next few Actions should be setup to prepare for the procedure (calibration, initialization, etc).

Much like the `Start` Action, the `End` Action also carries with it the significance as it is the signifier that the `Routine` is completed and the procedure executor will move into its standby state or begin applying post-processing if applicable.

The `Error` Action provides a means of catching flaws in `Routines` or `Actions` in a safe manner. If a state fails to transition into a known state defined in its transition table, it will automatically be moved into the `Error` action and the handler provided to the action will be executed.

While these states are always present, and therefore never need to be explicitly defined, their transitions still must be filled in. System behavior upon failure to do so is not explicitly guaranteed (see [implementation details](#implementation-details))


In addition to the above actions. The following Actions will be necessary to use:
- `Cleanup`  -- cleans up pin setups and other resources

### Transitions:

Transitions are defined as follows:
```yaml
<action>:
  <condition>: <next_action>
  <condition>: <next_action>
```

To enforce a unconditional transition, use the wild card operator `*`. This will act as a unconditional transition and proceed regardless **except** for `error` conditions.
To skip past `error` conditions, transitions **must** be implemented explicitly.

**NOT IMPLEMENTED YET**
### Compound Conditions: **EXPERIMENTAL**
The Usual boolean operators can be applied to transition conditions.
For example, conditions can be negated in transitions with the `not` keyword.
Planned supported operators are described below:

|Boolean Op |Operator |     STATUS        |
|:---------:|:-------:|:-----------------:|
|   `NOT`   |  `not`  | **not** supported         |
|   `AND`   |  `and`  | **not** supported |
|   `OR`    |  `or`   | **not** supported |
|   `XOR`   |  `xor`  | **not** supported |


## Implementation details:

`Routine` implementation is done as a container object that exposes an `Iterable` interface of action references and transition rules that are associated with it.
These are then mapped to actual `Actions` and linked together via the `Procedure` mechanism.

By default **all** actions will handle an `'error'` condition by falling into the `Error` state.

If a transition table entry is not supplied for an Action, It will drop all transitions and revert to the default `Routine` transition table of:

| Action | Transition | Next Action |
|:------:|:----------:|:-----------:|
|`START` |     `*`    |    `ERR`    |

As seen, the default action is to raise an error state and halt action. This was deemed a reasonable default behavior but is easily modified by overriding the Routine's default table.

Routines have no means of identifying if a specified `Action` exists and therefore has no handling of misspelled entries or invalid parameters. ***An improperly formed `Action` ***WILL*** provide undefined behavior.***
