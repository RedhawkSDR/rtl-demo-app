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
angular.module('rtl-rest', ['ngResource', 'toaster', 'ngAnimate', 'SubscriptionSocketService'])
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
    .factory('rtl', ['RTLRest', 'toaster', 'SubscriptionSocket',
        function(RTLRest, toastr, SubscriptionSocket) {

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

                self.task = function(frequency, processing) {
                    return RTLRest.survey.task({},
                        {
                            frequency: parseFloat(frequency) * frequencyConversion,
                            processing: processing
                        }, function(data) {
                            if(data['success']) {
                                self._update(data['status']);
                                toastr.pop('success', 'Task', 'Successfully tasked to '+frequency+' and '+processing+'.');
                                log.info(JSON.stringify(data));
                            } else {
                                log.error(data['error']);
                                toastr.pop('error', 'Task', data['error']);
                            }
                        }, function(resp) {
                            log.error(resp['data']['error']);
                            toastr.pop('error', 'Task', resp['data']['error']);
                        }
                    );
                };

                self.halt = function() {
                    return RTLRest.survey.halt({}, {},
                        function(data) {
                            if(data['success']) {
                                log.info(JSON.stringify(data));
                                toastr.pop('success', 'Halt', 'Successfully halted processing.');
                                self._reload();
                            } else {
                                log.error(data['error']);
                                toastr.pop('error', 'Halt', data['error']);
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
                            toastr.pop('error', data['error'], data['message']);
                        }
                    );
                };

                self._update = function(data) {
                    if('status' in data && data['status'] != self.status) {
                        var name = data['type'].toUpperCase();
                        if(data['status'] == 'ready')
                            toastr.pop('success', 'Device', name + " is ready.");
                        else if(data['status'] == 'unavailable')
                            toastr.pop('error', 'Device', name + " is unavailable.");
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
