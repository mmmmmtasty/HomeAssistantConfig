import appdaemon.appapi as appapi
import time


class FlicTriggeredModeChange(appapi.AppDaemon):

    def initialize(self):
        # Register callbacks
        self.listen_event(
            self.mode_change, self.args["trigger_event"], button_name=self.args['trigger_entity_id'])
        # Load shared utils
        self.utils = self.get_app('UtilsNew')

    # Update the mode and shut down lights if required
    def mode_change(self, event_name, data, kwargs):
        self.log("Mode change for {} to {} after {} triggered {}".format(
            self.args['house_mode'], self.args['new_mode'], data['button_name'], self.args['trigger_event']))
        # set night mode
        self.select_option(self.args["house_mode"], self.args["new_mode"])
        # shutdown lights if specified
        if 'shutdown_entity_ids' in self.args:
            self.set_turn_off_time(self.args['shutdown_entity_ids'])

    def set_turn_off_time(self, entity_ids):
        # First do this for new style lights
        self.utils.set_rel_off_time(
            {'entities': entity_ids, 'time_type': 'off_time', 'delay': self.args['delay']})

        self.log(entity_ids)

        # Then the old style lights
        # If this is a group then expand the members
        for current_entity_id in entity_ids:
            domain, entity_name = current_entity_id.split('.')
            all_entity_ids = [current_entity_id]

               # Make sure the turn_off keys exist in global_vars
            if 'settings' not in self.global_vars:
                self.global_vars['settings'] = {}

            # Write a turn off time for each expanded entity
            for entity_id in all_entity_ids:
                # Make sure a key exists for this entity
                if entity_id not in self.global_vars['settings']:
                    self.global_vars['settings'][entity_id] = {}
                # Set a turn off time of (now + delay)
                new_timestamp = (self.datetime().timestamp() +
                                 int(self.args["delay"]))
                time_string = time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(new_timestamp))
                self.log("Setting new off time for {} ({})".format(
                    entity_id, time_string))
                self.global_vars['settings'][entity_id]['off_time'] = new_timestamp
                # If we were provided an off transition time then include that as well
                off_transition_seconds = 5
                if 'off_transition_seconds' in self.args:
                    off_transition_seconds = self.args["off_transition_seconds"]
                self.global_vars['settings'][entity_id]['off_transition_seconds'] = off_transition_seconds

        # Set the light modes back to temperature
        for entity in entity_ids:
            domain, entity_name = self.split_entity(entity)
            if domain == 'light':
                self.select_option('input_select.{}_light_mode'.format(entity_name), 'temperature')
