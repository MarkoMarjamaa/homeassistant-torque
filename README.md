# homeassistant-torque
My fork of Home Assistants Torque plugin

This prevents the problem with Torque sensors to show as 'Entity not available' when HA is started but Torque not yet used. 
Every car has different sensors so they cannot be hardcoded. But with this you can list them in configuration.yaml and sensors are created in HA startup. 

1. Install Torque custom component

- Create directory custom_components/torque2 and copy the files there. The plugin is the also named torque2. 
- Rename your torque-section in configuration.yaml as torque2

2. Get the sensor definitions

- Set logger to log torque as debug
```
logger:
  default: warning

  logs:
      homeassistant.components.torque2.sensor: debug
```

- Restart HA
- Start using Torque. The plugin should list all available sensors. 
- Copy those sensor defintions from log to configuration.yaml

```
- platform: torque2
    email: marko.marjamaa@xxx.xx
    sensors:
       - 16716334:
           Name: 0-100kph Time
           Unit: s
       - 16716388:
           Name: 100-0kph Time
           Unit: s
       - 4:
           Name: Engine Load
           Unit: "%"
```
Remember percentage character needs quotation marks

3. Restart HA and check the plugin does not list sensor definitions in log and the sensors are available at startup. 
