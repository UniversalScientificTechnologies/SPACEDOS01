# SPACEDOS
## Physical dimensions
![Physical dimensions](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/blob/SPACEDOS01B/doc/src/SPACEDOS01B_PCB01A.png)

[Large view](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/blob/SPACEDOS01B/doc/src/SPACEDOS01B_PCB01A.png)

## Energetic range and Climatic endurance
Dissipated Energy range: from 100 keV to 9 MeV (divided into 8 logarithmic channels)

Energy Resolution: < 50 keV

Integration Time: 15 s
 
Temperature Stability: from -50 ℃ to +50 ℃ within error +50 keV

Used Sensor: HAMAMATSU S11773-02 (PIN diode 5 x 5 x 0.5 mm<sup>3</sup>)

Weight: 33 g

## Electrical interface
<img src="https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/blob/SPACEDOS01B/doc/src/header_B.png" width="400">

Conector is depicted from PIN's side.

Signal | Description
--- | ---
PD2 |  Universal Input pin
PD3 |  Universal Output pin
RX0 |  RS232 Receive (3.3 V)
TX0 |  RS232 Transmit (3.3 V)
RST# | Reset (trough capacitor)
GND |  Ground
3V3 |  Power supply +3.3 V

Power consumption: 2.6 mA from 3.3 V

## Communication protocol
### Sample of output data
```
$POSD,2a1c18d43c3937e40a3beb6c2855589b2d1a19e9
$ICSD
$DPSD,98,7fbd,36,1,0,0,0,0,0,0,100
$HKSD,9,98,800b,fe,0,0,7fbd,36,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
$BESD,4,e7,2,1,0,0,0,0,0
$ADSD,d3,3,0,0,0,0
```

SPACEDOS sends $DPSD, $HKSD and $BESD messages each cca 15 seconds.
$ADSD message is sended ones per one day.

Communication speed is 2400 baud.

### Power On
_It transmits just after power on._

`#POSD, <git hash>`

Value | Length | Type |Note
--- | --- | --- | ---
$POSD | 5 B | [Char](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Char) | Header
git hash | 20 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Git hash tag from source file

This information just says hello after power on.

### Initiation complete
_It transmits ones after initialisation after power on._

`#ICSD`

Initiation of the SPACEDOS HW is done.
Initiation is completed up to one second after power on.

### DPSD - SpaceDos Data Payload message
_It transmits every 15 seconds._

`
$DPSD, <uptime>, <noise channel>, <0.1 MeV>, <0.14 MeV>, <0.21 MeV>, <0.33 MeV>, <0.66 MeV>, <1.68 MeV>, <4.72 MeV>, <'>=9 MeV'>, <DC offset>`

Value | Length | Type |Note
--- | --- | --- | ---
$DPSD | 5 B | [Char](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Char) | Header
uptime | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Time from power on
noise channel | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | this channel containing noise
0.1 MeV | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.1 MeV
... | ... | ... |
'>=9' MeV | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Overrange particles
DC offset | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Offset of ADC

This messages should be stored for long period and transmited to the ground as a batch.

Minimal data payload (without timemark) is 18 B per 15 s => 103680 B per day

### HKSD - SpaceDos HouseKeeping message
_It transmits every 15 seconds._

`$HKSD, <measurement No.> , <uptime>, <filter suppressions>, <position of the 1-st channel>, <1-st ch.>, <2-nd ch.>, <3-rd ch.>,...` 

There is a packet with housekeeping information. Transmission of this packet is done besides other experiments hosekeeping data. Total length of this packet should be shorten. 

Value | Range | type |Note
--- | --- | --- | ---
$HKSD | fix | [Char](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Char) | Header
measurement No. | 0..65535 | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) |
uptime | 0..4294967295 | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) |
filter suppressions | 0..65535 | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Number of ussage of digital filter for double peak suppression
position of the 1-st channel | 0..511 | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) |
1-st ch. | 0..65535 | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Number of events in 1-st ch.
2-nd ch. | 0..65535 |  [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) |Number of events in 2-nd ch.
... | ... |
50-th ch. | 0..65535 |  [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) |Number of events in 50-th ch.

### BESD - SpaceDos BEacon message
_It transmits every 15 seconds. Values are zeroed after sending ADSD message._

`$BESD,<counter>, <0.1 MeV>, <0.14 MeV>, <0.21 MeV>, <0.33 MeV>, <0.66 MeV>, <1.68 MeV>, <4.72 MeV>, <'>=9 MeV'>`

This message contains cumulative data for beacon transmission.

Value | Length | Type |Note
--- | --- | --- | ---
$BESD | 5 B | [Char](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Char) | Header
counter | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Number of the beacon message
0.1 MeV | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.1 MeV
0.14 MeV | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.14 MeV
... | ... | ... |
'>=9' MeV | 2 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | Overrange particles

### ADSD - SpaceDos Almanac Data message
_It transmits after 5760 beacon messages. (cca every one day)_

`$ADSD, <0.1 MeV 1 day old>, <0.14 MeV one day old>, <0.66 MeV one day old>, <0.1 MeV two days old>, <0.14 MeV two days old>, <0.66 MeV two days old>`

This message contains two days old data for the beacon transmission purposes.

Value | Length | Type |Note
--- | --- | --- | ---
$ADSD | 5 B | [Char](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Char) | Header
0.1 MeV one day old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.1 MeV one day before
0.14 MeV one day old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.14 MeV one day before
0.66 MeV one day old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.66 MeV one day before
0.1 MeV two days old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.1 MeV two days before
0.14 MeV two days old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.14 MeV two days before
0.66 MeV two days old | 4 B | [Hex](https://github.com/ODZ-UJF-AV-CR/SPACEDOS01/wiki/Hex) | number of particles with absorbed energy above 0.66 MeV two days before

