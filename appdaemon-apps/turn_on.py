import appdaemon.appapi as appapi

# Turn on the specified entity_id on state change of sensor_id

class TurnOn(appapi.AppDaemon):

  def initialize(self):
    # Register callbacks
    for sensor_id in self.args["sensor_id"].split(','):
      self.log("Registering for {}".format(sensor_id))
      self.listen_state(self.motion, sensor_id)
    if "brightness_input" in self.args:
      self.listen_state(self.brightness_change, self.args["brightness_input"])
    if "temperature_input" in self.args:
      self.listen_state(self.temperature_change, self.args["temperature_input"])
    self.run_every(self.renew_delay, self.datetime(), 10)

  # Turn lights on if the sensor changes state
  def motion(self, entity, attribute, old, new, kwargs):
    # Don't turn on if the room is too bright
    if "illuminance_sensor_id" in self.args and "illuminance_max_lux" in self.args:
      illuminance = int(self.get_state(self.args["illuminance_sensor_id"]))
      max_illuminance = int(self.args["illuminance_max_lux"]) 
      if illuminance > max_illuminance:
        self.log("Motion detected, but room too bright ({} > {}). Doing nothing.".format(illuminance, max_illuminance))
        return
      else:
        self.log("Room is {}, which is less than {}. Turning on lights".format(illuminance, max_illuminance))
    self.log("Motion detected: turning on entity: {}".format(self.args["entity_id"]))
    self.turn_on_entity(False, kwargs)
    
    # Register a time that this needs to be turned off
    self.set_turn_off_time(kwargs)

  # Check to see if the sensor is on, if so, make sure the light delay gets renewed
  def renew_delay(self, kwargs):
    for sensor_id in self.args["sensor_id"].split(','):
      if self.get_state(sensor_id) == "on":
        self.set_turn_off_time(kwargs)

  def set_turn_off_time(self, kwargs):
    # If this is a group then expand the members
    domain, entity_name = self.args["entity_id"].split('.')
    entity_ids = [self.args["entity_id"]]
    if domain == 'group':
      entity_ids = self.get_state(self.args["entity_id"], attribute = 'all')['attributes']['entity_id']
   
    # Make sure the turn_off keys exist in global_vars 
    if 'turn_off' not in self.global_vars:
      self.global_vars['turn_off'] = {}
    
    # Write a turn off time for each expanded entity
    for entity_id in entity_ids: 
      # Make sure a key exists for this entity
      if entity_id not in self.global_vars["turn_off"]:
        self.global_vars['turn_off'][entity_id] = {}
      # Set a turn off time of (now + delay)
      self.global_vars["turn_off"][entity_id]['off_time'] = (self.datetime().timestamp() + int(self.args["delay"]))
      # If we were provided an off transition time then include that as well
      off_transition_seconds = 5
      if 'off_transition_seconds' in self.args:
         off_transition_seconds = self.args["off_transition_seconds"]
      self.global_vars["turn_off"][entity_id]['transition_time'] = off_transition_seconds

  def brightness_change(self, entity, attribute, old, new, kwargs):
    # The brightness we care about changed! Update the brightness of our lights
    self.log("Brightness of {} updated to {}. Updating {}".format(self.args["brightness_input"], new, self.args["entity_id"]))  
    self.turn_on_entity(True, kwargs)

  def temperature_change(self, entity, attribute, old, new, kwargs):
    # The temperature we care about changed! Update the brightness of our lights
    self.log("Temperature of {} updated to {}. Updating {}".format(self.args["temperature_input"], new, self.args["entity_id"]))  
    self.turn_on_entity(True, kwargs)

  def turn_on_entity(self, update,  kwargs):
    entity_id = self.args["entity_id"]
    
    # Work out how bright we should be setting our lights
    brightness = 0.0
    if "brightness" in self.args:
      brightness = self.args["brightness"]
    if "brightness_input" in self.args:
      brightness = float(self.get_state(self.args["brightness_input"]))
    if "brightness_offset" in self.args:
      brightness = brightness + float(self.args["brightness_offset"])

    # Make sure the brightness is within constraints
    if brightness < 0.0:
      brightness = 0.0
    if brightness > 255.0:
      brightness = 255.0

    # Work out if we have an on_transition_seconds
    on_transition_seconds = 1
    if "on_transition_seconds" in self.args:
      on_transition_seconds = int(self.args["on_transition_seconds"])
    if update: 
      if "update_transition_seconds" in self.args:
        on_transition_seconds = int(self.args["update_transition_seconds"])
      else:
        on_transition_seconds = 10

    # Work out if we should be using colour temperature or xy_color or nothing
    use_temp = False
    color_temp = 0
    xy_color = []
    if self.get_state("input_boolean.temp_not_color") == 'on' and "temperature_input" in self.args:
      use_temp = True
      color_temp = int(float(self.get_state(self.args["temperature_input"])))
    
    #  If this is an update then make sure the entity is already on
    if update:
      if self.get_state(entity_id) == 'off':
        self.log("Skipping {} as this is an update and the light is off".format(entity_id))
        return

    # If this is a switch then don't send the extra parameters
    domain,entity = entity_id.split('.')
    if domain == 'switch':
      self.log("Turning on {}".format(entity_id))
      self.turn_on(entity_id)
      return

    # Otherwise treat it as a light or group of lights
    if use_temp:
      self.log("Turning on {} at color_temp {} and brightness {}".format(entity_id, color_temp, brightness))
      self.turn_on(entity_id, color_temp = color_temp, brightness = brightness, transition = on_transition_seconds )
    else:
      self.log("Turning on {} at xy_colour {} and brightness {}".format(entity_id, xy_color, brightness))
      self.turn_on(entity_id, xy_color = [float(self.args["x_color"]),float(self.args["y_color"])], brightness = brightness, transition = on_transition_seconds )
  
