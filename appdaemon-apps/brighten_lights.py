
import appdaemon.appapi as appapi

# If we are in night or morning mode, brighten the lights if someone continues to be in the area
#
# Takes the following parameters
# - sensors
# - brightness_slider
# - max_brightness_slider

# TODO update to recognise motion across all sliders
class BrightenLights(appapi.AppDaemon):

  def initialize(self):
    # Define a handle to be used for all timers
    self.handle = None

    # Register callbacks for all sensors we were passed
    for sensor in self.args["sensors"].split(","):
      self.listen_state(self.motion, sensor)

  # On motion brighten the lights in 20 seconds 
  def motion(self, entity, attribute, old, new, kwargs):
    # Don't do anything if we are already at max brightness
    if  int(float(self.get_state(self.args["brightness_slider"]))) == int(float(self.get_state(self.args["max_brightness_slider"]))):
      return
    # If there is still movement in 20 seconds, then start bumping the brightness up
    if new == 'on':
      self.run_in(self.brighten, 20, entity_id = entity, last_increase = 0)

  # Increase the local brightness if the sensor is still on
  def brighten(self, kwargs):
    # If the motion sensor is still on, increase the brightness
    if self.get_state(kwargs["entity_id"]) == 'on':
      current_brightness = float(self.get_state(self.args["brightness_slider"]))
      max_brightness = float(self.get_state(self.args["max_brightness_slider"]))
      # Increase the brightness by 6% of the difference between current and max to start, then double that every time up to max
      if kwargs["last_increase"] == 0:
        current_increase = (max_brightness - current_brightness) * 0.06
        new_brightness = current_brightness + current_increase
      else:
        current_increase = float(kwargs["last_increase"]) * 2.0
        new_brightness = current_brightness + current_increase
      # Make sure we are not going above the max brightness
      if new_brightness > max_brightness:
        new_brightness = max_brightness
      self.log("Increasing brightness from {} to {}".format(current_brightness, new_brightness))
      self.select_value(self.args["brightness_slider"], new_brightness)
      # Check again in 20 seconds
      self.run_in(self.brighten, 20, entity_id = kwargs["entity_id"], last_increase = current_increase)
