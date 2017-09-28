import appdaemon.appapi as appapi

# Turn on the specified entity_id on state change of sensor_id

class TurnOn(appapi.AppDaemon):

  def initialize(self):
    # Load Utils and Defaults
    self.utils = self.get_app('Utils')
    self.settings = self.get_app('Defaults').get_defaults()
   
    # Register callbacks for state change of sensors
    for sensor in self.args['sensors']:
      self.listen_state(self.motion, sensor)

    # TODO: Iterate over keys of self.settings and parse and inputs

    # Save which modes this app should be active in
    if 'active_modes' in self.args and 'active_mode_input' in self.args:
      self.settings['active_modes'] = self.args['active_modes']
      self.settings['active_mode_input'] = self.args['active_mode_input']

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
    self.log("[MOTION] {} {}".format(entity, self.args["entities"]))
    # Don't turn on if the room is too bright
    if "illuminance_sensor_id" in self.args and "illuminance_max_lux" in self.args:
      illuminance = int(self.get_state(self.args["illuminance_sensor_id"]))
      max_illuminance = int(self.args["illuminance_max_lux"]) 
      if illuminance > max_illuminance:
        self.log("[BRIGHTNESS FAIL] {}: {} > {}".format(self.args["illuminance_sensor_id"], illuminance, max_illuminance))
        return
      else:
        self.log("[BRIGHTNESS PASS] {}: {} < {}".format(self.args['illuminance_sensor_id'], illuminance, max_illuminance))
    if self.utils.app_is_active(self.settings):
      self.utils.turn_on_light(self.args['entities'], self.settings)
    else:
      self.log("[NONE] Incorrect mode ({})".format(self.get_state(self.settings['active_mode_input'])))

  # Check to see if the sensor is on, if so, make sure the light delay gets renewed
  def renew_delay(self, kwargs):
    for sensor_id in self.args['sensors']:
      if self.get_state(sensor_id) == "on":
        self.utils.set_delayed_turn_off_time(self.args['entities'], self.settings['turn_off_delay'], self.settings['off_transition_seconds'])

  def brightness_update(self, entity, attribute, old, new, kwargs):
    self.log("[BRIGHTNESS UPDATE] {} {}".format(entity, new))
    self.settings['brightness'] = self.utils.get_brightness_value(new, self.settings['brightness_offset'])
    if self.utils.app_is_active(self.settings):
      self.run_in(self.utils.update_light_if_on, 1, **{'entity_ids': self.args['entities'], 'settings': self.settings})
    else:
      self.log("[NONE] Incorrect mode ({})".format(self.get_state(self.settings['active_mode_input'])))

  def color_temperature_update(self, entity, attribute, old, new, kwargs):
    self.log("[COLOR TEMPERATURE UPDATE] {} {}".format(entity, new))
    self.settings['color_temperature'] = self.utils.get_color_temperature_value(new, self.settings['color_temperature_offset'])
    if self.utils.app_is_active(self.settings):
      self.run_in(self.utils.update_light_if_on, 1, **{'entity_ids': self.args['entities'], 'settings': self.settings})
    else:
      self.log("[NONE] Incorrect mode ({})".format(self.get_state(self.settings['active_mode_input'])))

  def light_mode_update(self, entity, attribute, old, new, kwargs):
    self.log("[LIGHT MODE UPDATE] {} {}".format(entity, new))
    self.settings['light_mode'] = new
    if self.utils.app_is_active(self.settings):
      self.run_in(self.utils.update_light_if_on, 1, **{'entity_ids': self.args['entities'], 'settings': self.settings})
    else:
      self.log("[NONE] Incorrect mode ({})".format(self.get_state(self.settings['active_mode_input'])))

  def light_scene_update(self, entity, attribute, old, new, kwargs):
    self.log("[LIGHT SCENE UPDATE] {} {}".format(entity, new))
    self.settings['light_scene'] = new
    if self.utils.app_is_active(self.settings):
      self.run_in(self.utils.update_light_if_on, 1, **{'entity_ids': self.args['entities'], 'settings': self.settings})
    else:
      self.log("[NONE] Incorrect mode ({})".format(self.get_state(self.settings['active_mode_input'])))

