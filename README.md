# AllenBradley-adapter
Python adapter script for reading tags from Allen Bradley PLCs

This script was tested on a Teltonika RUT11X modem running OpenWRT connected via ethernet to an Allen Bradley Micrologix1100 PLC

# Basic Requirements

1. Install python and pip on the modem and ensure the plc is set up via ethernet with a reachable IP address

2. Use pip to install the pycomm3 library for communication with Allen Bradley devices
    - The pycomm3 library and its documentation can be found here [Pycomm3](https://docs.pycomm3.dev/en/latest/index.html)
    
    
3. Use pip to install the ClearBlade python SDK in order to interact with the platform 
    - The ClearBlade python SDK and its documentation can be found here [ClearBlade Python SDK](https://github.com/ClearBlade/ClearBlade-Python-SDK)

4. The creation of a device on the platform defined with the service account parameter selected to create an authorization key

5. A collection on the platform with the list of plc tags to be read that can be edited over time (the script uses the column "name" to reference the tags)

6. A completed adapter_settings row in the adapter_config collection on the platform named after the device

# Script Requirements

1. The script accepts the platform authentication credentials via command line arguments (the name of the script is arg[0])
    ```
    SystemKey = sys.argv[1]
    SystemSecret = sys.argv[2]
    SystemUrl = sys.argv[3]    
    DeviceName = sys.argv[4]
    DeviceKey =  sys.argv[5] 
    ```
2. Once a successful connection is made the script will query the 'adapter_config' collection for the device requirements, the requirements should be stored in the adapter_settings column and the adapter_name in the table should equal the device name, the settings contains
    
    - **"endpoint_ip"**             which is the ip address of the plc
    
    - **"msg_port"**                that will be used for the mqtt messages
    
    - **"interval"**                which is used to set the delay between each read in seconds
    
    - **"tag_collection_name"**     which is referenced above as basic requirement #5
    
    - **"msg_topic"**               that the list of tag values will be published to on the platform
    
    - **"allen_bradley_type"**      which is the type of plc driver to load
    
      - For SLC500 and Micrologix devices use SLCDriver, for all ControlLogix, CompactLogix and Micro800 plcs use the LogixDriver
   
   An example adapter_settings usage is shown below:
   
   ```
   {
      "endpoint_ip": "192.168.1.50",
      "msg_port": 1884, 
      "interval": 60, 
      "tag_collection_name": "plc_tag_descriptions", 
      "msg_topic": "cip/micrologix/1100/someTopic", 
      "allen_bradley_type": "SLCDriver" 
   }
   ```
3. That's it, the script will use the SDK to query the tag list from the collection and the tag values will be published to the mqtt topic named in the settings file on the platform, here is where you would create a normalizer code service on the platform to listen to that topic and to attribute the tag values to display in a meaningful manner

   
