import appdaemon.appapi as appapi

# Turn on the specified entity_id on state change of sensor_id

class TurnOn(appapi.AppDaemon):

  def initialize(self):
    # Load Utils and Defaults
    self.utils = self.get_app('Utils')
    self.settings = self.get_app('Defaults').get_defaults()
   
    # TODO: Investigate having multiple entries for each app using yaml rather than splitting
 
    # Register callbacks for state change of sensors
    for sensor in self.args['sensors']:
      self.listen_state(self.motion, sensor)

    # TODO: Iterate over keys of self.settings and parse and inputs

    # Get the brightness offset
    if 'brightness_offset' in self.args:
      self.settings['brightness_offset'] = self.args['brightness_offset']

    # If we are provided with a brightness input then listen for state changes
    if 'brightness_input' in self.args:
      self.listen_state(self.brightness_update, self.args['brightness_input'])
      self.settings['brightness'] = self.get_state(self.args['brightness_input'])
    elif 'brightness' in self.args:
      self.settings['brightness'] = self.args['brightness']

    # Apply the brightness offset
    self.settings['brightness'] = self.utils.get_brightness_value(self.settings['brightness'], self.settings['brightness_offset'])

    # Get the temperature offset
    if 'color_temperature_offset' in self.args:
      self.settings['color_temperature_offset'] = self.args['color_temperature_offset']

    # If we are provided with a color temperature input then listen for state changes
    if "color_temperature_input" in self.args:
      self.listen_state(self.color_temperature_update, self.args["color_temperature_input"]) 
      self.settings['color_temperature'] = self.get_state(self.args['color_temperature_input'])
    elif 'color_temperature' in self.args:
      self.settings['color_temperature'] = self.args['color_temperature']

    # Apply the color temperature offset
    self.settings['color_temperature'] = self.utils.get_color_temperature_value(self.settings['color_temperature'], self.settings['color_temperature_offset']) 

    # Get the light mode if set
    if "light_mode_input" in self.args:
      self.listen_state(self.light_mode_update, self.args["light_mode_input"])
      self.settings['light_mode'] = self.get_state(self.args['light_mode_input'])

    # Get the light scene if provided
    if "light_scene_input" in self.args:
      self.listen_state(self.light_scene_update, self.args["light_scene_input"])
      self.settings['light_scene'] = self.get_state(self.args['light_scene_input'])

    # Get the brightness offset
    if 'turn_off_delay' in self.args:
      self.settings['turn_off_delay'] = self.args['turn_off_delay']

    # Check every 10 seconds to see if entities should remain on
    self.run_every(self.renew_delay, self.datetime(), 10)

  # Turn lights on if the sensor changes state
  def motion(self, entity, attribute, old, new, kwargs):
    #TODO: Consider if illuminance should be in a helper function
    # Don't turn on if the room is too bright
    if "illuminance_sensor_id" in self.args and "illuminance_max_lux" in self.args:
      illuminance = int(self.get_state(self.args["illuminance_sensor_id"]))
      max_illuminance = int(self.args["illuminance_max_lux"]) 
      if illuminance > max_illuminance:
        self.log("Motion detected, but room too bright ({} > {}). Doing nothing.".format(illuminance, max_illuminance))
        return
      else:
        self.log("Room is {}, which is less than {}. Turning on lights".format(illuminance, max_illuminance))
    
    self.log("Motion detected: turning on entity: {}".format(self.args["entities"]))
    self.utils.turn_on_light(self.args['entities'], self.settings)

  # Check to see if the sensor is on, if so, make sure the light delay gets renewed
  def renew_delay(self, kwargs):
    for sensor_id in self.args['sensors']:
      if self.get_state(sensor_id) == "on":
        self.utils.set_delayed_turn_off_time(self.args['entities'], self.settings['turn_off_delay'], self.settings['off_transition_seconds'])

  def brightness_update(self, entity, attribute, old, new, kwargs):
    # Update the saved copy of the brightness and then update the lights
    self.settings['brightness'] = self.utils.get_brightness_value(new, self.settings['brightness_offset'])
    self.utils.update_light_if_on(self.args['entities'], self.settings)

  def color_temperature_update(self, entity, attribute, old, new, kwargs):
    self.log("Temperature of {} updated to {}. Updating {}".format(entity, new, self.args['entities']))  
    self.settings['color_temperature'] = self.utils.get_color_temperature_value(new, self.settings['color_temperature_offset'])
    self.utils.update_light_if_on(self.args['entities'], self.settings)

  def light_mode_update(self, entity, attribute, old, new, kwargs):
    self.log("Mode of {} updated to {}. Updating {}".format(entity, new, self.args['entities']))  
    self.settings['light_mode'] = new
    self.utils.update_light_if_on(self.args['entities'], self.settings)

  def light_scene_update(self, entity, attribute, old, new, kwargs):
    self.log('Scene of {} updated to {}. Updating {}'.format(entity, new, self.args['entities']))  
    self.settings['light_scene'] = new
    self.utils.update_light_if_on(self.args['entities'], self.settings)

