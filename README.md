# Rasperrby PI-based Health Management Platform

This repository contains a code and necessary technical details for a Raspberry PI-based prototype of the health management platform. 

**Project Description**

The goal of this project is to develop a prototype for a home-based healthcare data management platform. This includes data transfer from wearable devices to central repository on Azure Cloud and usage of Raspberry PI with Smart Mirror Module and touchscreen for user interface. Thus, the system follows Device-Cloud-Device architecture.  The core technical objective is to establish a cohesive ecosystem enabling integration between distributed data sources and the central control platform (edge device) with the ease-of-operability and minimum latency.

**Target Users**

The system is designed primarily for non-technical users who seek straightforward, intuitive tools for health monitoring. This includes elderly users, individuals managing chronic conditions, and those interested in wellness and preventive health. Moreover, is may serve as a experimentation platform for developers, computer scientists, and entrepreneurs. 

**Expected Outcomes**

* Improved user engagement with daily health management.
* Enhanced user understanding of his health data through interactive visualizations.
* Increased user satisfaction and abilities in managing health due to tracking of health data.

**Architecutre & Data Flow**

<img width="421" alt="Screenshot 2024-04-24 at 12 22 38" src="https://github.com/barto-official/health_mirror/assets/125658269/c8db2040-3122-4171-b227-da6354e5bb00">

1. Data Sources:
   * Huawei Watch GT 3-712 (Model JPT-B19) (Smartwatch) — records user activity, calculates health-related metrics, and saves data to Huawei Health iOS application.
   * Apple iPhone 13 — records user activity, calculates health-related metrics, and saves data to Apple Health iOS application. This application also aggregates data from smartwatch so behaves as a central repository on device.

2. Device-Cloud Transfer: Data is transferred from Apple Health to third-party application — [Health Auto Export](https://github.com/Lybron/health-auto-export) — which is responsible for device-cloud transfer. The transfer is executed with the following configuration:
   * 15 Health Metrics to transfer (out of over 100 available): Active Energy (kJ), Resting Heart Rate (bpm), Flights Climbed (count), Headphone Audio Exposure (dBASPL — Sound Pressure Level), Step Count (count), Resting Energy (kJ), Heart Rate [Min] (bpm), Heart Rate [Max] (bpm), Heart Rate [Avg] (bpm), Step Count (steps), Walking+Running Distance (km), Walking Speed (km/hr), Walking Step Length (cm), Walking Asymmetry Percentage (%), Walking Double Support Percentage (%)
   * Period of data to transfer: Since the Last Synchronization
   * Aggregation level: Hour
   * Synchronization Cadence Interval: Hours
   * Synchroniation Cadence Quantity: 3

  Data is sent in the JSON format based on HTTP Trigger to RestAPI and follows the timestamped-based schema. Health Auto Export does not share this data, does not include any third-party software development kits (SDKs), and does not    share data.

3. Cloud Processing: Data is sent to REST API in the form of Azure Function App. It accepts data in a JSON format, process it, and inserts data into MySQL database, which is also stored on Azure. 
4. Edge Device Processing: User interacts with the system through the touchscreen connected to Raspberry Pi and a [Magic Mirror](https://magicmirror.builders/) module, which serves as a user-friendly interface. If device is active, it hosts two processes:
  * Redis database —  an in-memory caching database that stores data from the last 7 days.
    * It updates data by calling MySQL every three hours using cron jobs (`0 */3 * * * /usr/bin/python3 /path/to/your/script.py`) and stores data for 24 hours or until the update using new fresh data (`key_expiry == 86400`). You can set up this parameter while using `r.set()` function. This serves as a protecting mechanism in case of retrieval failure.
    * Redis is configured to include Append Only File (AOF) mode which controls Redis persistence mode and how it logs every write operation to a file: `appendfsync` parameter is set to `always`. To make this changes, open Redis conf file and change `appendonly == yes` and `appendfsync == always`.
  * Streamlit Dashboard — using Seaborn and Matlpotlib for simple visualization of health data based on user range query. If the query requires data within the last seven days, cached data from Redis is used. Otherwise, Streamlit retrieves data from MySQL directly.

<img width="1431" alt="Screenshot 2024-04-24 at 13 47 36" src="https://github.com/barto-official/health_mirror/assets/125658269/c88abfef-7f64-4ba8-afc2-cb2e9a1c41f8">


**Technical Caveats:**
* Importantly, the automation cannot be run in the background if the smartphone is locked due to the privacy policy by Apple. This can be, however, circumvented by using Shortcuts and creating a widget for automation. Both can be achieved by settings in Auto Health Export application. 
* Auto Health Export supports different types of automation: REST API,  Home Assistant, MQTT, Dropbox, Google Drive, iCloud Drive.
* Streamlit can encounter many problems (pyarrow library) when using Raspberry PI with 32bit OS. Try 64.
* Find JSON schema for health metrics transfer directly here: [Health Auto Export](https://github.com/Lybron/health-auto-export/wiki/API-Export---JSON-Format)) 

