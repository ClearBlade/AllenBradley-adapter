# AllenBradley-adapter
Python adapter script for reading tags from Allen Bradley PLCs

This script was tested on a Teltonika RUTX11 modem running OpenWRT connected via ethernet to an Allen Bradley Micrologix 1100 PLC.

# Basic requirements

1. Install Python and pip on the modem and ensure the PLC is set up via ethernet with a reachable IP address.

2. Use pip to install the pycomm3 library for communication with Allen Bradley devices.
    - The pycomm3 library and its documentation can be found here [Pycomm3](https://docs.pycomm3.dev/en/latest/index.html).  
    
3. Use pip to install the ClearBlade Python SDK to interact with the Platform.
    - The ClearBlade Python SDK and its documentation can be found here [ClearBlade Python SDK](https://github.com/ClearBlade/ClearBlade-Python-SDK).

4. Create a device on the Platform defined with the selected service account parameter to create an authorization key.

5. A Platform collection with the list of PLC tags to be read that can be edited over time (the script uses the column "name" to reference the tags).

6. A completed adapter_settings row in the adapter_config collection on the Platform named after the device.

# Script requirements

1. The script accepts the Platform authentication credentials via command line arguments (the script name is arg[0]).
    ```python
    SystemKey = sys.argv[1]
    SystemSecret = sys.argv[2]
    SystemUrl = sys.argv[3]    
    DeviceName = sys.argv[4]
    DeviceKey =  sys.argv[5] 
    ```
2. Once a successful connection is made, the script will query the 'adapter_config' collection for the device requirements. The requirements should be stored in the adapter_settings column, and the adapter_name in the table should equal the device name. The settings contain:
    
    - **"endpoint_ip"**             which is the PLC's IP address
    
    - **"msg_port"**                that will be used for the MQTT messages
    
    - **"interval"**                which is used to set the delay between each read in seconds
    
    - **"tag_collection_name"**     which is referenced above as basic requirement #5
    
    - **"msg_topic"**               that the tag value list will be published to on the Platform
    
    - **"allen_bradley_type"**      which is the PLC driver type to load
    
      - For SLC500 and Micrologix devices, use SLCDriver. For all ControlLogix, CompactLogix, and Micro800 PLCs, use the LogixDriver.
   
   An adapter_settings usage example is shown below.
   
   ```json
   {
      "endpoint_ip": "192.168.1.50",
      "msg_port": 1884, 
      "interval": 60, 
      "tag_collection_name": "plc_tag_descriptions", 
      "msg_topic": "cip/micrologix/1100/someTopic", 
      "allen_bradley_type": "SLCDriver" 
   }
   ```
3. The script will use the SDK to query the tag list from the collection, and the tag values will be published to the MQTT topic named in the Platform's settings file. This is where you would create a normalizer code service on the Platform to listen to that topic and attribute the tag values to display meaningfully.
