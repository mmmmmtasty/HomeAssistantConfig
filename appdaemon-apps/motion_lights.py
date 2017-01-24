import appdaemon.appapi as appapi
import time

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

class MotionLights(appapi.AppDaemon):

  def initialize(self):
    # Specifiy a handle to use for timings 
    self.handle = None

    # Register callbacks
    self.listen_state(self.motion, self.args["sensor"])
    self.listen_state(self.brightness_change, self.args["input_brightness"])
    self.listen_state(self.temperature_change, self.args["input_temperature"])

  # Turn lights on if the sensor triggers on or off
  def motion(self, entity, attribute, old, new, kwargs):
    self.log("Motion detected: turning on entities: {}".format(self.args["entity_ids"]))
    self.turn_on_lights(False, kwargs)
    
    # Register a time that this needs to be turned off
    domain, entity_name = self.args["entity_ids"].split('.')
    entity_ids = [self.args["entity_ids"]]
    # If this is a group then expand the members
    if domain == 'group':
      entity_ids = self.get_state(self.args["entity_ids"], attribute = 'all')['attributes']['entity_id']
   
    self.log("Setting turn off times for these entities: {}".format(entity_ids))
    
    # Set the off time for each entity 
    for entity_id in entity_ids: 
      if 'turn_off' not in self.global_vars:
        self.global_vars['turn_off'] = {}
      if entity_id not in self.global_vars["turn_off"]:
        self.global_vars['turn_off'][entity_id] = {}
      domain, entity = entity_id.split('.')
      self.global_vars["turn_off"][entity_id]['off_time'] = (time.time() + int(self.args["delay"]))
      if domain == 'light':
        self.global_vars["turn_off"][entity_id]['transition_time'] = self.args["off_transition_seconds"]

    self.log("Turn_off: {}".format(self.global_vars["turn_off"]))

    # Cancel any old timers
    self.cancel_timer(self.handle)
    self.log("Scheduling turn off for {} seconds".format(self.args["delay"]))
    # Set a new timer to turn the lights off in the specified amount of time
    self.handle = self.run_in(self.turn_off_entities, self.args["delay"])
 
  def turn_off_entities(self, kwargs):
    # If the motion sensor is still active then delay this again
    if self.get_state(self.args["sensor"]) == 'on':
      self.log("{} is still on, delaying turning off by {} seconds".format(self.args["sensor"], self.args["delay"]))
      self.handle = self.run_in(self.turn_off_entities, self.args["delay"])
      return
    self.log("Turning off entities: {}".format(self.args["entity_ids"]))
    for entity_id in self.args["entity_ids"].split(","):
      # If this is a switch then just turn it off
      #domain,entity = entity_id.split('.')
      #if domain == 'switch':
      self.turn_off(entity_id)
      #  continue
      # Otherwise we assume this is a light or a group of lights and send through the transition
      #self.turn_off(entity_id)
      # TODO raise a bug request here - we should be able to call this with a transition but just get "Invalid Service";, and the turn_off helper function does not take kwargs
      #self.call_service("homeassistant.turn_off", entity_id = entity_id, transition = self.args["off_transition_seconds"])

  def brightness_change(self, entity, attribute, old, new, kwargs):
    # The brightness we care about changed! Update the brightness of our lights
    self.log("Brightness of {} updated to {}. Updating {}".format(self.args["input_brightness"], new, self.args["entity_ids"]))  
    self.turn_on_lights(True, kwargs)

  def temperature_change(self, entity, attribute, old, new, kwargs):
    # The temperature we care about changed! Update the brightness of our lights
    self.log("Temperature of {} updated to {}. Updating {}".format(self.args["input_temperature"], new, self.args["entity_ids"]))  
    self.turn_on_lights(True, kwargs)

  def turn_on_lights(self, update,  kwargs):
    # Work out how bright we should be setting our lights
    brightness = float(self.get_state(self.args["input_brightness"])) + float(self.args["offset"])
    if brightness < 0.0:
      brightness = 0.0
    if brightness > 255.0:
      brightness = 255.0
    # Work out if we should be using colour temperature or xy_color
    use_temp = None
    color_temp = 0
    xy_color = []
    if self.get_state("input_boolean.temp_not_color") == 'on':
      use_temp = True
      color_temp = int(float(self.get_state(self.args["input_temperature"])))
    else:
      use_temp = False
    # Split the entity_id array to get all the entities we need to turn on 
    for entity_id in self.args["entity_ids"].split(","):
      # If we are only supposed to update this one, then make sure it is already on before updating
      if update:
        if self.get_state(entity_id) == 'off':
          self.log("Skipping {} as this is an update and the light is off".format(entity_id))
          continue
      # If this is a switch then don't send the extra parameters
      domain,entity = entity_id.split('.')
      if domain == 'switch':
        self.log("Turning on {}".format(entity_id))
        self.turn_on(entity_id)
        continue
      # Otherwise treat it as a light or group of lights
      if use_temp:
        self.log("Turning on {} at color_temp {} and brightness {}".format(entity_id, color_temp, brightness))
        self.turn_on(entity_id, color_temp = color_temp, brightness = brightness, transition = int(self.args["on_transition_seconds"]) )
      else:
        self.log("Turning on {} at xy_colour {} and brightness {}".format(entity_id, xy_color, brightness))
        self.turn_on(entity_id, xy_color = [float(self.args["x_color"]),float(self.args["y_color"])], brightness = brightness, transition = int(self.args["on_transition_seconds"]) )
  
