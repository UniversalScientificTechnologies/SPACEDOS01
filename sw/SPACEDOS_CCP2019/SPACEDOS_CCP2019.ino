String githash = "$Id$";
//
/*
  SPACEDOS for CCP2019

  Compiled with: Arduino 1.8.5

  ISP
  ---
  PD0     RX
  PD1     TX
  RESET#  through 50M capacitor to RST#

  ANALOG
  ------
  +      A0  PA0
  -      A1  PA1
  TRACE  0   PB0

                     Mighty 1284p
                      +---\/---+
           (D 0) PB0 1|        |40 PA0 (AI 0 / D24)
           (D 1) PB1 2|        |39 PA1 (AI 1 / D25)
      INT2 (D 2) PB2 3|        |38 PA2 (AI 2 / D26)
       PWM (D 3) PB3 4|        |37 PA3 (AI 3 / D27)
    PWM/SS (D 4) PB4 5|        |36 PA4 (AI 4 / D28)
      MOSI (D 5) PB5 6|        |35 PA5 (AI 5 / D29)
  PWM/MISO (D 6) PB6 7|        |34 PA6 (AI 6 / D30)
   PWM/SCK (D 7) PB7 8|        |33 PA7 (AI 7 / D31)
                 RST 9|        |32 AREF
                VCC 10|        |31 GND
                GND 11|        |30 AVCC
              XTAL2 12|        |29 PC7 (D 23)
              XTAL1 13|        |28 PC6 (D 22)
      RX0 (D 8) PD0 14|        |27 PC5 (D 21) TDI
      TX0 (D 9) PD1 15|        |26 PC4 (D 20) TDO
RX1/INT0 (D 10) PD2 16|        |25 PC3 (D 19) TMS
TX1/INT1 (D 11) PD3 17|        |24 PC2 (D 18) TCK
     PWM (D 12) PD4 18|        |23 PC1 (D 17) SDA
     PWM (D 13) PD5 19|        |22 PC0 (D 16) SCL
     PWM (D 14) PD6 20|        |21 PD7 (D 15) PWM
                      +--------+
*/

#include "wiring_private.h"
#include <Wire.h>           // Tested with version 1.0.0. built in
#include "RTClib.h"         // Tested with version 1.5.4. by NeiroN
#include <avr/wdt.h>

#define TRACE     0    // PB0
#define PC7       23   // PC7
#define PC3       19   // PC3

#define CHANNELS 512   // number of channels in buffer for histogram, including negative numbers
#define RANGE 252      // Dynamic range in channels

uint16_t count = 0;
uint16_t offset, base_offset;
uint8_t lo, hi;
uint16_t u_sensor, maximum;
uint32_t dayly[8], day1[3], day2[3];
uint16_t daylycount = 0;

RTC_Millis rtc;

// Read Analog Differential without gain (read datashet of ATMega1280 and ATMega2560 for refference)
// Use analogReadDiff(NUM)
//  NUM  | POS PIN | NEG PIN | GAIN
//  0    | A0      | A1      | 1x
//  1    | A1      | A1      | 1x
//  2    | A2      | A1      | 1x
//  3    | A3      | A1      | 1x
//  4    | A4      | A1      | 1x
//  5    | A5      | A1      | 1x
//  6    | A6      | A1      | 1x
//  7    | A7      | A1      | 1x
//  8    | A8      | A9      | 1x
//  9    | A9      | A9      | 1x
//  10   | A10     | A9      | 1x
//  11   | A11     | A9      | 1x
//  12   | A12     | A9      | 1x
//  13   | A13     | A9      | 1x
//  14   | A14     | A9      | 1x
//  15   | A15     | A9      | 1x
#define PIN 0
uint8_t analog_reference = INTERNAL2V56; // DEFAULT, INTERNAL, INTERNAL1V1, INTERNAL2V56, or EXTERNAL

