import appdaemon.appapi as appapi

class Defaults(appapi.AppDaemon):
  def initialize(self):
    self.defaults = {}
    self.defaults['brightness'] = 150.0
    self.defaults['brightness_offset'] = 0.0
    self.defaults['color_temperature'] = 300
    self.defaults['color_temperature_offset'] = 0
    self.defaults['light_mode'] = 'temperature'
    self.defaults['light_scene'] = 'Relax'
    self.defaults['on_transition_seconds'] = 1
    self.defaults['off_transition_seconds'] = 1
    self.defaults['update_transition_seconds'] = 1
    self.defaults['turn_off_delay'] = 300
    #self.defaults['x_color'] = 1
    #self.defaults['y_color'] = 1

  def get_defaults(self):
    return self.defaults
