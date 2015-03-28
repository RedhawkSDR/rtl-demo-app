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
 * Directives for the RTL DEMO application.
 *
 * Created by Rob Cannon on 8/29/14.
 *
 **/
angular.module('rtl-rest-directives', ['rtl-rest'])
    .directive('deviceStatus', ['rtl',
        function(rtl) {
            return {
                restrict: 'E',
                scope: {},
                templateUrl: 'components/rtl-rest/templates/device-status.html',
                link: function (scope, element, attrs) {
                    scope.device = rtl.device;
                }
            };
        }
    ])
;
