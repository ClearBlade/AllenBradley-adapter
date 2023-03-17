from pycomm3 import SLCDriver, LogixDriver
from clearblade.ClearBladeCore import System, Query
import json, sys, time, os, signal

# a python script to read tags from Allen Bradley Micrologix and ControlLogix PLCs to ClearBlade local edge via MQTT

# nohup $ARGS > /dev/null 2>&1

print("Initializing script: ", sys.argv[0])

try:  
    SystemKey = sys.argv[1]
    SystemSecret = sys.argv[2]
    SystemUrl = sys.argv[3]    
    DeviceName = sys.argv[4]
    DeviceKey =  sys.argv[5] 
    
except: 
    print("Not enough arguments..Script requires 1)SystemKey 2)SystemSecret 3)SystemUrl 4)DeviceName 5)DeviceKey..")
    sys.exit()

try:
    # connect to ClearBlade platform and authenticate
    mySystem = System(SystemKey, SystemSecret, SystemUrl)
    device = mySystem.Device(DeviceName, DeviceKey)

except:
    print("Unable to connect to platform..check configuration settings")
    sys.exit()

try:
    # get device adapter config from collection
    adapter_config_collection = mySystem.Collection(device, collectionName="adapter_config")
    q = Query()
    q.equalTo("adapter_name", DeviceName)
    adapter_configs = adapter_config_collection.getItems(q)
    adapter_settings = adapter_configs[0]['adapter_settings']

except:
    print("Unable to pull adapter_settings from platform..must be stored in adapter_config collection")
    sys.exit()

try:    
    adapter_config = json.loads(adapter_settings)
    endpoint_ip = adapter_config['endpoint_ip']
    msg_port = adapter_config['msg_port']
    interval = adapter_config['interval']
    tag_collection_name = adapter_config['tag_collection_name']
    msg_topic = adapter_config['msg_topic']
    allen_bradley_type = adapter_config['allen_bradley_type']

except:
    print("Adapter configuration is required..must include 'endpoint_ip','msg_port','interval','tag_collection_name','msg_topic','allen_bradley_type'")
    sys.exit()

try:
    # log into the tag collection and grab list of tags
    tags_collection = mySystem.Collection(device, collectionName=tag_collection_name)
    tag_rows = tags_collection.getItems()
    tag_str = []
    for row in tag_rows:
        tag_str.append(row['name'])
    print('Script found ' + str(len(tag_str)) + ' tags..')

except:   
    print("Unable to pull tag list from platform..must be stored in a collection and named in adapter settings as 'tag_collection_name'")
    sys.exit()

try:
    # Define connection to Allen Bradley plc
    if allen_bradley_type == 'SLCDriver':
        plc = SLCDriver(endpoint_ip)
    else:
        plc = LogixDriver(endpoint_ip)

except:
    print("Invalid plc IP address..must be stored in adapter settings as 'endpoint_ip'")
    sys.exit()

def on_connect(client, userdata, flags, rc):        
    print("Platform connection successful, beginning loop..")

def on_disconnect(client, userdata, rc):            
    os.kill(os.getpid(), signal.SIGINT)
    
def on_publish(mqttc, userdata, mid):        
    print("Message published, messageID: " + str(mid))

try:  
    # connect to CB mqtt messenging   
    mqtt = mySystem.Messaging(device, port=msg_port, keepalive=60, use_tls=False)   
    mqtt.on_connect = on_connect   
    mqtt.on_disconnect = on_disconnect
    mqtt.on_publish = on_publish    
    mqtt.connect()

except:
    print("Platform MQTT connection unreachable! check device connection settings..")
    sys.exit()

faults = 0    
while(faults < 12):
    try:
        # attempt to open connection and read tags
        plc.open()
        plc_read = plc.read(*tag_str)
        print("PLC connection successful..")
        plc.close()

    except:
        # allow a certain amount of and time between retries before bailing
        faults += 1
        print("PLC unreachable! check device connection settings.. " + str(faults) + " faults")
        time.sleep(15)
            
    else:   
        #convert python list of dicts to json for transport       
        tag_list = []            
        for row in plc_read:            
            list_row= {"name" : row[0], "value": row[1], "type": row[2], "error": row[3]}           
            tag_list.append(list_row)            
        
        json_str = json.dumps(tag_list)
                
        #publish message to given mqtt topic on platform
        msg = mqtt.publish(msg_topic, json_str)
        msg.wait_for_publish()

        # allow counter to heal if msg gets published
        if msg.is_published():            
            if faults > 0: 
                print("Faults reset to 0..") 
                faults = 0
            time.sleep(interval)

        else:            
            mqtt.disconnect()      
            # something is wrong, bail and restart daemon

os.kill(os.getpid(), signal.SIGINT)