void setup()
{

  // Open serial communications and wait for port to open:
  Serial.begin(2400);

  wdt_enable(WDTO_8S); // Enable WDT with 8 second timeout

  Serial.println("$POSD," + githash.substring(5,45)); // FW Git hash

  ADMUX = (analog_reference << 6) | ((PIN | 0x10) & 0x1F);

  ADCSRB = 0;               // Switching ADC to Free Running mode
  sbi(ADCSRA, ADATE);       // ADC autotrigger enable (mandatory for free running mode)
  sbi(ADCSRA, ADSC);        // ADC start the first conversions
  sbi(ADCSRA, 2);           // 0x100 = clock divided by 16, 62.5 kHz, 208 us for 13 cycles of one AD conversion, 24 us fo 1.5 cycle for sample-hold
  cbi(ADCSRA, 1);
  cbi(ADCSRA, 0);

  pinMode(TRACE, OUTPUT);   // TRACE for peak detetor
  pinMode(PC7, INPUT);      // spare input port
  digitalWrite(PC3, LOW);   // turn the output port low
  pinMode(PC3, OUTPUT);     // spare output port
 
  digitalWrite(TRACE, LOW);

  // measurement of ADC offset
  ADMUX = (analog_reference << 6) | 0b10001; // Select +A1,-A1 for offset correction
  delay(200);
  ADCSRB = 0;               // Switching ADC to Free Running mode
  sbi(ADCSRA, ADATE);       // ADC autotrigger enable (mandatory for free running mode)
  sbi(ADCSRA, ADSC);        // ADC start the first conversions
  sbi(ADCSRA, 2);           // 0x100 = clock divided by 16, 62.5 kHz, 208 us for 13 cycles of one AD conversion, 24 us fo 1.5 cycle for sample-hold
  cbi(ADCSRA, 1);
  cbi(ADCSRA, 0);
  sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC
  while (bit_is_clear(ADCSRA, ADIF)); // wait for the first conversion
  sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC
  lo = ADCL;
  hi = ADCH;
  ADMUX = (analog_reference << 6) | 0b10000; // Select +A0,-A1 for measurement
  ADCSRB = 0;               // Switching ADC to Free Running mode
  sbi(ADCSRA, ADATE);       // ADC autotrigger enable (mandatory for free running mode)
  sbi(ADCSRA, ADSC);        // ADC start the first conversions
  sbi(ADCSRA, 2);           // 0x100 = clock divided by 16, 62.5 kHz, 208 us for 13 cycles of one AD conversion, 24 us fo 1.5 cycle for sample-hold
  cbi(ADCSRA, 1);
  cbi(ADCSRA, 0);
  // combine the two bytes
  u_sensor = (hi << 7) | (lo >> 1);
  // manage negative values
  if (u_sensor <= (CHANNELS / 2) - 1 ) {
    u_sensor += (CHANNELS / 2);
  } else {
    u_sensor -= (CHANNELS / 2);
  }
  base_offset = u_sensor - 2;

  for (int n = 0; n < 8; n++) // Reset dayly flux counts
  {
    dayly[n] = 0;
  }

  for (int n = 0; n < 3; n++) // Reset dayly circular buffer
  {
    day1[n] = 0;
    day2[n] = 0;
  }

  
  Serial.println("$ICSD");
}


