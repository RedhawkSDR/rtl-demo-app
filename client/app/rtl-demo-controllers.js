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
 * Controllers for the RTL DEMO application.
 *
 **/
angular.module('rtl-demo-controllers', ['rtl-rest'])
    .controller('Overview', ['$scope', 'rtl', '$routeParams',
        function($scope, rtl, $routeParams){
            $scope.connected = rtl.connected;
            $scope.survey = rtl.survey;
            $scope.device = rtl.device;
            $scope.rds = rtl.rds;
            $scope.processors = rtl.processors;

            $scope.audioUrl = '/rtl/output/stream';

            $scope.form = {
                frequency: undefined,
                processing: undefined
            };

            $scope.defaultFrequency = 104.5;

            $scope.task = function(){
                $scope.survey.task($scope.form.frequency? $scope.form.frequency : $scope.defaultFrequency, $scope.form['processing']);
            };
            $scope.halt = function(){
                $scope.survey.halt();
            };
            $scope.toggleSimulator = function() {
                $scope.device.setSimulation(!$scope.device.simulator)
            };

            if($routeParams.frequency && $routeParams.processing) {
                $scope.form.frequency  = $routeParams.frequency;
                $scope.form.processing = $routeParams.processing;
                $scope.task();
            }

            $scope.doTune = function(cf) {
                $scope.form.frequency = cf / 1e6;
                $scope.task();
            };

            $scope.widebandMode = "line";
            $scope.setWidebandMode = function(mode) {
                $scope.widebandMode = mode;
            };

            $scope.detailPlotMode = "narrowband";
            $scope.setDetailPlotMode = function(mode) {
                $scope.detailPlotMode = mode;
            };

            // Default to the device being ready unless we hear otherwise
            $scope.ready = true;
            $scope.$watch('device.status', function(status) {
                $scope.ready = (status == 'ready');
            });
            $scope.$watch('survey.processing', function(processing) {
                $scope.running = (processing != null);
            });

            $scope.$watch('survey.frequency', function(freq) {
                if(freq && $scope.form.frequency !== freq) {
                    $scope.form.frequency = freq;
                }
                if (!freq) {
                    $scope.form.frequency = null;
                }
                $scope.running = !!freq;
            });

            $scope.$watch('survey.processing', function(processing) {
                if(!$scope.form.processing) {
                    $scope.form.processing = processing ? processing : $scope.processors[0];
                }
            });
        }
    ])
;
