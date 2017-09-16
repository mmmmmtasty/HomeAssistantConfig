import appdaemon.appapi as appapi
import datetime

# Change the mode of the house at the right times
# Parameters:
# - morning
# - day
# - evening
# - night

class UpdateHouseMode(appapi.AppDaemon):
  def initialize(self):
    # Work out which mode we should be in now and reset it
    current_mode = 'morning'
    if self.time() > self.parse_time(self.args["day_start"]):
      current_mode = 'day' 
    if self.time() > self.parse_time(self.args["evening_start"]):
      current_mode = 'evening' 
    if self.time() > self.parse_time(self.args["night_start"]):
      current_mode = 'night'
    self.update_mode({'new_mode': current_mode}) 
    
    # Work out the times from the config file and register daily callbacks
    self.run_daily(self.update_mode, self.parse_time(self.args["morning_start"]), new_mode = "morning")
    self.run_daily(self.update_mode, self.parse_time(self.args["day_start"]), new_mode = "day")
    self.run_daily(self.update_mode, self.parse_time(self.args["evening_start"]), new_mode = "evening")
    self.run_daily(self.update_mode, self.parse_time(self.args["night_start"]), new_mode = "night")

  def update_mode(self, args):
    current_mode = self.get_state(self.args['house_mode'])
    if current_mode != args['new_mode']:
      self.log("[HOUSE MODE CHANGE] {} {}->{} ".format(self.args['house_mode'], current_mode, args['new_mode']))
      self.select_option(self.args['house_mode'], args['new_mode']) 
      #self.run_in(self.update_mode, 1, new_mode = args['new_mode'])
