import appdaemon.appapi as appapi

class Shared(appapi.AppDaemon):
  
  # TODO: Update so taht this is passed appdaemon self and uses it differently from self self
  # Turn on an entity, could be a group, lights, switch
  def turn_on(self, entity_id, kwargs):
    # Blindly turn things on for speed - then we can work out exactly what we did and record turn_off times
    
    
    # Work out all entities we have been asked to turn on
    domain, entity_name = entity_id.split('.')
    # If this is a group then expand the members
    # TODO: turn this into a recursive function to expand all groups
    entity_ids = [entity_id]
    if domain == 'group':
      entity_ids = self.get_state(self.args["entity_ids"], attribute = 'all')['attributes']['entity_id']
    
    for entity in entity_ids:
      domain, name = entity.split('.')
      if domain == 'light':

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

  # TODO: Think about changing this so it takes parameters not relying on things being in self.args
  # Work out how bright we should be setting our lights
  def get_brightness(self, kwargs):
    
    brightness = 0.0

    # If we were passed brightness as a value, use that
    if 'brightness' in self.args.keys:
      brightness = float(self.args["brightness"])
    # If we were passed an input to provide the brightness, use that
    elif 'input_brightness' in self.args.keys:
      brightness = float(self.get_state(self.args["input_brightness"]))
    # We weren't passed a valid bightness, return 0.0
    else: 
      return 0.0

    # If there is an offset specified then apply it
    if 'offset' in self.args.keys:
      brightness = brightness  + float(self.args["offset"])
    
    # Confirm brightness is within valid constraints
    if brightness < 0.0:
      brightness = 0.0
    if brightness > 255.0:
      brightness = 255.0

    return brightness
