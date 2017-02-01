import appdaemon.appapi as appapi
import datetime

# Check to see what needs to be turned off and turn it off
#
class TurnerOfferer(appapi.AppDaemon):

  def initialize(self):
    self.run_every(self.triggered, datetime.datetime.now(), 5)

  def triggered(self, kwargs):
    for entity_id in self.global_vars["turn_off"]:
      if self.global_vars["turn_off"][entity_id]["off_time"] > self.datetime().time()
        self.turn_off_entity()
 
  def turn_off_entity(self, kwargs):
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
