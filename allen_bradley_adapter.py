from pycomm3 import SLCDriver, LogixDriver
from clearblade.ClearBladeCore import System, Query
import json, sys, time, requests

# a python script to read tags from Allen Bradley Micrologix and ControlLogix PLCs to ClearBlade plaform via MQTT

# nohup python adapter.py $ARGS > /dev/null 2>&1 

print("Initializing script: ", sys.argv[0])

if len(sys.argv) > 5:  
    SystemKey = sys.argv[1]
    SystemSecret = sys.argv[2]
    SystemUrl = sys.argv[3]    
    DeviceName = sys.argv[4]
    DeviceKey =  sys.argv[5] 
    
else : 
    print("Not enough arguments..Script requires 1)SystemKey 2)SystemSecret 3)SystemUrl 4)DeviceName 5)DeviceKey..")
    sys.exit()

# connect to ClearBlade platform and authenticate
mySystem = System(SystemKey, SystemSecret, SystemUrl)
device = mySystem.Device(DeviceName, DeviceKey)

# get device adapter config from collection
adapter_config_collection = mySystem.Collection(device, collectionName="adapter_config")
q = Query()
q.equalTo("adapter_name", DeviceName)
adapter_configs = adapter_config_collection.getItems(q)

# pull user defined device specs from adapter settings column
if len(adapter_configs):
    adapter_settings = adapter_configs[0]['adapter_settings']
    adapter_config = json.loads(adapter_settings)
    endpoint_ip = adapter_config['endpoint_ip']
    msg_port = adapter_config['msg_port']
    interval = adapter_config['interval']
    tag_collection_name = adapter_config['tag_collection_name']
    msg_topic = adapter_config['msg_topic']
    allen_bradley_type = adapter_config['allen_bradley_type']

else:
    print("Adapter configuration is required..must be stored in adapter_config collection")
    sys.exit()

# log into the tag collection and grab list of tags
tags_collection = mySystem.Collection(device, collectionName=tag_collection_name)
tag_rows = tags_collection.getItems()

if not tag_rows:
    print("Unable to pull tag list from platform..must be stored in a collection and named in adapter settings")
    sys.exit()

# open connection to Allen Bradley plc
if allen_bradley_type == 'SLCDriver':
    plc = SLCDriver(endpoint_ip)
else:
    plc = LogixDriver(endpoint_ip)

if plc.open():
    print("PLC connection successful..")

    # AB device driver connected, now connect to clearblade platform mqtt
    mqtt = mySystem.Messaging(device, port=msg_port, use_tls=True)

    def on_disconnect(client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnect from platform mqtt broker..")
            sys.exit()

    def on_connect(client, userdata, flags, rc):
        print("Platform connection succesful, beginning loop..")

    mqtt.on_connect = on_connect 
    mqtt.on_disconnect = on_disconnect
    mqtt.connect()
    
    # Iterate through collection rows reading tags and adding them to list
    while(True):
        
        tag_list = []
        for row in tag_rows:    
            collection_row_tag_name = row['name']
            plc_read = plc.read(collection_row_tag_name)
            list_row= {"name" : plc_read[0], "value": plc_read[1], "type": plc_read[2], "error": plc_read[3]}
            tag_list.append(list_row)

        #convert python list of dicts to json for transport
        json_str = json.dumps(tag_list)
              
        #publish message to given mqtt topic on platform
        mqtt.publish(msg_topic, json_str)
        time.sleep(interval)  

else:
    print("PLC unreachable! check device connection settings..")
    sys.exit()
