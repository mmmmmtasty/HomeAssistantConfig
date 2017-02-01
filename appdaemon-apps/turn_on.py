import appdaemon.appapi as appapi

# Turn on the specified entities based on a motion detector
# Takes the following parameters
# - sensor
# - entity_ids (comma separated list of entity_ids to turn on or off)
# - input_brightness
# - input_temperature
# - offset (offset from the sepcified brightness)
# - on_transition_seconds
# - TODO add an off_transition!
# - update_transition_seconds
# - delay

class TurnOn(appapi.AppDaemon):

  def initialize(self):
    # Specifiy a handle to use for timings 
    self.handle = None

    # Register callbacks
    self.listen_state(self.motion, self.args["sensor"])
    if 'input_brightness' in self.args:
      self.listen_state(self.brightness_change, self.args["input_brightness"])
    if 'input_temperature' in self.args:
      self.listen_state(self.temperature_change, self.args["input_temperature"])

  # Turn lights on if the sensor triggers on or off
  def motion(self, entity, attribute, old, new, kwargs):
    self.log("Motion detected: turning on entities: {}".format(self.args["entity_id"]))
    self.turn_on_entity(False, kwargs)
    
    # Register a time that this needs to be turned off
    domain, entity_name = self.args["entity_id"].split('.')
    entity_ids = [self.args["entity_id"]]
    # If this is a group then expand the members
    if domain == 'group':
      entity_ids = self.get_state(self.args["entity_ids"], attribute = 'all')['attributes']['entity_id']
   
    # Make sure the turn_off keys exist in globa_vars 
    if 'turn_off' not in self.global_vars:
      self.global_vars['turn_off'] = {}
    # Write a turn off time for every entity
    for entity_id in entity_ids: 
      # Make sure a key exists for this entity
      if entity_id not in self.global_vars["turn_off"]:
        self.global_vars['turn_off'][entity_id] = {}
      # Set a turn off time based of the delay from now 
      self.global_vars["turn_off"][entity_id]['off_time'] = (self.datetime().now() + int(self.args["delay"]))
      # If we were provided an off transition time then include that as well
      if 'off_transition_seconds' in self.args:
        self.global_vars["turn_off"][entity_id]['transition_time'] = self.args["off_transition_seconds"]

  def brightness_change(self, entity, attribute, old, new, kwargs):
    # The brightness we care about changed! Update the brightness of our lights
    self.log("Brightness of {} updated to {}. Updating {}".format(self.args["input_brightness"], new, self.args["entity_id"]))  
    self.turn_on_entity(True, kwargs)

  def temperature_change(self, entity, attribute, old, new, kwargs):
    # The temperature we care about changed! Update the brightness of our lights
    self.log("Temperature of {} updated to {}. Updating {}".format(self.args["input_temperature"], new, self.args["entity_id"]))  
    self.turn_on_entity(True, kwargs)

  def turn_on_entity(self, update,  kwargs):
    entity_id = self.args["entity_id"]
    # Work out how bright we should be setting our lights
    brightness = 0.0
    if 'brightness' in self.args:
      brightness = float(self.get_state(self.args["input_brightness"]))
    if 'offset' in self.args:
      brightness = brightness + float(self.args["offset"])

    # Make sure the brightness is within constraints
    if brightness < 0.0:
      brightness = 0.0
    if brightness > 255.0:
      brightness = 255.0

    # Work out if we should be using colour temperature or xy_color or nothing
    use_temp = False
    color_temp = 0
    xy_color = []
    if self.get_state("input_boolean.temp_not_color") == 'on' and 'input_temperature' in self.args:
      use_temp = True
      color_temp = int(float(self.get_state(self.args["input_temperature"])))
    
    #  Make sure the entity is already on before updating
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
      self.turn_on(entity_id, color_temp = color_temp, brightness = brightness, transition = int(self.args["on_transition_seconds"]) )
    else:
      self.log("Turning on {} at xy_colour {} and brightness {}".format(entity_id, xy_color, brightness))
      self.turn_on(entity_id, xy_color = [float(self.args["x_color"]),float(self.args["y_color"])], brightness = brightness, transition = int(self.args["on_transition_seconds"]) )
  
