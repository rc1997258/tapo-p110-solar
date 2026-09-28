Tapo P110 Solar Energy Monitor

A Python utility for retrieving historical energy-generation data from a TP-Link Tapo P110 smart plug and producing a human-readable solar-energy report.

The program communicates directly with the P110 using the python-kasa library and the device's get_energy_data protocol API.

Features

Retrieves historical monthly energy data.

Retrieves daily energy data.

Retrieves hourly energy data.

Automatically checks multiple historical years.

Calculates yearly energy generation.

Calculates monthly energy generation.

Calculates daily and hourly energy generation.

Calculates the monetary value of generated energy.

Produces a human-readable plain-text report.

Uses configurable electricity value per kWh.

Keeps Tapo credentials outside the source code.

Does not require the Tapo cloud API for retrieving the energy data.

Example Report

The program generates:

========================================================================================
                         TAPO P110 SOLAR ENERGY HISTORY
========================================================================================

Device       : P110
IP Address   : 172.23.254.95
Generated    : 2026-09-28 17:40:00
Unit Value   : ₹7.00 / kWh
Measurement  : Solar energy generated


----------------------------------------------------------------------------------------
YEARLY SOLAR ENERGY GENERATION
----------------------------------------------------------------------------------------

Year             Energy (Wh)        Energy (kWh)               Savings
------------------------------------------------------------------------------
2025                297,690            297.690             ₹2,083.83
2026                419,707            419.707             ₹2,937.95

TOTAL               717,397            717.397             ₹5,021.78


----------------------------------------------------------------------------------------
MONTHLY SOLAR ENERGY GENERATION
----------------------------------------------------------------------------------------

Year      Month              Energy (Wh)        Energy (kWh)               Savings
--------------------------------------------------------------------------------
2025      January                    0              0.000                   ₹0.00
2025      February                   0              0.000                   ₹0.00
2025      July                   1,898              1.898                  ₹13.29
2025      August                31,128             31.128                 ₹217.90
2025      September             39,757             39.757                 ₹278.30
2025      October               72,558             72.558                 ₹507.91
2025      November              89,682             89.682                 ₹627.77
2025      December              62,667             62.667                 ₹438.67


========================================================================================
                              SOLAR SAVINGS SUMMARY
========================================================================================

Total Solar Energy Generated                         717.397 kWh
Electricity Value                                       ₹7.00 / kWh
Total Electricity Savings                           ₹5,021.78


========================================================================================
                     TOTAL SAVINGS FROM SOLAR GENERATION
                                      ₹5,021.78
========================================================================================


The numbers above are examples.

Requirements

Python 3.9+

A Tapo P110 smart plug with energy monitoring.

The P110 and the computer running this program must be able to communicate over the local network.

python-kasa.

Installation

Clone the repository:

git clone https://github.com/YOUR_USERNAME/tapo-p110-solar.git
cd tapo-p110-solar


Create a virtual environment:

python3 -m venv .venv


Activate it:

source .venv/bin/activate


Install dependencies:

pip install -r requirements.txt

Configuration

The program expects the following environment variables:

TAPO_USERNAME
TAPO_PASSWORD


Set them:

export TAPO_USERNAME='your-tapo-email@example.com'
export TAPO_PASSWORD='your-tapo-password'


The IP address of the P110 is configured inside download_history.py:

IP = "172.23.254.95"


Change this to the IP address of your P110.

The value used to calculate the monetary savings is also configurable:

UNIT_COST = 7.00


For example, if the electricity value is ₹7 per kWh:

UNIT_COST = 7.00

Running

Run:

python download_history.py


The program will connect to the P110 and retrieve the available historical data.

The final report will be written to:

p110_solar_energy.txt


View it with:

less p110_solar_energy.txt


or:

cat p110_solar_energy.txt

Energy Data

The P110 provides energy consumption/generation data in Wh.

The program converts the values to kWh:

1 kWh = 1000 Wh


For example:

297,690 Wh = 297.690 kWh

Savings Calculation

The monetary value is calculated as:

Savings = Generated Energy (kWh) × Value per kWh


With an electricity value of ₹7/kWh:

297.690 kWh × ₹7.00 = ₹2,083.83


The savings figure represents the estimated monetary value of the measured solar energy at the configured per-kWh rate.

Historical Data

The P110's historical API can provide data at different intervals.

The program uses:

Interval	Data
43200	Monthly
1440	Daily
60	Hourly

Monthly history is requested separately for each year because the P110's API expects the monthly query to be aligned to the beginning of the year.

The program probes historical years starting from the configured:

OLDEST_YEAR = 2015


Change this if necessary.

For example:

OLDEST_YEAR = 2020

Security

Do not put your Tapo username or password directly into the Python source code.

Do not commit credentials to GitHub.

Use environment variables:

export TAPO_USERNAME='your-email@example.com'
export TAPO_PASSWORD='your-password'


The repository's .gitignore also excludes common secret and environment files.

If credentials are accidentally committed to a Git repository, changing or removing the file is not sufficient because the credentials may remain in Git history. Rotate the credentials immediately.

Network

The program communicates with the P110 over the local network.

Make sure:

The P110 has a stable IP address.

The server can reach the P110.

Local network/firewall rules permit communication.

The P110 is powered on and connected to Wi-Fi.

You can test basic connectivity with:

ping 172.23.254.95

Limitations

The exact amount of historical data available depends on the P110 firmware/device.

The program queries the raw get_energy_data endpoint rather than relying exclusively on the high-level kasa energy command.

Daily and hourly history may cover a shorter period than monthly history.

The monetary calculation is an estimate based on the configured value per kWh.

Disclaimer

This project is not affiliated with TP-Link or Tapo.

Use it at your own risk. Device firmware and local protocol behavior may change over time.

License

MIT License
