import appdaemon.appapi as appapi

# Doorbell script to do Sonos and Hue light notification

class Doorbell(appapi.AppDaemon):

  def initialize(self):

    # Register callbacks
    # TODO change this to be triggered on an event
    self.listen_state(self.ring, self.args["sensor"])

  # Flash lights and play doorbell sound if sensor goes to on
  def ring(self, entity, attribute, old, new, kwargs):
    # Only do this if the new status is on
    if new == 'on':
      # Save the current Sonos state
      self.call_service("media_player/sonos_snapshot", entity_id = self.args["sonos"])
      # Save the volume of the Sonos
      volume = self.get_state(self.args["sonos"], attribute = 'volume_level')
      self.log("Saving volume of {} ({})".format(self.args["sonos"], volume))
      # Stop the Sonos
      self.call_service("media_player/media_stop", entity_id = self.args["sonos"])
      # Set the volume of the Sonos to the desired level
      self.log("Setting volume of {} to {}".format(self.args["sonos"], self.args["volume"]))
      self.call_service("media_player/volume_set", entity_id = self.args["sonos"], volume_level = self.args["volume"])
      # Play the doorbell sound
      self.call_service("media_player/play_media", entity_id = self.args["sonos"], media_content_id = self.args["doorbell"], media_content_type = 'MUSIC')
      # Flash all the lights
      self.turn_on(self.args["lights"], flash = 'short')
      # Wait until the doorbell noise has finished and run the restore part
      self.run_in(self.restore, self.args["music_break"])

  def restore(self, kwargs):
      # self.log("Setting volume of {} back to {}".format(self.args["sonos"], volume))
      # self.call_service("media_player/volume_set", entity_id = self.args["sonos"], volume_level = self.args["volume"])
      # Restore the original Sonos state
      self.call_service("media_player/sonos_restore", entity_id = self.args["sonos"])
 