void loop()
{
  uint16_t buffer[CHANNELS];

  for (int n = 0; n < CHANNELS; n++) // Reset buffer for histogram
  {
    buffer[n] = 0;
  }

  // measurement of ADC offset
  ADMUX = (analog_reference << 6) | 0b10001; // Select +A1,-A1 for offset correction
  delay(50);
  ADCSRB = 0;               // Switching ADC to Free Running mode
  sbi(ADCSRA, ADATE);       // ADC autotrigger enable (mandatory for free running mode)
  sbi(ADCSRA, ADSC);        // ADC start the first conversions
  sbi(ADCSRA, 2);           // 0x100 = clock divided by 16, 62.5 kHz, 208 us for 13 cycles of one AD conversion, 24 us fo 1.5 cycle for sample-hold
  cbi(ADCSRA, 1);
  cbi(ADCSRA, 0);
  sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC
  while (bit_is_clear(ADCSRA, ADIF)); // wait for the first conversion
  sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC
  lo = ADCL;
  hi = ADCH;
  ADMUX = (analog_reference << 6) | 0b10000; // Select +A0,-A1 for measurement
  ADCSRB = 0;               // Switching ADC to Free Running mode
  sbi(ADCSRA, ADATE);       // ADC autotrigger enable (mandatory for free running mode)
  sbi(ADCSRA, ADSC);        // ADC start the first conversions
  sbi(ADCSRA, 2);           // 0x100 = clock divided by 16, 62.5 kHz, 208 us for 13 cycles of one AD conversion, 24 us fo 1.5 cycle for sample-hold
  cbi(ADCSRA, 1);
  cbi(ADCSRA, 0);
  // combine the two bytes
  u_sensor = (hi << 7) | (lo >> 1);
  // manage negative values
  if (u_sensor <= (CHANNELS / 2) - 1 ) {
    u_sensor += (CHANNELS / 2);
  } else {
    u_sensor -= (CHANNELS / 2);
  }
  offset = u_sensor;

  PORTB = 1;                          // Set RESET/TRACE output for peak detector to H
  sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC
  while (bit_is_clear(ADCSRA, ADIF)); // wait for the first dummy conversion
  DDRB = 0b10011111;                  // RESET/TRACE peak detector
  delayMicroseconds(100);             // guaranteed reset
  DDRB = 0b10011110;

  sbi(ADCSRA, ADIF);        // reset interrupt flag from ADC

  uint16_t suppress = 0;

  // dosimeter integration
  //for (uint8_t i = 0; i < 6; i++) // multiple of 5 s
  {
    while (bit_is_clear(ADCSRA, ADIF)); // wait for dummy conversion
    DDRB = 0b10011111;                  // RESET/TRACE peak detector
    asm("NOP");                         // cca 6 us for 2k2 resistor and 1k capacitor in peak detector
    asm("NOP");
    asm("NOP");
    asm("NOP");
    asm("NOP");
    DDRB = 0b10011110;
    sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC

    for (uint16_t n = 0; n < 65535; n++) // 4600 = cca 1 s
    {
      while (bit_is_clear(ADCSRA, ADIF)); // wait for end of conversion
      //delayMicroseconds(24);            // 24 us wait for 1.5 cycle of 62.5 kHz ADC clock for sample/hold for next conversion
      asm("NOP");                         // cca 8 us after loop
      asm("NOP");
      asm("NOP");
      asm("NOP");
      asm("NOP");
      asm("NOP");

      DDRB = 0b10011111;                  // RESET/TRACE peak detector
      asm("NOP");                         // cca 7 us for 2k2 resistor and 100n capacitor in peak detector
      asm("NOP");
      asm("NOP");
      asm("NOP");
      asm("NOP");
      DDRB = 0b10011110;
      sbi(ADCSRA, ADIF);                  // reset interrupt flag from ADC

      // we have to read ADCL first; doing so locks both ADCL
      // and ADCH until ADCH is read.  reading ADCL second would
      // cause the results of each conversion to be discarded,
      // as ADCL and ADCH would be locked when it completed.
      lo = ADCL;
      hi = ADCH;

      // combine the two bytes
      u_sensor = (hi << 7) | (lo >> 1);

      // manage negative values
      if (u_sensor <= (CHANNELS / 2) - 1 ) 
      {
        u_sensor += (CHANNELS / 2);
      } 
      else 
      {
        u_sensor -= (CHANNELS / 2);
      }

      if (u_sensor > maximum) // filter double detection for pulses between two samples
      {
        maximum = u_sensor;
        suppress++;
      }
      else
      {
        buffer[maximum]++;
        maximum = 0;
      }
      wdt_reset(); //Reset WDT 
    }
  }

  // Data out
  {
    DateTime now = rtc.now();
    uint32_t uptime;
    uptime = now.unixtime();

    // make a string for assembling the data to log
    // HexaDecimal Compressed Spectrum
    String dataString = "$DPSD,";

    dataString += String(uptime, HEX);;
    dataString += ",";

    uint16_t noise = base_offset + 3;
    uint16_t energy = 0;

    // noise
    dataString += String(buffer[noise-1], HEX);
    dataString += ",";

    // 0.1 MeV
    dataString += String(buffer[noise], HEX);
    dayly[0] += buffer[noise];
    dataString += ",";

    // 0.14 MeV
    for (uint16_t n = noise + 1; n < (noise + 3); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[1] += energy;
    dataString += ",";
    energy = 0;

    // 0.21 MeV
    for (uint16_t n = noise + 3; n < (noise + 6); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[2] += energy;
    dataString += ",";
    energy = 0;

    // 0.33 MeV
    for (uint16_t n = noise + 6; n < (noise + 15); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[3] += energy;
    dataString += ",";
    energy = 0;

    // 0.66 MeV
    for (uint16_t n = noise + 15; n < (noise + 42); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[4] += energy;
    dataString += ",";
    energy = 0;

    // 1.68 MeV
    for (uint16_t n = noise + 42; n < (noise + 123); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[5] += energy;
    dataString += ",";
    energy = 0;

    // 4.72 MeV
    for (uint16_t n = noise + 123; n < (noise + 236); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[6] += energy;
    dataString += ",";
    energy = 0;

    // 9 MeV
    for (int16_t n = noise + 236; n < (CHANNELS); n++)
    {
      energy += buffer[n];
    }
    dataString += String(energy, HEX);
    dayly[7] += energy;
    dataString += ",";
    energy = 0;

    dataString += String(offset, HEX);

    Serial.println(dataString);  // print-out data

    // Decimal spectrum for Housekeeping
    dataString = "$HKSD,";

    dataString += String(count, HEX);
    dataString += ",";
    dataString += String(uptime, HEX);
    dataString += ",";
    dataString += String(suppress, HEX);
    dataString += ",";
    dataString += String(base_offset, HEX);

    for (uint16_t n = base_offset; n < (base_offset + 50); n++)
    {
      dataString += ",";
      dataString += String(buffer[n], HEX);
    }


    Serial.println(dataString);  // print-out data


    // Dayly data for Beacon
    dataString = "$BESD,";

    dataString += String(daylycount, HEX);

    for (int n = 0; n < 8; n++)
    {
      dataString += ",";
      dataString += String(dayly[n], HEX);
    }

    Serial.println(dataString);  // print-out data

    count++;
    daylycount++;

    if (daylycount > 4) //!!! ((60*60*24)/15))
    {
      // Almanac data for Beacon

      dataString = "$ADSD,";
      dataString += String(day1[0], HEX);
      dataString += ",";
      dataString += String(day1[1], HEX);
      dataString += ",";
      dataString += String(day1[2], HEX);
      dataString += ",";
      dataString += String(day2[0], HEX);
      dataString += ",";
      dataString += String(day2[1], HEX);
      dataString += ",";
      dataString += String(day2[2], HEX);

      Serial.println(dataString);  // print-out data

      for (int n = 0; n < 3; n++) // Shift dayly circular buffer
      {
        day2[n] = day1[n];
      }
      day1[0] = dayly[0];
      day1[1] = dayly[1] + dayly[2] + dayly[3];
      day1[2] = dayly[4] + dayly[5] + dayly[6] + dayly[7]; 

      daylycount = 0;
      for (int n = 0; n < 8; n++) // Reset dayly flux counts
      {
        dayly[n] = 0;
      }
    }
  }
}









