import appdaemon.appapi as appapi

class MotionLightsGeneric(appapi.AppDaemon):

  def initialize(self):
    
    self.handle = None

    # Subscribe to sensors
    if "location_snippet" in self.args:
      # Generate sensor name and register callback
      sensor = "binary_sensor.motion_{}_motion".format(self.args["location_snippet"])
      self.log("Registering callback for sensor: {}".format(sensor))
      self.listen_state(self.motion, sensor)
    else:
      self.log("No location_snippet specified, doing nothing")
    
  def motion(self, entity, attribute, old, new, kwargs):
    if new == "on":
      # Generate name of scenes
      scene = "scene.{}_{}_on".format(self.args["location_snippet"], self.get_state("input_select.house_mode"))
      self.log("Motion detected: turning on scene: {}".format(scene))
      self.turn_on(scene)
      if "delay" in self.args:
        delay = self.args["delay"]
      else:
        delay = 300
      # Cancel any existing timer
      self.cancel_timer(self.handle)
      self.log("Scheduling turn off for {} seconds".format(delay))
      # Launch new timer
      self.handle = self.run_in(self.light_off, delay)
  
  def light_off(self, kwargs):
    scene = "scene.{}_off".format(self.args["location_snippet"])
    self.log("Motion detected: turning on scene: {}".format(scene))
    # If it's a scene we need to turn it on not off
    self.turn_on(scene)

