import appdaemon.appapi as appapi

# Check to see what needs to be turned off and turn it off
#
class TurnerOfferer(appapi.AppDaemon):

  def initialize(self):
    self.utils = self.get_app('Utils')
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

          self.utils.turn_off_entity(entity_id, off_transition_seconds)

          # Set the turn off time to be 0.0
          self.global_vars["turn_off"][entity_id]["off_time"] = 0.0
 
