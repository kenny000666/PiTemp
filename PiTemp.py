#!/usr/bin/python

import sys
import getopt
import os
import time 
import logging
import glob
import paho.mqtt.publish as publish
import configparser

log = None

def initLogger(name, file):
    global log
    log = logging.getLogger(__name__)
    soh = logging.StreamHandler(sys.stdout)
    soh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    if (file):
        fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + "/" + name + ".log"),maxBytes=1000,backupCount=10)
        log.addHandler(fileHandler)
    log.addHandler(soh)
    log.setLevel(logging.INFO)

def read_temp_raw(file):
    f = open(file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp(file, unit):
    lines = read_temp_raw(file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        if (unit == "c"):
            return temp_c
        else: return temp_f

def main(argv): 
    logToFile = False
    debug = False
    unit = 'c'

    if (argv != None):
        try:
            opts, args = getopt.getopt(argv, "hodu")
        except getopt.GetoptError:
            print(os.path.basename(__file__) + " -h -o -d -u")
            sys.exit(1)

        for opt, arg in opts:
            if opt in '-h':
                print(os.path.basename(__file__) + " -h -o -d -u")
                sys.exit(2)
            elif (opt == '-o'):
                logToFile = True
            elif (opt == '-d'):
                debug = True
            elif (opt == 'u'):
                if (arg == 'c'):
                    unit = 'c'
                else: unit = 'f'



    initLogger(os.path.basename(__file__), logToFile)
    log.info("Initializing " + os.path.basename(__file__) + "...")


    # if (not debug):
    #     os.system("modprobe w1-gpio")
    #     os.system("modprobe w1-therm")

    if (debug):
        base_dir = 'C:\\Users\\kenny\\Documents\\dev\\PiTemp\\'
    else:
        base_dir = '/sys/bus/w1/devices/'
    tempfiles = glob.glob(base_dir + '28*/w1_slave', recursive=True)
    
    for dir in tempfiles:
        log.info("Dir Name: " + dir) 
 
    cfg = configparser.ConfigParser(
            {"client_id": os.path.basename(__file__) + str(os.getpid()), "hostname": "mqtt", "port": "1883", "auth": "False",
             "retain": "False", "qos": "0"})
    cfg.optionxform = str
    cfg.read(os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + "/mqtt.conf"))
    
    client_id = cfg.get("mqtt", "client_id")
    host = cfg.get("mqtt", "hostname")
    port = eval(cfg.get("mqtt", "port"))
    topic = cfg.get("mqtt", "topic")
    qos = eval(cfg.get("mqtt", "qos"))
    retain = eval(cfg.get("mqtt", "retain"))
    if eval(cfg.get("mqtt", "auth")):
        auth = {"username": cfg.get("mqtt", "user"), "password": cfg.get("mqtt", "password")}
    else:
        auth = None

    
    while True:
        try:
            mqttmsg = []
            count = 1
            for file in tempfiles:
                temperature = read_temp(file, unit)
                log.info("Probe " + str(count) + " : " + str(temperature))
                count=count+1
                msg = [{"topic": topic + "/Probe" + str(count) , "payload": "{ unit: " + unit + " value : " + str(temperature) + "}" , "qos": qos, "retain": retain}]
                mqttmsg.append(msg)
            if (not debug):
                publish.multiple(mqttmsg, hostname=host, port=port, client_id=client_id, auth=auth)
            time.sleep(5)
        except Exception as e:
            log.error("Error updating and publishing message")
            log.error(e)

if __name__ == "__main__":
    main(sys.argv[1:])
    

