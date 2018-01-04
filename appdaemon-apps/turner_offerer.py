import appdaemon.appapi as appapi
import time

# Check to see what needs to be turned off and turn it off


class TurnerOfferer(appapi.AppDaemon):

    def initialize(self):
        # Load shared utils
        self.utils = self.get_app('UtilsNew')

        self.run_every(self.triggered, self.datetime(), 5)
        self.run_every(self.triggered_new, self.datetime(), 5)

    def triggered(self, kwargs):
        if 'settings' in self.global_vars:
            for entity_id in self.global_vars['settings']:
                off_time = self.global_vars['settings'][entity_id]['off_time']
                off_time_string = time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(self.global_vars['settings'][entity_id]['off_time']))

                #self.log("{} Off Time: {}".format(entity_id, off_time_string))

                if off_time > self.datetime().timestamp() and off_time != 0.0:
                    off_time_string = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(off_time))
                    now_time_string = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime())
                    #self.log("[NONE] {} {} > {}".format(entity_id, off_time_string, now_time_string))

                if off_time < self.datetime().timestamp() and off_time != 0.0:
                    off_time_string = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(off_time))
                    now_time_string = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime())
                    self.log("[TIMES UP] {} {} < {}".format(
                        entity_id, off_time_string, now_time_string))

                    if "off_transition_seconds" in self.global_vars['settings'][entity_id]:
                        off_transition_seconds = self.global_vars['settings'][entity_id]['off_transition_seconds']
                    else:
                        off_transition_seconds = None

                    self.run_in(self.turn_off_entity, 1, **{
                                'entity_id': entity_id, 'off_tran_secs': off_transition_seconds})

                    # Set the turn off time to be 0.0
                    self.global_vars['settings'][entity_id]['off_time'] = 0.0

    def triggered_new(self, kwargs):
        if 'state' in self.global_vars:
            for entity in self.global_vars['state']:
                off_time = self.utils.get_state_attr(entity, 'off_time')
                off_time_str = time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(off_time))

                #self.log("{} Off Time: {}".format(entity, off_time_str))

                if off_time > self.datetime().timestamp() and off_time != 0.0:
                    off_time_str = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(off_time))
                    now_time_str = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime())
                    #self.log("[NONE] {} {} > {}".format(entity, off_time_str, now_time_str))

                if off_time < self.datetime().timestamp() and off_time != 0.0:
                    off_time_str = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(off_time))
                    now_time_str = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime())
                    self.log("[OFF] {} {} < {}".format(
                        entity, off_time_str, now_time_str))

                    off_tran_secs = self.utils.get_state_attr(
                        entity, 'off_tran_secs')

                    #self.log('off_tran_secs: {}'.format(off_tran_secs))

                    self.run_in(self.turn_off_entity, 1, **{
                                'entity_id': entity, 'off_tran_secs': off_tran_secs})

                    # Set the turn off time to be 0.0
                    self.utils.set_state_attr(entity, 'off_time', 0.0)

    def turn_off_entity(self, kwargs):
        off_tran_secs = kwargs['off_tran_secs']
        entity = kwargs['entity_id']
        domain, entity_name = self.split_entity(entity)
        if self.get_state(entity) == 'on':
            if off_tran_secs is None or domain == 'switch':
                self.log("[FAST OFF] {}".format(entity))
                self.turn_off(entity)
                # Run again for good measure
                self.turn_off(entity)
                self.run_in(self.turn_off_entity, 1, **
                            {'entity_id': entity, 'off_tran_secs': None})
            else:
                self.log("[SLOW OFF] {} {} seconds".format(
                    entity, off_tran_secs))
                self.turn_off(entity, transition=off_tran_secs)
                # Run again for good measure
                self.turn_off(entity, transition=off_tran_secs)
                self.run_in(self.turn_off_entity, 1, **
                            {'entity_id': entity, 'off_tran_secs': off_tran_secs})
