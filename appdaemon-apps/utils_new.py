import appdaemon.appapi as appapi
import traceback


class Utils(appapi.AppDaemon):

    # Initialise class
    def initialize(self):
        self.default_settings = self.get_app('Defaults').get_defaults()

    # Make sure the brightness and offset result in a value between 10.0 and 255.0
    def get_brt_val(self, brt):
        # Make sure the brightness is a float
        brt = float(brt)
        if brt < 10.0:
            brt = 10.0
        if brt > 255.0:
            brt = 255.0
        return brt

    # Make sure the clt and offset result in a value between 165 and 500
    def get_clt_val(self, clt):
        # Make sure color_temperature is an int
        clt = int(float(clt))
        if clt < 165:
            clt = 165
        if clt > 500:
            clt = 500
        return clt

    # Turn an entity on
    def turn_on_light(self, kwargs):
        if 'update' in kwargs:
            update = kwargs['update']
        else:
            update = False

        # Confirm that entitiess is actually an array here
        entities = kwargs['entities']
        if not isinstance(entities, list):
            entities = [entities]

        for entity in entities:
            # Transitions could be different for updates
            on_tran_secs = self.get_state_attr(entity, 'on_tran_secs')
            if update:
                on_tran_secs = self.get_state_attr(entity, 'up_tran_secs')

            # Lock the state while we mess with it
            self.set_rel_off_time(
                {'entities': entity, 'time_type': 'state_lock_time', 'delay': (int(on_tran_secs) + 1)})

            # Set a turn off time of now + turn_off_delay if this is not an update
            if update is False:
                self.set_rel_off_time(
                    {'entities': entity, 'time_type': 'off_time', 'delay': self.get_state_attr(entity, 'off_delay')})
                # Do nothing else if the entity is already on
                if self.get_state(entity) == 'on':
                    return

            action = 'ON'
            domain = self.split_entity(entity)[0]
            # If this is an update then make sure the entity is already on
            if update and domain != 'switch':
                action = 'UP'
                if self.get_state(entity) == 'off':
                    action = 'NA'
                    self.log('[{}] [{}] Currently off'.format(
                        action, entity))
                    continue

            # If this is a switch then don't send the extra parameters
            if domain == 'switch' and self.get_state(entity) == 'off':
                # self.log('[{}] [{}] Switch, no parameters required'.format(
                #    action, entity))
                self.turn_on(entity)
                continue

            # Otherwise treat it as a light or group of lights
            light_mode = self.get_state_attr(entity, 'light_mode')
            brt = int(float(self.get_state_attr(entity, 'brt')))
            if light_mode == 'temperature':
                clt = int(float(self.get_state_attr(entity, 'clt')))
                self.log('[{}] [{}] color_temp {} and brightness {}'.format(
                    action, entity, clt, brt))
                self.turn_on(
                    entity, color_temp=clt, brightness=brt, transition=on_tran_secs)
            elif light_mode == 'color':
                xy_color = self.get_state_attr(entity, 'xy_color')
                self.log('[{}] [{}] xy_colour {} and brightness {}'.format(
                    action, entity, xy_color, brt))
                self.turn_on(entity, xy_color=xy_color,
                             brightness=brt, transition=on_tran_secs)
            elif light_mode == 'scene':
                group_name = self.friendly_name(entity)
                scene = self.get_state_attr(entity, 'light_scene')
                self.log('[{}] [{}] Hue Scene: {}'.format(
                    action, group_name, settings['light_scene']))
                self.call_service(
                    'light/hue_activate_scene', group_name=group_name, scene_name=scene)
            elif light_mode == 'colorloop_sync':
                pass
            elif light_mode == 'colorloop_split':
                pass



    # Apply updates to a light only if it is already on
    def update_light(self, kwargs):
        self.turn_on_light({'entities': kwargs['entities'], 'update': True})

    # Set the privded attribute to the provided value in the internal state
    def set_state_attr(self, entity, attr, val):
        if 'state' not in self.global_vars:
            self.global_vars['state'] = {}
        if entity not in self.global_vars['state']:
            self.global_vars['state'][entity] = {}

        self.global_vars['state'][entity][attr] = val
        if attr == 'off_time' and val != 0.0:
            stringforme = ''
            for line in traceback.format_stack():
                stringforme += line.strip()
            self.log('setting new off time for {} : {}'.format(entity, stringforme))
        # self.log("{}, {}, {}: {}".format(entity, attr,
        #                                 val, self.global_vars['state'][entity]))

    # Return the value of an attribute for an entity. If none has been set then return the default value
    def get_state_attr(self, entity, attr):
        if 'state' in self.global_vars:
            if entity in self.global_vars['state']:
                if attr in self.global_vars['state'][entity]:
                    return self.global_vars['state'][entity][attr]
        return self.default_settings[attr]

    # Set the off time an array of entities
    def set_off_time(self, entities, time_type, time):
        # Confirm that entities is an array
        if not isinstance(entities, list):
            entities = [entities]

        for entity in entities:
            # If this is a group then expand the members so we reference every entity
            if self.split_entity(entity)[0] == 'group':
                group_entities = self.get_state(entity, attribute='all')[
                    'attributes']['entity_id']
            else:
                group_entities = [entity]

            # Write a turn off time for each entity
            for group_entity in group_entities:
                self.set_state_attr(group_entity, time_type, time)

    # Set a new off time of an offset from self.datetime()
    def set_rel_off_time(self, kwargs):
        self.set_off_time(kwargs['entities'], kwargs['time_type'],
                          (self.datetime().timestamp() + int(kwargs['delay'])))

    def is_locked(self, entity):
        lock_exp = self.get_state_attr(entity, 'state_lock_time')
        if lock_exp > self.datetime().timestamp():
            return True
        else:
            return False
