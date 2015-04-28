/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of REDHAWK rtl-demo-client.
 *
 * REDHAWK rtl-demo-client is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 *
 * REDHAWK rtl-demo-client is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
 * for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 */
/**
 *
 * Services to interact with the RTL DEMO Application.
 *
 * Created by rxc on 8/29/14.
 **/
angular.module('rtl-rest', ['ngResource', 'ngAnimate', 'SubscriptionSocketService'])
    .service('RTLRest', ['$resource',
        function($resource){
            var self = this;
            var url = '/rtl';

            self.survey = $resource(url+'/survey', {}, {
                status: {method: 'GET'},
                task: {method: 'POST'},
                halt: {method: 'DELETE'}
            });

            self.device = $resource(url+'/device', {}, {
                status: {method: 'GET'},
                configure: {method: 'PUT'}
            });
        }
    ])
    .factory('rtl', ['RTLRest', 'RedhawkNotificationService', 'SubscriptionSocket',
        function(RTLRest, RedhawkNotificationService, SubscriptionSocket) {

            var notify = RedhawkNotificationService;
            var log = {
                info:  function(txt) { console.log('INFO:  '+txt); },
                warn:  function(txt) { console.log('WARN:  '+txt); },
                error: function(txt) { console.log('ERROR: '+txt); }
            };

            var rtl = {};
            rtl.processors = [];

            var Survey = function() {
                var self = this;
                var frequencyConversion = 1000 * 1000;
                var defaultFrequency = 100.1;

                self._update = function(data) {
                    if(data.hasOwnProperty('frequency') && data['frequency']){
                        data['frequency'] /= frequencyConversion;
                    }
                    angular.extend(self, data);
                };
                self._load = function() {
                    RTLRest.survey.status(
                        function(data){
                            if(data.hasOwnProperty('availableProcessing'))
                                angular.copy(data['availableProcessing'], rtl.processors);
                            self._update(data['status']);
                        },
                        function(resp){
                            rtl.connected = false;
                            log.error("Failed to get survey status "+resp.status+": "+resp.statusText)
                        }
                    );
                };
                self._reload = function(){ self._load(); };

                self.task = function(rf_cf, if_cf, processing) {
                    var entity = {};
                    entity.processing = processing;
                    if (rf_cf) {
                        entity.frequency = parseFloat(rf_cf) * frequencyConversion;
                    } else {
                        entity.frequency = defaultFrequency * frequencyConversion;
                    }
                    if (if_cf) {
                        entity.demod_if = parseFloat(if_cf) * frequencyConversion;
                    } else {
                        entity.demod_if = parseFloat(0);
                    }
                    console.log("REST CALL with entity " + JSON.stringify(entity));
                    return RTLRest.survey.task(
                        {},
                        entity,
                        function(data) {
                            if(data['success']) {
                                self._update(data['status']);
                                var tuned_freq = data.status.frequency  + data.status.demod_if / 1e6;
                                //var tuned_freq = (entity.frequency ? entity.frequency : 0) +  (entity.demod_if ? entity.demod_if : 0);
                                notify.success('Successfully tasked to '+ tuned_freq +' MHz and '+processing+'.', 'Task');
                                log.info(JSON.stringify(data));
                            } else {
                                log.error(data['error']);
                                notify.error(data['error'], 'Task');
                            }
                        }, function(resp) {
                            log.error(resp['data']['error']);
                            notify.error(resp['data']['error'], 'Task');
                        }
                    );
                };

                self.halt = function() {
                    return RTLRest.survey.halt({}, {},
                        function(data) {
                            if(data['success']) {
                                log.info(JSON.stringify(data));
                                notify.success('Successfully halted processing', 'Halt');
                                self._reload();
                            } else {
                                log.error(data['error']);
                                notigy.error(data['error'], 'Halt');
                            }
                        }
                    );
                };

                self._load();
            };

            var Device = function() {
                var self = this;

                self.setSimulation = function(value) {
                    if(value == this.simulator) {
                        log.warn("Device simulation is already set to "+value);
                        return
                    }

                    RTLRest.device.configure({}, {simulation: value},
                        function() {
                            self._reload();
                        },
                        function(data) {
                            log.error(data['error']+" : "+data['message']);
                            notify.error(data['message'], data['error']);
                        }
                    );
                };

                self._update = function(data) {
                    if('status' in data && data['status'] != self.status) {
                        var name = data['type'].toUpperCase();
                        if(data['status'] == 'ready')
                            notify.success(name + " is ready.", 'Device');
                        else if(data['status'] == 'unavailable')
                            notify.error(name + " is unavailable", 'Device');
                        else
                            log.warn("Unknown device status of '"+data['status']+" for "+name);
                    }

                    angular.extend(self, data);
                };
                self._load = function() {
                    RTLRest.device.status(
                        function(data){
                            self._update(data);
                        },
                        function(resp){
                            rtl.connected = false;
                            log.error("Failed to get device status "+resp.status+": "+resp.statusText)
                        }
                    );
                };
                self._reload = function(){ self._load(); };

                self._load();
            };

            var Rds = function() {
                var self = this;
                self._update = function(rds) {
                    if (rds) {
                        angular.extend(self, rds);
                    }
                }
            }

            rtl.connected = true;
            rtl.survey = new Survey();
            rtl.device = new Device();
            rtl.rds = new Rds();
            rtl.minDeviceFreq = 23.99e6;
            rtl.maxdeviceFreq = 900e6;
            rtl.minSimFreq = 87.99e6;
            rtl.maxSimFreq = 108.01e6;

            var statusSocket = SubscriptionSocket.createNew();

            statusSocket.addJSONListener(function(data){
                if('type' in data && 'body' in data) {
                    if(data['type'] == 'device') {
                        rtl.device._update(data['body']);
                    } else if(data['type'] == 'survey') {
                        rtl.survey._update(data['body']);
                    } else if(data['type'] == 'rds') {
                        rtl.rds._update(data['body']);
                    } else {
                        log.error("Unhandled Status Notification of type '" + data['type'] + "'"
                        + JSON.stringify(data['body']))
                    }
                } else {
                    log.error("Status Notification missing 'type' and/or 'body'"+JSON.stringify(data))
                }
            });

            statusSocket.connect('/rtl/status', function(){
                console.log("Connected to Status");
            });

            return rtl;
        }
    ])
;
