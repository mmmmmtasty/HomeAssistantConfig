import appdaemon.appapi as appapi
import time

class FlicTriggeredModeChange(appapi.AppDaemon):

  def initialize(self):
    # Register callbacks
    self.listen_event(self.mode_change, self.args["trigger_event"], button_name = self.args['trigger_entity_id'])

  # Update the mode and shut down lights if required
  def mode_change(self, event_name, data, kwargs):
    self.log("Mode change for {} to {} after {} triggered {}".format(self.args['house_mode'], self.args['new_mode'], data['button_name'], self.args['trigger_event']))
    # set night mode
    self.select_option(self.args["house_mode"], self.args["new_mode"]) 
    # shutdown lights if specified
    if 'shutdown_entity_id' in self.args:
      self.set_turn_off_time(kwargs)

  def set_turn_off_time(self, kwargs):
    # If this is a group then expand the members
    for current_entity_id in self.args["shutdown_entity_id"].split(','): 
      domain, entity_name = current_entity_id.split('.')
      entity_ids = [current_entity_id]
      if domain == 'group':
        entity_ids = self.get_state(self.args["entity_id"], attribute = 'all')['attributes']['entity_id']
     
       # Make sure the turn_off keys exist in global_vars 
      if 'turn_off' not in self.global_vars:
        self.global_vars['turn_off'] = {}
      
      # Write a turn off time for each expanded entity
      for entity_id in entity_ids:
        self.log("Setting new off time for {}".format(entity_id)) 
        # Make sure a key exists for this entity
        if entity_id not in self.global_vars["turn_off"]:
          self.global_vars['turn_off'][entity_id] = {}
        # Set a turn off time of (now + delay)
        self.global_vars["turn_off"][entity_id]['off_time'] = (self.datetime().timestamp() + int(self.args["delay"]))
        # If we were provided an off transition time then include that as well
        off_transition_seconds = 5
        if 'off_transition_seconds' in self.args:
           off_transition_seconds = self.args["off_transition_seconds"]
        self.global_vars["turn_off"][entity_id]['off_transition_seconds'] = off_transition_seconds
