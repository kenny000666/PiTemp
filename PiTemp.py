#!/usr/bin/python

import sys
import getopt
import os
import time 
import logging
import glob
import paho.mqtt.publish as publish
import paho.mqtt.client as Client
import configparser
import atexit

log = None

mqttClient = None

def exit_handler():
    mqttClient.disconnect

def initLogger(name, file):
    global log
    log = logging.getLogger(__name__)
    soh = logging.StreamHandler(sys.stdout)
    soh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    if (file):
        fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + "/" + name + ".log"),maxBytes=1000,backupCount=10)
        log.addHandler(fileHandler)
    log.addHandler(soh)
    log.setLevel(logging.DEBUG)

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
    configPath = None
    topic = None
    host = None
    port = None

    if (argv != None):
        try:
            opts, args = getopt.getopt(argv, 'hodul:', ['Topic=', 'Host=', 'Port=' ] )

            initLogger(os.path.basename(__file__), logToFile)
            log.info("Initializing " + os.path.basename(__file__) + "...")


            for opt, arg in opts:
                if opt in '-h':
                    print(os.path.basename(__file__) + " -h -o -d -u -l --Config --Topic --Host --Port")
                    sys.exit(2)
                elif (opt == '-o'):
                    logToFile = True
                elif opt == '-l':
                    if arg == 'i':
                        logLevel = 'info'
                    elif arg == 'd':
                        logLevel = 'debug'
                    elif arg == 'e':
                        logLevel = 'error'
                    elif arg == 'w':
                        logLevel = 'warn'
                elif (opt == '-d'):
                    debug = True
                elif (opt == 'u'):
                    if (arg == 'c'):
                        unit = 'c'
                    else: unit = 'f'
                elif (opt == '--Config'):
                    configPath = arg
                elif (opt == '--Topic'):
                    topic = arg
                elif (opt == '--Host'):
                    host = arg
                elif (opt == '--Port'):
                    port = arg

            if (not debug):
                if (configPath == None and (topic == None or host == None or port == None)):
                    raise Exception('No Config and MQTT Parameters not set')

        except getopt.GetoptError:
            print(os.path.basename(__file__) + " -h -o -d -u --Config --Topic --Host --Port")
            sys.exit(1)
        except Exception as e:
            print("Error reading parameters")
            print(e) 
            sys.exit(1)

    if (not debug):
        os.system("modprobe w1-gpio")
        os.system("modprobe w1-therm")

    if (debug):
        base_dir = 'C:\\Users\\kenny\\Documents\\dev\\Python\\PiTemp\\'
    else:
        base_dir = '/sys/bus/w1/devices/'

     
    if (configPath != None):
        cfg = configparser.ConfigParser()
        #        {"client_id": os.path.basename(__file__) + str(os.getpid()), "hostname": "mqtt", "port": "1883", "auth": "False",
        #        "retain": "False", "qos": "0"})
        cfg.optionxform = str
        try:
            cfg.read(configPath)
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
        except Exception as e:
            log.error("Error while reading Config")
            log.error(e)      
            exit()  

    global mqttClient
    mqttClient = Client.Client(client_id=os.path.basename(__file__))
    try:
        mqttClient.connect(host,port=int(port))
        connected = True
    except Exception as e:
        log.error("Error connecting to mqtt broker")
        log.error(e)
        connected = False

    

    while True:
        log.debug("looking for files in: %s", base_dir)
        tempfiles = glob.glob(base_dir + '28*/w1_slave', recursive=True)
        log.debug("Files found " + str(len(tempfiles)))
        for file in tempfiles:
            probeName = os.path.basename(os.path.dirname(file))
            temperature = read_temp(file, unit)
            log.debug( probeName + " : " + str(temperature))
            published = False
            retry = 0
            while (not published and retry <= 3):
                try:
                    if (not debug or connected):
                        mqttClient.publish(topic + "/" + probeName, payload=str(temperature), qos=1)                
                        log.debug("Message Published to topic %s", topic + "/" + probeName)
                        published = True
                except Exception as e:
                    log.error("Error updating and publishing message")
                    log.error(e)
                    published = False
                    sys.exit(2)
        log.debug("Sleeping")
        time.sleep(5)

if __name__ == "__main__":
    main(sys.argv[1:])
    

