# simple-sunspec
Python-routines to read data from SunSpec-compliant PV-inverters (e.g. SolarEdge, SMA, Fronius and others)

If you want a full-fledged SunSpec library for Python, have a look at [pysunspec2](https://github.com/sunspec/pysunspec2). If you want a Python-library and commandline-tool that can directly be used for reading data and returning it as JSON or storing it in an Influx database, have a look at [solaredge_modbus](https://github.com/nmakel/solaredge_modbus).

The routines in this repository can retrieve basic SunSpec-data over modbus-TCP or modbus-RTU, but they can also be used to access inverters remotely through the MQTT-modbus-gateway provided by Teltonika in its LTE-routers, such as the [RUT240](https://wiki.teltonika-networks.com/view/RUT240_Modbus#MQTT_Gateway).
