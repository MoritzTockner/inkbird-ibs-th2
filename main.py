#!/usr/bin/env python3

"""Get inkbird IBS-TH2 temperature, humidity and battery and publishing to mqtt.

Tested only on raspberry pi 3b
"""

import argparse
import logging
import os
import json

from dotenv import dotenv_values

from logger import log, basicConfig
from mqttpublisher import MqttPublisher
from scanner import start


def main():
    config = dotenv_values(os.path.dirname(__file__) + "/.env")
    if len(config) == 0:
        print("Error: .env file not found.")
        exit(1)

    parser = argparse.ArgumentParser(description="Get inkbird IBS-TH2 temperature, humidity and battery and publishing to mqtt.")
    parser.add_argument("--loglevel", dest="logLevel", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="set the logging level")

    args = parser.parse_args()
    if args.logLevel:
        basicConfig(level=getattr(logging, args.logLevel))

    f = open("./config_payloads/temperature.json")
    temperatureConfig = json.load(f)
    f.close()

    f = open("./config_payloads/humidity.json")
    humidityConfig = json.load(f)
    f.close()

    f = open("./config_payloads/battery.json")
    batteryConfig = json.load(f)
    f.close()

    def callback(mac_address, data):
        log.info("Received temperature = %s°C", data["temperature"])
        log.info("Received humidity = %s%%", data["humidity"])
        log.info("Received battery = %s%%", data["battery"])
        
        publisher = MqttPublisher(config)
        topics = config.get("MQTT_TOPICS").split(",")
        mac_addresses = config.get("MAC_ADDRESSES").split(",")
        sensor_ids = config.get("SENSOR_IDS").split(",")

        topic = topics[mac_addresses.index(mac_address)]
        device_name = sensor_ids[mac_addresses.index(mac_address)]

        log.debug("topic = %s", topic)
        log.debug("data = %s", json.dumps(data))

        temperatureConfig["name"] = device_name + " " + "Temperature" 
        temperatureConfig["state_topic"] = topic + "/state"
        temperatureConfig["unique_id"] = device_name + "T"
        temperatureConfig["device"]["identifiers"] = mac_address
        temperatureConfig["device"]["name"] = device_name 

        humidityConfig["name"] = device_name + " " + "Humidity"
        humidityConfig["state_topic"] = topic + "/state"
        humidityConfig["unique_id"] = device_name + "H"
        humidityConfig["device"]["identifiers"] = mac_address
        humidityConfig["device"]["name"] = device_name 
        
        batteryConfig["name"] = device_name + " " + "Battery"
        batteryConfig["state_topic"] = topic + "/state"
        batteryConfig["unique_id"] = device_name + "B"
        batteryConfig["device"]["identifiers"] = mac_address
        batteryConfig["device"]["name"] = device_name 
        
        publisher.publish(topic + "T/config", json.dumps(temperatureConfig))
        publisher.publish(topic + "H/config", json.dumps(humidityConfig))
        publisher.publish(topic + "B/config", json.dumps(batteryConfig))
        publisher.publish(topic + "/state", json.dumps(data))
        #publisher.publish(topic + "T/config", json.dumps(temperatureConfig).replace(" ", ""))
        #publisher.publish(topic + "H/config", json.dumps(humidityConfig).replace(" ", ""))
        #publisher.publish(topic + "B/config", json.dumps(batteryConfig).replace(" ", ""))
        #publisher.publish(topic + "/state", json.dumps(data).replace(" ", ""))
        

    start(config.get("MAC_ADDRESSES").split(','), float(config.get("TIMEOUT")), float(config.get("SAMPLING_TIME")), callback)


if __name__ == "__main__":
    main()
