# Pi Control
This is a software stack intended for easy and highly configurable setup of procedures for the proposed elastocaloric material's testing rig. Designed for a [Raspberry Pi][rpi] based system running python

## Philosophy:
The philosophy of the stack is to provide a combination of a simplified interface abstraction and coordination via a mix between [yaml][yaml] configuration files and simplified and convenient interfaces to hardware to describe configurations and procedures.

#### Users:
As a user, there are two main areas you will be using to describe procedures:
- [Actions](#actions) - define new actions for setup (`python`)
- [Routines](#routines) - define new routines for setup (`yaml`)

For a more description of what each area is for see the appropriate subsection here for a link to the area's documentation.

#### Devs:
As a developer, knowing the entire code base is not difficult but in addition to the stack, reading up on the protocols used to communicate between peripherals and the master controller will save you headache later. Recommended topics to cover include:
- I2C communications
- UART communications
- Datasheets for components
- Thermocouples
- Strain gauges

Most of the interfaces are wrappers around pre-existing libraries that are intended to provide usable default behavior while maintaining an extensible api that allows for replacing one ADC interface with another being a relatively painless process.


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

_*Not Implemented*_


#### ADC:

There are multiple ADCs in the system that quantize realworld signals into manipulatable digital formats. In the entire system, the following ADCs exist and are used:
- [ADS1115][ads1115] Used to measure position of the linear actuator. 16-bits of resolution.
- [HX711][hx711] Part of the OpenScale sensor module. Contains a 24-bit ADC operating at upto 80 sps.
- [MAX31856][max31856] Part of MAX universal thermocouple chip. Contains an on-board 19-bit ADC operating in a multiplexed method.

Because all of the converters are part of a module save for the ADS1115, the reference to `ADC` or `adc` can be safely implied to be referring to it and not the other modules.

#### DAC:

Used in conjunction with a jellybean [3-phase brushless DC motor driver](https://www.progressiveautomations.com/lc-241) to control actuator motor speed.

#### Temperature:

Temperature interfaces are implemented with a customized version of John Robinson's [adafruit MAX31856 library][adafruit_github_python].

#### Load cell:

Implemented with the Sparkfun OpenScale interface. The interface aims to be as generic as possible in the future to support multiple hardware families.

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

_*Not Implemented*_

### Control:
---

Control of the entire system is done via a `Procedure`. A `Procedure` is a combination of `Routines` and `Actions` (see below for more information).

#### Actions:

For more complete documentation, see the action's [readme][actions].

#### Routines:

For more complete documentation, see the routine's [readme][routines].

#### Configurable PID controller:

A traditional implementation of a [PID][pid] controller. Able to be put in-line as a controller for the Actuator. It accepts a reference input, an output, and an input.

#### Custom operation profiles:

These are accomplished as a combination of actions and routines. For more information see the related sections.

[//]:#(refs)

[rpi]: https://www.raspberrypi.org/
[yaml]: https://learnxinyminutes.com/docs/yaml/
[actions]: src/actions/readme.md
[routines]: src/routines/readme.md
[max31856]: https://datasheets.maximintegrated.com/en/ds/MAX31856.pdf
[adafruit_github_python]: https://github.com/johnrbnsn/Adafruit_Python_MAX31856
[ads1115]: http://www.ti.com/lit/ds/symlink/ads1115.pdf
[mcp4725]: http://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf
[vpg60001]: http://docs.vpgtransducers.com/?id=2686
[openscale]: https://www.sparkfun.com/products/13261
[hx711]: http://www.aviaic.com/Download/hx711_brief_en.pdf.pdf
[pa14]: https://www.progressiveautomations.com/media/catalog/pdf/Mini_Linear_Actuator_PA-14.pdf
[pid]: https://en.wikipedia.org/wiki/PID_controller
