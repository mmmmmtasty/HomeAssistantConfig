import appdaemon.appapi as appapi

# Check to see what needs to be turned off and turn it off
#
class TurnerOfferer(appapi.AppDaemon):

  def initialize(self):
    self.run_every(self.triggered, self.datetime(), 5)

  def triggered(self, kwargs):
    if "turn_off" in self.global_vars:
      for entity_id in self.global_vars['turn_off']:
        off_time = self.global_vars["turn_off"][entity_id]["off_time"]

        if off_time < self.datetime().timestamp() and off_time != 0.0:
          self.log("[TIMES UP] {} {} < {}".format(entity_id, off_time, self.datetime().timestamp()))

          if "off_transition_seconds" in self.global_vars["turn_off"][entity_id]:
            off_transition_seconds = self.global_vars['turn_off'][entity_id]['off_transition_seconds']
          else:
            off_transition_seconds = None

          self.turn_off_entity({'entity_id': entity_id, 'off_transition_seconds': off_transition_seconds})

          # Set the turn off time to be 0.0
          self.global_vars["turn_off"][entity_id]["off_time"] = 0.0
 
  def turn_off_entity(self, kwargs):
    off_transition_seconds = kwargs['off_transition_seconds']
    entity_id = kwargs['entity_id']
    domain, entity_name = self.split_entity(entity_id)
    self.log("[STATE] {} {}".format(entity_id, self.get_state(entity_id)))
    if self.get_state(entity_id) == 'on':
      if off_transition_seconds is None or domain == 'switch': 
        self.log("[FAST OFF] {}".format(entity_id))
        self.turn_off(entity_id)
      else:
        self.log("[SLOW OFF] {} {} seconds".format(entity_id, off_transition_seconds))
        self.turn_off(entity_id, transition = off_transition_seconds)
      self.run_in(self.turn_off_entity, 1, **{'entity_id': entity_id, 'off_transition_seconds': None})
