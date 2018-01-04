import appdaemon.appapi as appapi
from copy import deepcopy

class Defaults(appapi.AppDaemon):
  def initialize(self):
    self.defaults = {}
    self.defaults['brt'] = 150.0
    self.defaults['brightness'] = 150.0
    self.defaults['brt_offset'] = 0.0
    self.defaults['brightness_offset'] = 0.0
    self.defaults['clt'] = 300
    self.defaults['color_temperature'] = 300
    self.defaults['clt_offset'] = 0
    self.defaults['color_temperature_offset'] = 0
    self.defaults['light_mode'] = 'temperature'
    self.defaults['light_scene'] = 'Relax'
    self.defaults['on_tran_secs'] = 1
    self.defaults['on_transition_seconds'] = 1
    self.defaults['off_time'] = 0
    self.defaults['off_tran_secs'] = 3
    self.defaults['off_transition_seconds'] = 3
    self.defaults['up_tran_secs'] = 5
    self.defaults['update_transition_seconds'] = 5
    self.defaults['off_delay'] = 300
    self.defaults['turn_off_delay'] = 300
    self.defaults['xy_color'] = [0.5, 0.5]
    self.defaults['state_lock_time'] = 0

  def get_defaults(self):
    return deepcopy(self.defaults)
