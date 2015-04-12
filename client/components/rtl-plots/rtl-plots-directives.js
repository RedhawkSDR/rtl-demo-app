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
 * Created by Rob Cannon on 9/22/14.
 */
angular.module('rtl-plots', ['SubscriptionSocketService', 'toastr'])
    .config(function(toastrConfig) {
        angular.extend(toastrConfig, {
            positionClass: 'toast-bottom-right'
        });
    })
    .service('plotDataConverter', ['Modernizr', function(Modernizr){
        /*
         Create a map to convert the standard REDHAWK BulkIO Formats
         into Javascript equivalents.
         ----
         byte      = 8-bit signed
         char      = 8-bit unsigned
         octet     = 8-bit The signed-ness is undefined
         short     = 16-bit signed integer
         ushort    = 16-bit unsigned integer
         long      = 32-bit signed integer
         ulong     = 32-bit unsigned integer
         longlong  = 64-bit signed integer
         ulonglong = 64-bit unsigned integer
         float     = 32-bit floating point
         double    = 64-bit floating point
         ----
         */
        var conversionMap = {
            byte: Int8Array,
            char: Uint8Array,
            octet: Uint8Array,
            ushort: Uint16Array,
            short: Int16Array,
            long: Int32Array,
            ulong: Uint32Array,
            longlong: undefined, //This should be 64-bit
            ulonglong: undefined, //This should be 64-bit
            float: Float32Array,
            double: Float64Array
        };
        var defaultConversion = Float32Array;

        return function(type) {
            var fn = conversionMap[type];

            if(type == 'octet')
                console.log("Plot::DataConverter::WARNING - Data type is 'octet' assuming unsigned.");

            if(!fn) {
                console.log("Plot::DataConverter::WARNING - Data type is '"+type+"' using default.");
                fn = defaultConversion;
            }

            return function(data) { return new fn(data); };
        };
    }])
    .service('plotNotSupportedError', [function(){
        return function(element) {
            element.html('<div class="rtl-plots-error">Plotting is not supported by this browser.</div>');
        }
    }])
    .service('RedhawkNotificationService', [
        'toastr',
        function(toastr){
            var self = this;
            self.enabled = true;

            self.msg = function(severity, message, subject) {
                if (this.enabled) {
                    var title = subject || severity.toUpperCase();
                    console.log("[" + severity.toUpperCase() + "] :: " + message);
                    switch (severity) {
                        case 'error':
                            toastr.error(message, title);
                            break;
                        case 'success':
                            toastr.success(message, title);
                            break;
                        case 'info':
                        default:
                            toastr.info(message, title);
                            break;
                    }
                }
            };

            self.error = function(text, subject) {
                this.msg("error", text, subject);
            };
            self.info = function(text, subject) {
                this.msg("info", text, subject);
            };
            self.success = function(text, subject) {
                this.msg("success", text, subject);
            };

            self.enable = function(enable) {
                this.enabled = enable;
            };
        }
    ])
    .directive('rtlPlot', ['SubscriptionSocket', 'plotDataConverter', 'plotNotSupportedError', '$interval', 'RedhawkNotificationService',
        function(SubscriptionSocket, plotDataConverter, plotNotSupportedError, $interval, RedhawkNotificationService){
            return {
                restrict: 'E',
                scope: {
                    width: '@',
                    height: '@',
                    url: '@',
                    type: '@',
                    doTune: '&',
                    useGradient: '=?',
                    cmode: '@?',
                    plotType: '@',
                    autol: '@',
                    tuneContext: '=',
                    form: "="
                },
                template: '<div style="width: {{width}}; height: {{height}};" ></div>',
                link: function (scope, element, attrs) {
                    if(!SubscriptionSocket.isSupported() || !SubscriptionSocket.isBinarySupported()) {
                        plotNotSupportedError(element);
                        return;
                    }
                    var plotSocket = SubscriptionSocket.createNew();

                    //use one of the following two lines
                    var RUBBERBOX_ACTION = 'zoom'; //left-click will zoom, ctr-left-click will do drag-tune (if enabled)
                    //var RUBBERBOX_ACTION = 'select'; //left-click will do drag-tune (if enabled), ctr-left-click will zoom

                    var RUBBERBOX_MODE = 'horizontal';

                    var accordionDrag = false;

                    if(!angular.isDefined(scope.useGradient))
                        scope.useGradient = true;

                    //wideband tuned frequency
                    var rf_cf;

                    //narrowband IF
                    var if_cf = 0;

                    var target_freq;

                    //narrowband bandwidth
                    var nb_bw = 100e3;

                    //wideband bandwidth
                    var wb_bw;

                    var MIN_WB_SPECTRUM = 25e6;

                    var MAX_WB_SPECTRUM = 900e6;

                    /**
                     * plot rendering mode
                     *   "IN" = Index, "AB" = Abscissa,
                     *   "MA" = Magnitude, "PH" = Phase,
                     *   "RE" = Real,
                     *   "IM" = Imaginary,
                     *   "LO" or "D1" = 10log,
                     *   "L2" or "D2" = 20log,
                     *   "RI" or "IR" = Real vs. Imaginary
                     *   "AB" = Abscissa
                     *   "PH" = Phase
                     * @type {string[]}
                     */
                    var validCMode = ['IN', 'MA', 'RE', 'IM', 'L0', 'D1', 'L2', 'D2', 'RI', 'IR', 'AB', 'PH'];
                    var cmode = 'D2';
                    if(angular.isDefined(scope.cmode) && scope.cmode != "") {
                        if(validCMode.indexOf(scope.cmode) == -1) {
                            console.log("WARN::Invalid cmode '"+scope.cmode+"' setting to '"+cmode+"'.");
                        } else {
                            cmode = scope.cmode;
                        }
                    }

                    //sigplot objects
                    var plot,
                        raster,
                        activePlot,
                        activePlotLayer,
                        accordion //sigplot plug-in, used here to display vertical line at tuned frequency

                    var tunedWhileZoomed = false;

                    var TUNE_STEP = 20e3;

                    var STEP_DELAY = 300;

                    var BOUNDARY_FACTOR = 0.1;

                    var pan_control = '';

                    var pan;

                    var accordion_pixel_loc;

                    var leftButton, rightButton;

                    var ghostAccordion;

                    //Since freq is on MHz scale, we need some tolerance when comparing click-point to some value
                    var clickTolerance = 200; //TODO set value automatically as a multiple of xdelta, to work with any data scale

                    //settings used when plot is created. Will be overridden from received SRI
                    var defaultSettings = {
                        xdelta:10.25390625,
                        xstart: -1,//ensure change is detected with first SRI
                        xunits: 3,
                        ydelta : 0.09752380952380953,
                        ystart: 0,
                        yunits: 3,
                        subsize: 4097,
                        size: 32768,
                        format: 'SF'
                    };

                    //apply new values from SRI to this object
                    scope.plotSettings = angular.copy(defaultSettings);
                    scope.rasterSettings = angular.copy(defaultSettings);

                    var plotOptions = {
                        autohide_panbars: true,
                        autox: 3, //auto-scale min and max x values
                        autoy: 3, //auto-scale min and max y values
                        legend: false, //don't show legend of traces being plotted
                        all: true, //show all plot data, rather than partial range with pan bars
                        cmode: cmode,
                        xcnt: 'continuous',
                        rubberbox_action: RUBBERBOX_ACTION,
                        rubberbox_mode: RUBBERBOX_MODE, //horizontal mode not supported when rubberbox_action == 'zoom'
                        colors: {bg: "#222", fg: "#888"}
                    };


                    if (scope.autol && (scope.plotType === 'line' || scope.plotType === 'dots')) {
                        angular.extend(plotOptions, {'autol': scope.autol});
                    }

                    //Show readout (values under plot, updated as cursor moves) only for wideband plot
                    if (scope.url.indexOf('psd/fm') >= 0 || scope.url.indexOf('psd/narrowband') >= 0) {
                        angular.extend(plotOptions, {'noreadout': true});
                    }

                    scope.element = element;

                    //we have to wait until the plot's parent div is ready before drawing a plot in its canvas
                    scope.$watch(function(scope) { return scope.element[0] },
                        function(e) {
                            if (!plot && (scope.plotType === 'line' || scope.plotType === 'dots')) {
                                createPlot(plotOptions);
                            } else if (!raster && scope.plotType === 'raster') {
                                createRaster(rasterOptions);
                            }
                        }
                    );

                    var createPlot = function(options) {
                        options = options || {};
                        activePlot = plot = new sigplot.Plot(element[0].firstChild, options);
                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            //mouse listeners used to provide click-tuning and drag-tuning
                            plot.addListener('mdown', plotMDownListener);
                            plot.addListener('mup', plotMupListener);
                        }

                        if(scope.useGradient) {
                            plot.change_settings({
                                fillStyle: [
                                    "rgba(255, 255, 100, 0.7)",
                                    "rgba(255, 0, 0, 0.7)",
                                    "rgba(0, 255, 0, 0.7)",
                                    "rgba(0, 0, 255, 0.7)"
                                ]
                            });
                        }

                    };

                    var addButtons = function(style) {
                        var bounds = currentZoomBounds();
                        var leftButtonPos = {
                            x: bounds.x1 + 15,
                            y: bounds.y1 + 15
                        };
                        var rightButtonPos = {
                            x: bounds.x2 - 15,
                            y: bounds.y1 + 15
                        };
                        var buttonSettings = {
                            position: {x: leftButtonPos.x, y: leftButtonPos.y},
                            direction: 'left',
                            id: 'left'
                        };
                        if (style) {
                            buttonSettings.strokeStyle = style;
                        }
                        leftButton = new sigplot.ButtonPlugin(buttonSettings);
                        activePlot.add_plugin(leftButton, activePlotLayer + 3);
                        leftButton.addListener('selectevt', leftButtonListener);
                        buttonSettings = {
                            position: {x: rightButtonPos.x, y: rightButtonPos.y},
                            direction: 'right',
                            id: 'right'
                        };
                        if (style) {
                            buttonSettings.strokeStyle = style;
                        }
                        rightButton = new sigplot.ButtonPlugin(buttonSettings);
                        activePlot.add_plugin(rightButton, activePlotLayer + 4);
                        rightButton.addListener('selectevt', rightButtonListener);
                    };

                    var leftButtonListener = function(e) {
                        if (e.id === 'left') {
                            target_freq = Math.max(rf_cf - wb_bw, MIN_WB_SPECTRUM);
                            scope.tuneContext.handleTune();
                        }
                    };

                    var rightButtonListener = function(e) {
                        if (e.id === 'right') {
                            target_freq = Math.min(rf_cf + wb_bw, MAX_WB_SPECTRUM);
                            scope.tuneContext.handleTune();
                        }
                    };

                    var inRectangle = function(rect, x, y) {
                        return (x >= rect.x  && x <= rect.x + rect.width && y >= rect.y && y <= rect.y + rect.height);
                    };

                    var updateButtons = function() {
                        leftButton.setEnabled(rf_cf - wb_bw / 2 >= MIN_WB_SPECTRUM);
                        rightButton.setEnabled(rf_cf + wb_bw / 2 <= MAX_WB_SPECTRUM);
                    };

                    var setPlotBounds = function() {
                        var bounds = currentZoomBounds();
                        wb_bw = bounds.xmax - bounds.xmin;
                        console.log("SET WB BW " + wb_bw);
                    };

                    var overlayPlot = function(overrides, options) {
                        options = options || {};
                        var optionsCopy = angular.extend(options, {layerType: sigplot.Layer1D});
                        activePlotLayer = plot.overlay_array(null, overrides, options);

                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            accordion = new sigplot.AccordionPlugin({
                                draw_center_line: true,
                                shade_area: true,
                                draw_edge_lines: true,
                                direction: "vertical",
                                edge_line_style: {strokeStyle: "#FF2400"},
                                prevent_drag: true
                            });
                            ghostAccordion = new sigplot.AccordionPlugin({
                                draw_center_line: true,
                                shade_area: true,
                                draw_edge_lines: true,
                                direction: "vertical",
                                edge_line_style: {strokeStyle: "#881200"},
                                center_line_style: {strokeStyle: "#505050"},
                                fill_style: {opacity: 0.4, fillStyle: 'rgb(0,0,0)'},
                                prevent_drag: true
                            });
                            plot.add_plugin(accordion, activePlotLayer + 1);//plug-ins are drawn in separate layers
                            ghostAccordion.set_center(-nb_bw);
                            ghostAccordion.set_width(nb_bw);
                            plot.add_plugin(ghostAccordion, activePlotLayer + 2)

                            addButtons();
                        }
                    };

                    var rasterOptions = {
                        all: true,
                        expand: true,
                        autol: 5,
                        autox: 3,
                        autohide_panbars: true,
                        xcnt: 0,
                        colors: {bg: "#222", fg: "#888"},
                        nogrid: true,
                        cmode: cmode,
                        rubberbox_action: RUBBERBOX_ACTION,
                        rubberbox_mode: RUBBERBOX_MODE
                    };

                    if (scope.autol && scope.plotType === 'raster') {
                        angular.extend(rasterOptions, {'autol': scope.autol});
                    }

                    var createRaster = function(options) {
                        options = options || {};
                        activePlot = raster = new sigplot.Plot(element[0].firstChild, options);
                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            raster.addListener('mdown', plotMDownListener);
                            raster.addListener('mup', plotMupListener);
                        }

                    };

                    var overlayRaster = function(overrides, options) {
                        var overridesCopy = angular.copy(overrides);
                        activePlotLayer = raster.overlay_pipe(angular.extend(overridesCopy, {type: 2000, pipe: true, pipesize: 1024 * 1024 * 5}), options);

                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            accordion = new sigplot.AccordionPlugin({
                                draw_center_line: false,
                                shade_area: true,
                                draw_edge_lines: true,
                                direction: "vertical",
                                edge_line_style: {strokeStyle: "#FF2400"},
                                prevent_drag: true
                            });
                            ghostAccordion = new sigplot.AccordionPlugin({
                                draw_center_line: false,
                                shade_area: true,
                                draw_edge_lines: true,
                                direction: "vertical",
                                edge_line_style: {strokeStyle: "#881200"},
                                center_line_style: {strokeStyle: "#505050"},
                                fill_style: {opacity: 0.4, fillStyle: 'rgb(0,0,0)'},
                                prevent_drag: true
                            });
                            raster.add_plugin(accordion, activePlotLayer + 1);
                            ghostAccordion.set_center(-nb_bw);
                            ghostAccordion.set_width(nb_bw);
                            raster.add_plugin(ghostAccordion, activePlotLayer + 2);
                            addButtons('rgb(250,250,250');
                        }
                    };

                    var lastMouseDown = {
                        x: undefined,
                        y: undefined
                    };

                    var plotBoundary = function(x) {
                        var bounds = currentZoomBounds();
                        var rightFastThreshold = bounds.xmax - (bounds.xmax - bounds.xmin) * BOUNDARY_FACTOR;
                        var rightThreshold = bounds.xmax - (bounds.xmax - bounds.xmin) * BOUNDARY_FACTOR * 2;
                        var leftFastThreshold = bounds.xmin + (bounds.xmax - bounds.xmin) * BOUNDARY_FACTOR;
                        var leftThreshold = bounds.xmin + (bounds.xmax - bounds.xmin) * BOUNDARY_FACTOR *2;
                        if (x < leftFastThreshold) {
                            return 0;
                        } else if (x < leftThreshold) {
                            return 1;
                        } else if (x > rightThreshold && x <= rightFastThreshold) {
                            return 2;
                        } else if (x > rightFastThreshold) {
                            return 3;
                        } else {
                            return 4;
                        }
                    }

                    /**
                     * Determine if the user is unzooming to get back to the top zoom level, and a tune
                     * event occurred while zoomed
                     * @param {Number} button the mouse button that was pressed (1: left, 2L center, 3:right)
                     * @returns {boolean} true if the plot is being returned to the top zoom level and a tune event
                     * occurred while zoomed
                     */
                    var lastUnzoomAfterTune = function(button) {
                        if (button === 3) { //right-click
                            var zoom = zoomLevel();
                            //stack will have two entries before last unzoom, the current zoomed level and the top level
                            var retVal = (zoom === 2);
                            if (retVal) {
                                retVal = tunedWhileZoomed;
                                tunedWhileZoomed = false;
                            }
                            return retVal;
                        }
                        return false;
                    }
                    /**
                     * Return the current zoom level
                     * @returns {Integer} 1 if the plot is unzoomed all the way, otherwise 1 + the number of zooms
                     * that have occurred
                     */
                    var zoomLevel = function() {
                        var zoomStack = activePlot._Mx.stk;
                        return zoomStack.length;
                    }

                    /**
                     * Determine whether a select or  zoom action is being performed with the current drag operation,
                     * in accordance with the current rubberbox_action plot option setting.
                     *
                     * @param {Number} button the mouse button that is being pressed. 1: left; 2: middle; 3: right
                     * @returns {boolean} true if a select action is being performed, false if a zoom action is being performed.
                     */
                    var dragSelect = function(button) {
                        switch (RUBBERBOX_ACTION) {
                            case 'select' :
                                //true for left-click drag
                                return button === 1 && scope.ctrlKeyPressed;
                            case 'zoom' :
                                //true for ctrl-left-click drag
                                return button === 1 && !scope.ctrlKeyPressed;
                            default:
                                return false;
                        }
                    };

                    /** Tune to freq value at center of rectangle. In applications where bandwidth is selectable
                     * it can be set from width of rectangle. Here bandwidth is not selectable because we're dealing with
                     * fixed-bandwidth FM broadcast signals.
                     */
                    var dragTune = function(event) {
                        if (lastMouseDown.x && lastMouseDown.y) {
                            var rect = {
                                x1: lastMouseDown.x,
                                x2: event.x,
                                y1: lastMouseDown.y,
                                y2: event.y
                            };
                            lastMouseDown = {x:undefined, y: undefined}; //reset initial drag-point
                            target_freq = (rect.x1 + rect.x2) / 2;
                            scope.tuneContext.handleTune();
                            console.log("Tuned to sub-band from " + rect.x1 / 1000  + " KHz to " + rect.x2 / 1000 + " KHz");
                        }
                    };

                    scope.$watch('form.frequency', function(freq) {
                        target_freq = parseFloat(freq) * 1e6;
                    });

                    if (scope.tuneContext) {
                        scope.tuneContext.handleTune = function () {
                            var bounds = currentZoomBounds();
                            if (target_freq - nb_bw >= bounds.xmin && target_freq + nb_bw <= bounds.xmax) {
                                if_cf = target_freq - rf_cf;
                            } else {
                                rf_cf = target_freq;
                                if_cf = 0;
                            }
                            scope.doTune({rf_cf: rf_cf, if_cf: if_cf});
                            showHighlight(rf_cf);
                            if (pan) {
                                accordion.set_center(mx.pixel_to_real(activePlot._Mx, accordion_pixel_loc.x, accordion_pixel_loc.y).x);
                            }
                            if (leftButton && rightButton) {
                                updateButtons();
                            }
                        };
                    }

                    /**
                     * Determine whether the specified x value is within the bounds of the plot accordion
                     * @param x the Real World Coordinate (RWC) X value
                     * @returns {boolean} true if x is within the bounds of the plot accordion
                     */
                    var inAccordionBounds = function(x) {
                        if (accordion) {
                            var min = accordion.get_center() - nb_bw / 2;
                            var max = accordion.get_center() + nb_bw / 2;
                            return x >= min && x <= max;
                        }
                        return false;
                    };

                    /**
                     * Plot min/max values go beyond the plot boundary, to include the area where labels, etc are displayed.
                     * Here we detect whether clicking on actual plot or surrounding area.
                     */
                    var inPlotBounds = function(x, y) {
                        var bounds = currentZoomBounds();
                        var xmin = bounds.xmin;
                        var xmax = bounds.xmax;
                        var ymin = bounds.ymin;
                        var ymax = bounds.ymax;
                        // Use >= and <= because when clicking on any x position > xmax, x will be set to xmax. Same for y values
                        if (x >= xmax || x <= xmin || y >= ymax || y <= ymin) {
                            return false;
                        }
                        return true;
                    };

                    var currentZoomBounds = function() {
                        //zoom stack remembers min/max values at each zoom level, with current zoom values at end of stack
                        return activePlot._Mx.stk[activePlot._Mx.stk.length - 1];
                    }

                    //mark initial drag point
                    var plotMDownListener = function(event) {
                        if (inAccordionBounds(event.x)) {
                            accordionDrag = true;
                            //Don't draw the warpbox while dragging the accordion
                            activePlot.change_settings({rubberbox_action: ""});
                            activePlot.addListener('mmove', accordionMoveListener);
                            ghostAccordion.set_center(event.x);
                            return;
                        }
                        lastMouseDown.x = event.x;
                        lastMouseDown.y = event.y;
                    };

                    //Compare with initial drag-point to get user-specified rectangle
                    var plotMupListener = function(event) {
                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            var lBounds = leftButton.bounds();
                            var rBounds = rightButton.bounds();
                            if (inRectangle(lBounds, event.xpos, event.ypos) || inRectangle(rBounds, event.xpos, event.ypos)) {
                                console.log("CLICKED on BUTTON");
                                return;
                            }
                            ghostAccordion.set_center(-nb_bw);
                            if (accordionDrag) {
                                stopPan();
                                target_freq = event.x;
                                scope.tuneContext.handleTune();
                                accordionDrag = false;
                                activePlot.removeListener('mmove', accordionMoveListener);
                                activePlot.change_settings({rubberbox_action: RUBBERBOX_ACTION});
                                return;
                            }
                        }

                        //event.which==> 1=left-click, 2=middle-click, 3=right-click
                        /*tune if left-click or if unzooming to top level after tuning while zoomed.*/
                        if (Math.abs(event.x - lastMouseDown.x) <= clickTolerance && (event.which === 1 || lastUnzoomAfterTune(event.which))) {
                            if (inPlotBounds(event.x, event.y) && !scope.ctrlKeyPressed) {
                                console.log("Tuned to " + event.x / 1000 + " KHz");
                                if (zoomLevel() > 2) {
                                    tunedWhileZoomed = true;
                                }
                                target_freq = event.x;
                                if (event.which === 3) {
                                    //re-tune to the value specified while zoomed, to re-scale the plot
                                    target_freq = rf_cf + if_cf;
                                    activePlot.refresh();
                                }
                                if (scope.tuneContext) {
                                    scope.tuneContext.handleTune();
                                }
                            }
                        } else if (Math.abs(event.x - lastMouseDown.x) >= clickTolerance && dragSelect(event.which)) {
                            //Drag tune disabled for this application because it doesn't make sense with fixed bandwidth signals
                            //dragTune(event);
                        }
                    };

                    var accordionMoveListener = function(event) {
                        accordion.set_center(event.x);
                        var boundaryProximity = plotBoundary(event.x);
                        accordion_pixel_loc = mx.real_to_pixel(activePlot._Mx, event.x, event.y);
                        switch (boundaryProximity) {
                            case 0:
                                pan_control = "left_fast";
                                doPan();
                                break;
                            case 1:
                                pan_control = "left";
                                doPan();
                                break;
                            case 2:
                                pan_control = "right";
                                doPan();
                                break;
                            case 3:
                                pan_control = "right_fast";
                                doPan();
                                break;
                            default:
                                pan_control = '';
                                stopPan();
                        }
                    };

                    var doPan = function() {
                        if (pan) {
                            return;
                        }
                        RedhawkNotificationService.enable(false);
                        pan = $interval(function() {
                                if (!pan) {
                                    return;
                                }
                                if (pan_control === 'left') {
                                    target_freq-= TUNE_STEP;
                                    rf_cf = target_freq;
                                } else if (pan_control === 'left_fast') {
                                    target_freq-= TUNE_STEP * 10;
                                    rf_cf = target_freq;
                                } else if (pan_control === 'right') {
                                    target_freq+= TUNE_STEP;
                                    rf_cf = target_freq;
                                } else if (pan_control === 'right_fast') {
                                    target_freq+= TUNE_STEP * 10;
                                    rf_cf = target_freq;
                                }
                                if_cf = 0;
                                scope.tuneContext.handleTune();
                            },
                            STEP_DELAY);

                    };

                    var stopPan = function() {
                        if (pan) {
                            $interval.cancel(pan);
                            pan = undefined;
                            RedhawkNotificationService.enable(true);
                            accordion_pixel_loc = undefined;
                            ghostAccordion.set_center(-nb_bw);
                        }
                    };

                    /**
                     * Show subband tuning by adding a feature to the plot which draws a different color trace
                     * for data in a specified x-value range
                     */
                    var showHighlight = function (cf) {
                        if (pan) {
                            return;
                        }
                        if (scope.url.indexOf('psd/narrowband') >= 0) {
                            cf = 0;//show baseband freq for narrowband plot, not RF
                        } else {
                            cf+= if_cf;
                        }
                        if (activePlot && cf !== undefined && activePlot.get_layer(activePlotLayer)) {
                            if (scope.url.indexOf('psd/wideband') >= 0 || scope.url.indexOf('psd/narrowband') >= 0) {
                                if ( scope.url.indexOf('psd/narrowband') >= 0) {
                                    activePlot.get_layer(activePlotLayer).remove_highlight('subBand');
                                    activePlot.get_layer(activePlotLayer).add_highlight(
                                        {
                                            xstart: cf - nb_bw / 2,
                                            xend: cf + nb_bw / 2,
                                            color: 'rgba(255,50,50,1)',
                                            id: 'subBand'
                                        }
                                    );
                                } else if (accordion) {
                                    accordion.set_center(cf);
                                    accordion.set_width(nb_bw);
                                }
                            }
                        }

                    };

                    /** When SRI has changed, plot settings will be updated with next push of data **/
                    var reloadSri;

                    /** Detect changes to xstart and draw new highlight */
                    var lastXStart = -1;

                    /** String value used as part of format string: S = scalar data, C = complex data  **/
                    var mode;

                    /**
                     * Detect changed values from SRI and apply to plot
                     */
                    var updatePlotSettings = function(data) {
                        var isDirty = false;
                        rf_cf = data.keywords.CHAN_RF;
                        var xstart = data.xstart;
                        if (Math.abs(lastXStart - xstart) > 0) {
                            lastXStart = xstart;
                            showHighlight(rf_cf);
                            isDirty = true;
                        }

                        angular.forEach(data, function(item, key){
                            if (angular.isDefined(scope.plotSettings[key]) && !angular.equals(scope.plotSettings[key], item)) {
                                if (!(key === 'ydelta' && item === 0)) {
                                    scope.plotSettings[key] = item;
                                    isDirty = true;
                                    console.log('Plot New SRI: ' + key + ' changed from ' +  scope.plotSettings[key] + ' to ' + item);
                                }
                            }

                            if (angular.isDefined(scope.rasterSettings[key]) && !angular.equals(scope.rasterSettings[key], item)) {
                                if (!(key === 'ydelta' && item === 0)) {
                                    scope.rasterSettings[key] = item;
                                    isDirty = true;
                                    console.log('Raster New SRI: ' + key + ' changed from ' +  scope.rasterSettings[key] + ' to ' + item);
                                }
                            }
                        });

                        if (!data.ydelta) {
                            if (scope.plotSettings.ydelta != scope.plotSettings.xdelta * scope.plotSettings.subsize) {
                                scope.plotSettings.ydelta = scope.plotSettings.xdelta * scope.plotSettings.subsize;
                                isDirty = true;
                            }
                            if (scope.rasterSettings.ydelta != scope.rasterSettings.xdelta * scope.rasterSettings.subsize) {
                                scope.rasterSettings.ydelta = scope.rasterSettings.xdelta * scope.rasterSettings.subsize;
                                isDirty = true;
                            }
                        }
                        scope.plotSettings['size'] = 1;
                        scope.rasterSettings['size'] = 1;

                        /**
                         * We create the plot the first time SRI is received
                         */
                        switch (data.mode) {
                            case 0:
                                mode = "S";
                                break;
                            case 1:
                                mode = "C";
                                break;
                            default:
                        }

                        if (mode) {

                            // format string = (C|S)(F|D|I) for scalar/complex data containing Float/Double/Short values
                            var format = '';
                            switch (scope.type) {
                                case "float":
                                    format = mode +"F";
                                    break;
                                case "double":
                                    format = mode +"D";
                                    break;
                                case "short":
                                    format = mode + "I";
                                    break;
                                default:
                            }

                            if (scope.plotSettings.format !== format) {
                                scope.plotSettings.format = format;
                                isDirty = true;
                            }

                            if (scope.rasterSettings.format !== format) {
                                scope.rasterSettings.format = format;
                                isDirty = true;
                            }

                            showHighlight(rf_cf);
                        }

                        if(isDirty) {
                            reloadSri = true;
                        }
                    };

                    //SRI = Signal Related Information: signal metadata, pushed from server initially and when values change
                    var on_sri = function(sri) {
                        updatePlotSettings(sri);
                    };

                    var dataConverter = plotDataConverter(scope.type);
                    var lastDataSize;

                    /* Server pushes data one frame at a time */
                    var on_data = function(data) {

                        /*bpa and ape not currently used. Useful if we need to identify frame boundaries in data.

                         Number of raw bytes = subsize (from SRI) * bytes per element (BPE).
                         BPE = number of bytes per atom (BPA) * atoms per element (APE)
                         BPA = bytes needed to represent a value, i.e 2 for float, 4 for double
                         APE = 1 for scalar data, 2 for complex

                         Complex data can be plotted in various complex output modes, i.e. magnitude
                         of complex number (sqrt(real** + imag**)), sum of real and imaginary components,
                         separate trace for real and imaginary values, etc.
                         */

                        var bpa;
                        switch (scope.type) {
                            case 'double':
                                bpa = 2;
                                break;
                            case 'float':
                                bpa = 4;
                                break;
                            case 'short':
                                bpa = 2;
                                break;
                            default:
                                return;
                        }

                        var ape;
                        switch (mode) {
                            case 'S':
                                ape = 1;
                                break;
                            case 'C':
                                ape = 2;
                                break;
                            default:
                                return;
                        }

                        //bytes per element. There will be bpe * subsize raw bytes per frame.
                        var bpe = bpa * ape;

                        //assume single frame per handler invocation
                        var array = dataConverter(data);
                        lastDataSize = array.length;
                        if (activePlot) {
                            reloadPlots(array);
                        }
                    };

                    var reloadPlots = function(data) {

                        if (scope.plotType === 'line' && activePlotLayer === undefined) {
                            overlayPlot(scope.plotSettings);
                            if (scope.tuneContext) {
                                setPlotBounds();
                                scope.tuneContext.handleTune();
                            }
                        } else if (scope.plotType === 'dots' && activePlotLayer === undefined) {
                            overlayPlot(scope.plotSettings, angular.extend(plotOptions, {line: 0, radius: 1, symbol: 1}));
                        } else if (scope.plotType === 'raster' && activePlotLayer === undefined) {
                            angular.extend(scope.rasterSettings, {'yunits': 1});
                            overlayRaster(scope.rasterSettings, rasterOptions);
                            if (scope.tuneContext) {
                                setPlotBounds();
                                scope.tuneContext.handleTune();
                            }
                        }

                        if (reloadSri) {
                            if (plot && activePlotLayer !== undefined) {
                                plot.reload(activePlotLayer, data, scope.plotSettings);
                                plot.refresh();
                            }
                            if (raster && activePlotLayer !== undefined) {
                                raster.push(activePlotLayer, data, angular.copy(angular.extend(scope.rasterSettings)));
                                raster.refresh();
                            }
                            reloadSri = false;
                        } else {
                            if (plot && activePlotLayer !== undefined) {
                                plot.reload(activePlotLayer, data);
                                plot.refresh();
                            }
                            if (raster && activePlotLayer !== undefined) {
                                raster.push(activePlotLayer, data);
                                raster.refresh();
                            }
                        }
                    };

                    if (on_data)
                        plotSocket.addBinaryListener(on_data);
                    if (on_sri)
                        plotSocket.addJSONListener(on_sri);

                    plotSocket.connect(scope.url, function(){
                        console.log("Connected to Plot at " + scope.url);
                    });

                    scope.$on("$destroy", function(){
                        plotSocket.close();
                    })

                }
            };
        }
    ])
;
