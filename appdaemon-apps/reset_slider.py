import appdaemon.appapi as appapi

# After a slider has been moved to another value, leave it at that value for a specified delay before resetting to its master's value

# - master_slider
# - slave_slider
# - delay
# - lock_boolean (if this is set then do not update the brightness)
# - house_mode (input_select that has the house's current mode)


class ResetSlider(appapi.AppDaemon):

  def initialize(self):
    # Define a handle to be used in other callbacks
    self.handle = None

    # Create some callbacks
    # If there is only a master slider defined then this must be THE master slider
    if "slave_slider" in self.args: 
      self.listen_state(self.slider_change, self.args["master_slider"])
      self.listen_state(self.slider_change, self.args["slave_slider"])
      self.listen_state(self.slave_mode_change, self.args["house_mode"]) 
    else:
      self.listen_state(self.master_mode_change, self.args["house_mode"]) 

  def slider_change(self, entity, attribute, old, new, kwargs):
    # Don't do anything if this slider is locked
    if self.get_state(self.args["lock_boolean"]) == "on":
      self.log("{} is on, doing nothing...".format(self.args["lock_boolean"]))
      return

    # If this is a slave slider being updated, we either need to lock it at a new value or move it back to the master after a delay
    if entity == self.args["slave_slider"]:
      # Only try and change this slider if it is different from the master now
      if new != self.get_state(self.args["master_slider"]):
        # If we are in the morning or night then we want to set a timer to move the brightness back to the master
        house_mode = self.get_state(self.args["house_mode"])
        if house_mode in ['morning','night']:
          self.log("State change in {} found. Resetting to value of {} in {} seconds".format(self.args["slave_slider"], self.args["master_slider"], self.args["delay"]))  
          # Cancel any existing timers 
          self.cancel_timer(self.handle)
          # Set a new timer
          self.handle = self.run_in(self.reset_slave_slider, self.args["delay"])
        else:
          # Otherwise we just lock the slider
          self.log("House is in '{}' mode. Locking brightness at current level".format(house_mode))
          self.turn_on(entity_id = self.args["lock_boolean"])

    # If this is the master slider, only move the slaves if they are unlocked
    if entity == self.args["master_slider"]:
      if self.get_state(self.args["lock_boolean"]) == "off":
        # Set the value of the slave slider to be the new value of this master slider
        self.reset_slave_slider(kwargs)

  # Set the value of the slave slider to match the value of its master
  def reset_slave_slider(self, kwargs):
    master_value = self.get_state(self.args["master_slider"])
    self.log("Resetting value of {} to {}".format(self.args["slave_slider"], master_value))
    self.select_value(self.args["slave_slider"], master_value)

  # If the house mode changes and this is a slave slider then undo the lock
  def slave_mode_change(self, entity, attribute, old, new, kwargs):
    # Turn off the lock boolean
    self.turn_off(entity_id = self.args["lock_boolean"])

  # If the house mode changes and this is a master slider then wait 2 seconds and set the slider to match the defaut slider
  def master_mode_change(self, entity, attribute, old, new, kwargs):
    # Generate the name of the default slider from the house_mode
    input_slider = "input_slider.{}_brightness".format(new)
    self.run_in(self.master_mode_callback, 2, input_slider = input_slider)

  # Function required to facilitate using the self.run_in above
  def master_mode_callback(self, args):
    self.log("House mode change: resetting {} to value of {}".format(self.args["master_slider"], args["input_slider"]))
    self.select_value(self.args["master_slider"], self.get_state(args["input_slider"])) 
