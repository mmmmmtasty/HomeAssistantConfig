import appdaemon.appapi as appapi

# TODO: This does not control the brightness via REST, that happens in some slider application
# This just controls what happens when it sees external events happen


class LightController(appapi.AppDaemon):

    def initialize(self):
        # Register REST endpoint
        # self.register_endpoint(self.rest_motion)

        self.entities = self.args['entities']
        self.sensors = self.args['sensors']

        # Load shared utils
        self.utils = self.get_app('UtilsNew')

        # Save which modes this app should be active in
        mode_constraint_string = None
        if 'active_modes' in self.args and 'active_mode_input' in self.args:
            mode_constraint_string = "{}".format(
                self.args['active_mode_input'])
            for mode in self.args['active_modes']:
                mode_constraint_string += ",{}".format(mode)

        # Register callbacks for state change of sensors
        if mode_constraint_string is None:
            for sensor in self.sensors:
                self.listen_state(self.motion, sensor, new='on')
        else:
            for sensor in self.sensors:
                self.listen_state(self.motion, sensor,
                                  constrain_input_select=mode_constraint_string, new='on')

        # Listen to the state of the entities in case they are changed by an external party
        for entity in self.entities:
            self.listen_state(self.update_light, entity, attribute='all')

            # Record settings
            for input in ['brt_offset', 'clt_offset', 'on_tran_secs', 'up_tran_secs', 'off_tran_secs', 'off_delay']:
                if input in self.args:
                    self.utils.set_state_attr(entity, input, self.args[input])

            # Record values or listen for inputs if required and apply offsets
            for input in ['brt', 'clt', 'light_mode', 'light_scene']:
                if input in self.args:
                    self.utils.set_state_attr(entity, input, self.args[input])

                input_var = '{}_input'.format(input)
                if input_var in self.args:
                    # Apply an offset if one has been defined and val is a number
                    val = self.get_state(self.args[input_var])
                    if isinstance(val, (int, float)):
                        val += self.get_state_attr(entity,
                                                   "{}_offset".format(input))
                    self.utils.set_state_attr(entity, input, val)
                    # Listen for changes in this input to update internal state and light if on
                    fun_name = '{}_update_state'.format(input)
                    self.listen_state(getattr(self, fun_name),
                                      self.args[input_var])
                    # Listen for changes in this input to update light if relevant
                    if mode_constraint_string is None:
                        self.listen_state(self.update_light,
                                          self.args[input_var])
                    else:
                        self.listen_state(
                            self.update_light, self.args[input_var], constrain_input_select=mode_constraint_string)

            #sself.log('{}: {}'.format(entity, self.global_vars['state'][entity]))

        # Check every 10 seconds to see if entities should remain on
        self.run_every(self.renew_delay, self.datetime(), 10)

    # def rest_motion(self, data):
    #    return {}, 200

    # Turn lights on if the sensor changes state
    def motion(self, entity, attribute, old, new, kwargs):
        self.log("[MOTION] {} {}".format(entity, self.args["entities"]))
        # Don't turn on if the room is too bright
        if "illuminance_sensor_id" in self.args and "illuminance_max_lux" in self.args:
            illuminance = int(self.get_state(
                self.args["illuminance_sensor_id"]))
            max_illuminance = int(self.args["illuminance_max_lux"])
            if illuminance > max_illuminance:
                self.log("[BRT FAIL] {}: {} > {}".format(
                    self.args["illuminance_sensor_id"], illuminance, max_illuminance))
                return
            else:
                self.log("[BRT PASS] {}: {} < {}".format(
                    self.args['illuminance_sensor_id'], illuminance, max_illuminance))
        self.utils.turn_on_light({'entities': self.entities})

    # Check to see if the sensor is on, if so, make sure the light delay gets renewed
    def renew_delay(self, kwargs):
        for sensor in self.sensors:
            if self.get_state(sensor) == 'on':
                for entity in self.entities:
                    self.run_in(self.utils.set_rel_off_time, 1, **{'entities': [
                                entity], 'time_type': 'off_time', 'delay': self.utils.get_state_attr(entity, 'off_delay')})

    def brt_update_state(self, entity, attribute, old, new, kwargs):
        self.log("[BRT UPDATE] {} {}".format(entity, new))
        brt = self.utils.get_brt_val(int(float(new)) +
                                     self.utils.get_state_attr(entity, 'brt_offset'))
        for entity in self.entities:
            self.utils.set_state_attr(entity, 'brt', brt)

    def clt_update_state(self, entity, attribute, old, new, kwargs):
        self.log("[CLT UPDATE] {} {}".format(entity, new))
        clt = self.utils.get_clt_val(int(float(new)) +
                                     self.utils.get_state_attr(entity, 'clt_offset'))
        for entity in self.entities:
            self.utils.set_state_attr(entity, 'clt', clt)

    def light_mode_update_state(self, entity, attribute, old, new, kwargs):
        self.log("[LIGHT MODE UPDATE] {} {}->{}".format(entity, old, new))
        for entity in self.entities:
            self.utils.set_state_attr(entity, 'light_mode', new)

    def light_scene_update_state(self, entity, attribute, old, new, kwargs):
        self.log("[LIGHT SCENE UPDATE] {} {}->{}".format(entity, old, new))
        for entity in self.entities:
            self.utils.set_state_attr(entity, 'light_scene', new)

    def update_light(self, entity, attribute, old, new, kwargs):
        # If this is an initial turn on or an update to an appdaemon input, set it to match the appdaemon stored state
        if entity not in self.entities or old['state'] == 'off':
            #self.log('initial on or update to appdaemon!')
            self.run_in(self.utils.update_light, 1, **
                        {'entities': self.entities})
            return

        # If the light is currently off do nothing
        if new['state'] == 'off':
            return

        # If this is an entity that has changed then update our internal state.
        if not self.utils.is_locked(entity):
            # This was an update from another input, update the relevant inputs
            if old['attributes']['brightness'] != new['attributes']['brightness']:
                if 'brt_input' in self.args:
                    #self.log('setting brt_input')
                    self.select_value(
                        self.args['brt_input'], new['attributes']['brightness'])
                else:
                    #self.log('setting brt directly')
                    self.utils.set_state_attr(
                        entity, 'brt', new['attributes']['brightness'])

            # If the color_temp has been updated put the lights in temperature mode
            if old['attributes']['color_temp'] != new['attributes']['color_temp'] and new['attributes']['color_temp'] != 153 and new['attributes']['color_temp'] != 500:
                if 'clt_input' in self.args:
                    #self.log('setting clt input')                    
                    self.select_value(
                        self.args['clt_input'], new['attributes']['color_temp'])
                else:
                    self.utils.set_state_attr(
                        entity, 'clt', new['attributes']['color_temp'])
                if 'light_mode_input' in self.args:
                    #self.log('setting light mode input to temperature')
                    self.select_option(self.args['light_mode_input'], 'temperature')
                    #self.log('{} \n {} \n {} \n -------------------------------- \n {} \n{}'.format(entity, attribute, old, new, kwargs))
                    return
                else:
                    self.log('setting light mode to temperature directly')
                    self.utils.set_state_attr(entity, 'light_mode', 'temperature')
                    return

            # If the xy_color has been updated put the lights in color mode
            if old['attributes']['xy_color'] != new['attributes']['xy_color']:
                # TODO: Update this if we implement color pickers
                self.utils.set_state_attr(
                    entity, 'xy_color', new['attributes']['xy_color'])
                if 'light_mode_input' in self.args:
                    #self.log('setting light mode input to color')
                    self.select_option(self.args['light_mode_input'], 'color')
                    #self.log('{} \n {} \n {} \n -------------------------------- \n {} \n{}'.format(entity, attribute, old, new, kwargs))
                    return
                else:
                    #self.log('setting light mode to color directly')
                    self.utils.set_state_attr(entity, 'light_mode', 'color')
                    return
