import appdaemon.appapi as appapi

class Utils(appapi.AppDaemon):
  def initialize(self):
    pass
  
  # Make sure the brightness and offset result in a value between 0 and 255
  def get_brightness_value(self, brightness, offset):
    # Make sure brightness is a float 
    brightness = float(brightness) + float(offset)
    # Confirm brightness is within valid constraints and not just completely off
    if brightness < 10.0:
      brightness = 10.0
    if brightness > 255.0:
      brightness = 255.0
    return brightness

  # Make sure the color_temperature and offset result in a value between 165 and 500
  def get_color_temperature_value(self, color_temperature, offset):
    # Make sure color_temperature is a float 
    color_temperature = int(float(color_temperature)) + int(float(offset))
    # Confirm color_temperature is within valid constraints
    if color_temperature < 165:
      color_temperature = 165
    if color_temperature > 500:
      color_temperature = 500
    return color_temperature

  def turn_on_light(self, entity_ids, settings, update = False):
    # Confirm that entity_ids is actually an array here
    if not isinstance(entity_ids, list):
      entity_ids = [entity_ids]

    on_transition_seconds = int(settings['on_transition_seconds'])
    if update:
      on_transition_seconds = int(settings['update_transition_seconds'])

    for entity_id in entity_ids:
      domain, entity = self.split_entity(entity_id)
      # If this is an update then make sure the entity is already on
      action = 'TURN ON'
      if update:
        action = 'UPDATE'
        if self.get_state(entity_id) == 'off':
          action = 'NONE'
          self.log('[{}] [{}] Currently off'.format(action, entity_id))
          continue
        if domain == 'switch':
          action = 'NONE'
          self.log('[{}] [{}] Updates not relevant for switches'.format(action, entity_id))
          continue

      # If this is a switch then don't send the extra parameters
      if domain == 'switch':
        self.log('[{}] [{}] Switch, no parameters required'.format(action, entity_id))
        self.turn_on(entity_id)
        continue
      
      # Otherwise treat it as a light or group of lights
      if settings['light_mode'] == 'temperature':
        self.log('[{}] [{}] color_temp {} and brightness {}'.format(action, entity_id, settings['color_temperature'], settings['brightness']))
        self.turn_on(entity_id, color_temp = settings['color_temperature'], brightness = settings['brightness'], transition = on_transition_seconds )
      elif settings['light_mode'] == 'color':
        self.log('[{}] [{}] xy_colour {},{} and brightness {}'.format(action, entity_id, settings['x_color'], settings['y_color'], settings['brightness']))
        self.turn_on(entity_id, xy_color = [settings['x_color'],settings['y_color']], brightness = settings['brightness'], transition = on_transition_seconds )
      elif settings['light_mode'] == 'scene':
        group_name = self.friendly_name(entity_id)
        self.log('[{}] [{}] Hue Scene: {}'.format(action, group_name, settings['light_scene']))
        self.call_service('light/hue_activate_scene', group_name = group_name, scene_name = settings['light_scene'])
      elif settings['light_mode'] == 'colorloop_sync':
        pass
      elif settings['light_mode'] == 'colorloop_split':
        pass

    # Set a turn off time of now + turn_off_delay
    self.set_delayed_turn_off_time(entity_ids, settings['turn_off_delay'], settings['off_transition_seconds'])

  # Set the turn off time for a single eneity_id. Expand if it is a group
  def set_turn_off_time(self, entity_ids, turn_off_time, off_transition_seconds):
    # Make sure the turn_off keys exist in global_vars 
    if 'turn_off' not in self.global_vars:
      self.global_vars['turn_off'] = {}

    for entity_id in entity_ids:
      # If this is a group then expand the members
      domain, entity_name = self.split_entity(entity_id)
      if domain == 'group':
        group_entity_ids = self.get_state(entity_id, attribute = 'all')['attributes']['entity_id']
      else:
        group_entity_ids = [entity_id]
  
      # Write a turn off time for each expanded entity
      for group_entity_id in group_entity_ids: 
        # Make sure a key exists for this entity
        if group_entity_id not in self.global_vars["turn_off"]:
          self.global_vars['turn_off'][group_entity_id] = {}
        # Set turn off time
        self.global_vars["turn_off"][group_entity_id]['off_time'] = turn_off_time
        # Include off transition settings
        self.global_vars["turn_off"][group_entity_id]['off_transition_seconds'] = off_transition_seconds

  # Set a new off time of a delay from now. Does not persist values even if they were further out than the new off time
  def set_delayed_turn_off_time(self, entity_ids, turn_off_delay, off_transition_seconds):
    self.set_turn_off_time(entity_ids, (self.datetime().timestamp() + int(turn_off_delay)), off_transition_seconds)

  # Apply updates to a light only if it is already on
  def update_light_if_on(self, entity_ids, settings):
    self.turn_on_light(entity_ids, settings, True)

  def turn_off_entity(self, entity_ids, off_transition_seconds = None):
    self.log("Called for {}".format(entity_ids))
    # Confirm that entity_ids is actually an array here
    if not isinstance(entity_ids, list):
      entity_ids = [entity_ids]

    for entity_id in entity_ids:
      domain, entity_name = self.split_entity(entity_id)
      if off_transition_seconds is None or domain == 'switch': 
        while self.get_state(entity_id) == 'on':
          self.log("[FAST OFF] {}".format(entity_id))
          self.turn_off(entity_id)
      else:
        while self.get_state(entity_id) == 'on':
          self.log("[SLOW OFF] {} {} seconds".format(entity_id, off_transition_seconds))
          self.turn_off(entity_id, transition = off_transition_seconds)

      # TODO: Confirm that the device is actually off

