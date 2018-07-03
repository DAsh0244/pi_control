# Pi Control
This is a software stack intended for easy and highly configurable setup of procedures for the proposed elastocaloric material's testing rig. Designed for a Raspberry pi based system running python

## Philosophy:
The philosophy of the stack is to provide a combination of a simplified interface abstraction and coordination via [yaml][yaml] configuration files to describe configurations and procedures.

As a user, there are two main areas you will be using:
- [Actions](#actions) - define new actions for setup (`python`)
- [Routines](#routines) - define new routines for setup (`yaml`)

For a more description of what each area is for see the appropriate subsection here for a link to the area's documentation.

As a developer, knowing the entire code base is not terribly difficult but


## Capabilities:
Currently the stack supports:

- Interfaces:
	- [x] Linear actuator
	- [x] ADC
    - [x] DAC
    - [x] Temperature
    - [x] Load cell
    - [ ] Strain measurement
    - [ ] Fluid pump


- Sensors:
    - [x] [ADS1115](#ads1115)
    - [x] [MCP4725](#mcp4725)
    - [x] [MAX31856](#max31856)
    - [x] [VPG60001](#vpg60001) via [Sparkfun Openscale][openscale]
    - [ ] Strain measurement
- Control:
	- [x] [Actions](#actions)
    - [ ] [Routines](#routines)
    - [x] [Configurable PID controller](#configurable-pid-controller)
    - [ ] [Custom operation profiles](#custom-operation-profiles)

Below are larger explanations of each ability:

### Interfaces:
---
#### Linear actuator:
Models a [PA-14][pa14] linear actuator. With an ADC and DAC as the position and speed control.

#### Fluid pump:

_**Not Implemented:**_


#### ADC:

#### DAC:

#### Temperature:

#### Load cell:


### Sensors:
---
#### ADS1115
16-bit, 4-channel, I2C,  Delta-Sigma Converter with on board programmable gain amplifier.

[ADS1115 Datasheet][ads1115]

#### MCP4725
12-bit, I2C, DAC with on board EEPROM.

[MCP4725 Datasheet][mcp4725]

#### MAX31856
Thermocouple to digital converter.

[MAX31856 Datasheet][max31856]

#### VPG60001
S-type load cell:
- 1000 lb (453.6 kg)
- 3mV/V sensitivity.
- Read with a [HX711][hx711] load cell ASIC based board providede by sparkfun

[VPG60001 Datasheet][vpg60001]

#### Strain measurement:


### Control:
---

#### Actions:

For more complete documentation, see the action's [readme][actions].

#### Routines:

For more complete documentation, see the routine's [readme][routines].

#### Configurable PID controller:

A traditional implementation of a [PID][pid] controller.

#### Custom operation profiles:


[//]:#(refs)

[yaml]: https://learnxinyminutes.com/docs/yaml/
[actions]: src/actions/readme.md
[routines]: src/routines/readme.md
[max31856]: https://datasheets.maximintegrated.com/en/ds/MAX31856.pdf
[ads1115]: http://www.ti.com/lit/ds/symlink/ads1115.pdf
[mcp4725]: http://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf
[vpg60001]: http://docs.vpgtransducers.com/?id=2686
[openscale]: https://www.sparkfun.com/products/13261
[hx711]: http://www.aviaic.com/Download/hx711_brief_en.pdf.pdf
[pa14]: https://www.progressiveautomations.com/media/catalog/pdf/Mini_Linear_Actuator_PA-14.pdf
[pid]: https://en.wikipedia.org/wiki/PID_controller
