# README.md

## Nahrání firmwaru pomocí PlatformIO

### 1. Inicializace MCU (bootloader a pojistky)
```bash
pio run -e ATmega1284P_isp -t bootloader
pio run -e ATmega1284P_isp -t fuses
```

### 2. Nahrání firmwaru
```bash
# Přes ISP programátor
pio run -e ATmega1284P_isp -t upload

# Nebo přes UART bootloader
pio run -e ATmega1284P_uart -t upload
```

### Změna USB portu
Ve výchozím nastavení je použit `/dev/ttyUSB0`. Pro změnu portu použijte parametr `--upload-port`:
```bash
pio run -e ATmega1284P_isp --upload-port /dev/ttyUSB1 -t upload
```

---

**Poznámka:** Pro kompletní inicializaci nového MCU spusťte nejprve bootloader a pojistky přes ISP, poté firmware.

## Výstupní datové stringy

Firmware posílá přes sériový port (2400 baud) následující NMEA-like zprávy:

### $POSD - Power On Self Diagnostics
Odesláno při startu zařízení.
```
$POSD,<git_hash>
```
- `git_hash`: Git hash verze firmwaru (40 znaků)

### $ICSD - Initialization Complete Space Dosimeter
Odesláno po dokončení inicializace.
```
$ICSD
```

### $DPSD - Data Packet Space Dosimeter
Hlavní datový paket s energetickým spektrem (hexadecimální formát).
```
$DPSD,<uptime>,<noise>,<0.1MeV>,<0.14MeV>,<0.21MeV>,<0.33MeV>,<0.66MeV>,<1.68MeV>,<4.72MeV>,<9MeV>,<offset>
```
- `uptime`: Čas od startu v sekundách (HEX)
- `noise`: Počet impulsů v šumovém kanálu (HEX)
- `0.1MeV` až `9MeV`: Počty detekovaných částic v jednotlivých energetických pásmech (HEX)
- `offset`: Aktuální ADC offset (HEX)

### $HKSD - Housekeeping Space Dosimeter
Diagnostická data včetně prvních 50 kanálů spektra.
```
$HKSD,<count>,<uptime>,<suppress>,<base_offset>,<ch0>,<ch1>,...,<ch49>
```
- `count`: Pořadové číslo měření (HEX)
- `uptime`: Čas od startu v sekundách (HEX)
- `suppress`: Počet potlačených dvojitých detekcí (HEX)
- `base_offset`: Základní ADC offset (HEX)
- `ch0-ch49`: Počty v prvních 50 kanálech spektra (HEX)

### $BESD - Beacon Space Dosimeter
Denní akumulované hodnoty.
```
$BESD,<daylycount>,<E1>,<E2>,<E3>,<E4>,<E5>,<E6>,<E7>,<E8>
```
- `daylycount`: Počet měření od začátku dne (HEX)
- `E1-E8`: Akumulované počty v energetických pásmech za den (HEX)

### $ADSD - Almanac Data Space Dosimeter
Odesláno jednou za den, obsahuje sumarizaci za poslední 2 dny.
```
$ADSD,<day1_low>,<day1_mid>,<day1_high>,<day2_low>,<day2_mid>,<day2_high>
```
- `day1_*`: Sumarizované hodnoty pro včerejší den v třech pásmech (HEX)
- `day2_*`: Sumarizované hodnoty pro předvčerejší den v třech pásmech (HEX)
