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
        else:
            # Only try and change this slider if it is different from the master now
            if new != self.get_state(self.args['master_slider']):
                # If we are in the morning or night then we want to set a timer to move the brightness back to the master
                house_mode = self.get_state(self.args['house_mode'])
                if house_mode in ['morning', 'night']:
                    # Cancel any existing timers
                    if entity in self.handles:
                        self.cancel_timer(self.handles[entity])
                    # Set a new timer
                    self.handles[entity] = self.run_in(
                        self.reset_slave_slider, self.args['reset_delay'], **{'slider': entity})
                else:
                    # Otherwise we just lock the slider
                    self.turn_on(
                        entity_id=self.args['slave_sliders'][entity]['lock_boolean'])

    # Set the value of the slave slider to match the value of its master
    def reset_slave_slider(self, kwargs):
        master_value = self.get_state(self.args["master_slider"])
        self.select_value(kwargs['slider'], master_value)

    def house_mode_change(self, entity, attribute, old, new, kwargs):
        # Turn off the lock boolean for all slaves
        for slave_slider in self.args['slave_sliders']:
            self.turn_off(
                entity_id=self.args['slave_sliders'][slave_slider]['lock_boolean'])

        # Generate the name of the default slider from the house_mode but only if this is the master
        if 'master' in self.args and self.args['master'] == True:
            input_number = "input_number.{}{}".format(
                new, self.args['house_mode_suffix'])
            self.run_in(self.master_mode_callback,
                        2, input_number=input_number)

        # Reset all sliders to the right value
        for slave_slider in self.args['slave_sliders']:
            self.run_in(self.reset_slave_slider, 3, **{'slider': slave_slider})

    def master_mode_callback(self, kwargs):
        self.select_value(self.args['master_slider'],
                          self.get_state(kwargs['input_number']))
