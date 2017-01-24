import appdaemon.appapi as appapi
import datetime

# Check to see what needs to be turned off and turn it off
#
class TurnerOfferer(appapi.AppDaemon):

  def initialize(self):
    self.run_every(self.triggered, datetime.datetime.now(), 5)

  def triggered(self, kwargs):
    for entity_id in self.global_vars["turn_off"]:
      self.log("Found entity details: {}".format(self.global_vars["turn_off"][entity_id])) 
