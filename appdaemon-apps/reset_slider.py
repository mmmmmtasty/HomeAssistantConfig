import appdaemon.appapi as appapi

# After a slider has been moved to another value, leave it at that value for a specified delay before resetting to its master's value

class ResetSlider(appapi.AppDaemon):

  def initialize(self):
    self.handles = {}
    if 'house_mode' in self.args:
      self.listen_state(self.house_mode_change, self.args['house_mode'])

    for slave_slider in self.args['slave_sliders']:
      self.listen_state(self.slider_change, slave_slider)
    self.listen_state(self.slider_change, self.args['master_slider'])

  def slider_change(self, entity, attribute, old, new, kwargs):
    # If this is a master slider changing then reset all slaves if they aren't locked
    if entity == self.args['master_slider']:
      for slave_slider in self.args['slave_sliders']:
        if self.get_state(self.args['slave_sliders'][slave_slider]['lock_boolean']) == 'off':
          self.reset_slave_slider({'slider': slave_slider})
      return

    # This is definitely a slave being changed, let's react accordingly
    # Don't do anything if this slider is locked
    #if self.get_state(self.args['slave_sliders'][entity]['lock_boolean']) == 'on':
      #self.log("[NONE] {} is locked".format(self.args['slave_sliders'][entity]["lock_boolean"]))
    else:
      # Only try and change this slider if it is different from the master now
      if new != self.get_state(self.args['master_slider']):
        # If we are in the morning or night then we want to set a timer to move the brightness back to the master
        house_mode = self.get_state(self.args['house_mode']) 
        if house_mode in ['morning','night']:
          #self.log("[SLIDER RESET DELAY] {} changed. Resetting to value of {} in {} seconds".format(entity, self.args["master_slider"], self.args["reset_delay"]))  
          # Cancel any existing timers 
          self.cancel_timer(self.handle[entity])
          # Set a new timer
          self.handle[entity] = self.run_in(self.reset_slave_slider, self.args['reset_delay'], **{'slider': entity})
        else:
          # Otherwise we just lock the slider
          #self.log("[SLIDER LOCK] {} House is in '{}' mode. Locking until house mode change".format(entity, house_mode))
          self.turn_on(entity_id = self.args['slave_sliders'][entity]['lock_boolean'])

  # Set the value of the slave slider to match the value of its master
  def reset_slave_slider(self, kwargs):
    master_value = self.get_state(self.args["master_slider"])
    #self.log("[SLIDER RESET] {} to {}".format(kwargs['slider'], master_value))
    self.select_value(kwargs['slider'], master_value)

  # If the house mode changes and this is a slave slider then undo the lock
  def house_mode_change(self, entity, attribute, old, new, kwargs):
    # Turn off the lock boolean for all slaves
    for slave_slider in self.args['slave_sliders']:
      self.turn_off(entity_id = self.args['slave_sliders'][slave_slider]['lock_boolean'])

    # Generate the name of the default slider from the house_mode but only if this is the master
    if 'master' in self.args:
      if self.args['master'] == True:
        input_slider = "input_slider.{}{}".format(new, self.args['house_mode_suffix'])
        self.run_in(self.master_mode_callback, 2, input_slider = input_slider)

  # Function required to facilitate using the self.run_in above
  def master_mode_callback(self, kwargs):
    #self.log("[MASTER SLIDER RESET] House mode change: resetting {} to value of {}".format(self.args['master_slider'], kwargs["input_slider"]))
    self.select_value(self.args['master_slider'], self.get_state(kwargs['input_slider'])) 
