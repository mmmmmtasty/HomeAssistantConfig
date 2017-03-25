import appdaemon.appapi as appapi

# Check to see what needs to be turned off and turn it off
#
class TurnerOfferer(appapi.AppDaemon):

  def initialize(self):
    self.run_every(self.triggered, self.datetime(), 5)

  def triggered(self, kwargs):
    if "turn_off" in self.global_vars:
      for entity_id in self.global_vars["turn_off"]:
        off_time = self.global_vars["turn_off"][entity_id]["off_time"]
        if off_time < self.datetime().timestamp() and off_time != 0.0:
          self.log("Turning off entity: {} ({} vs. {})".format(entity_id, off_time, self.datetime().timestamp()))
          self.turn_off_entity(entity_id, kwargs)
 
  def turn_off_entity(self, entity_id, kwargs):
    domain, entity_name = entity_id.split('.')
    if "off_transition_seconds" in self.global_vars["turn_off"][entity_id] and domain != "switch":
      self.turn_off(entity_id, transition = self.global_vars["turn_off"][entity_id]["off_transition_seconds"])
    else:
      self.turn_off(entity_id)

    # TODO: Confirm that the device is actually off
    # Set the turn off time to be 0.0
    self.global_vars["turn_off"][entity_id]["off_time"] = 0.0
