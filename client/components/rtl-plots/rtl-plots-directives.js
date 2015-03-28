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
angular.module('rtl-plots', ['SubscriptionSocketService'])
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
    //Line plot
    .directive('rtlPlot', ['SubscriptionSocket', 'plotDataConverter', 'plotNotSupportedError',
        function(SubscriptionSocket, plotDataConverter, plotNotSupportedError){
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
                    autol: '@'
                },
                template: '<div style="width: {{width}}; height: {{height}};" ></div>',
                link: function (scope, element, attrs) {
                    if(!SubscriptionSocket.isSupported() || !SubscriptionSocket.isBinarySupported()) {
                        plotNotSupportedError(element);
                        return;
                    }
                    var plotSocket = SubscriptionSocket.createNew();

                    var RUBBERBOX_ACTION = 'select';

                    var RUBBERBOX_MODE = 'horizontal';

                    if(!angular.isDefined(scope.useGradient))
                        scope.useGradient = true;

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
                        plotLayer,
                        rasterLayer,
                        plotAccordion, //sigplot plug-in, used here to display vertical line at tuned frequency
                        rasterAccordion;

                    //narrowband bandwidth
                    var bw = 100000;

                    //wideband bandwidth
                    var spectrumBw = 2e6;

                    var tunedFreq; //TODO see if this is still needed

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
                        rubberbox_action: RUBBERBOX_ACTION,
                        rubberbox_mode: RUBBERBOX_MODE,
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
                        plot = new sigplot.Plot(element[0].firstChild, options);
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


                    var overlayPlot = function(overrides, options) {
                        options = options || {};
                        var optionsCopy = angular.extend(options, {layerType: sigplot.Layer1D});
                        plotLayer = plot.overlay_array(null, overrides, options);

                        //sigplot plug-in used to draw vertical line at tuned freq
                        plotAccordion = new sigplot.AccordionPlugin({
                            draw_center_line: true,
                            shade_area: false,
                            draw_edge_lines: false,
                            direction: "vertical",
                            edge_line_style: {strokeStyle: "#FF0000"}
                        });

                        plot.add_plugin(plotAccordion, plotLayer + 1);//plug-ins are drawn in separate layers
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
                        raster = new sigplot.Plot(element[0].firstChild, options);
                        if (scope.url.indexOf('psd/wideband') >= 0) {
                            raster.addListener('mdown', plotMDownListener);
                            raster.addListener('mup', plotMupListener);
                        }

                    };

                    var overlayRaster = function(overrides, options) {
                        var overridesCopy = angular.copy(overrides);
                        rasterLayer = raster.overlay_pipe(angular.extend(overridesCopy, {type: 2000, pipe: true, pipesize: 1024 * 1024 * 5}), options);

                        rasterAccordion = new sigplot.AccordionPlugin({
                            draw_center_line: false,
                            shade_area: true,
                            draw_edge_lines: true,
                            direction: "vertical",
                            edge_line_style: {strokeStyle: "#FF0000"}
                        });

                        raster.add_plugin(rasterAccordion, rasterLayer + 1);
                    };

                    var lastMouseDown = {
                        x: undefined,
                        y: undefined
                    };

                    //mark initial drag point
                    var plotMDownListener = function(event) {
                        lastMouseDown.x = event.x;
                        lastMouseDown.y = event.y;
                    };

                    //Since freq is on MHz scale, we need some tolerance when comparing click-point to some value
                    var clickTolerance = 200; //TODO set value automatically as a multiple of xdelta, to work with any data scale

                    //Compare with initial drag-point to get user-specified rectangle
                    var plotMupListener = function(event) {
                        //event.which==> 1=left-click, 2=middle-click, 3=right-click
                        //left-click zooming is built into sigplot. Here we implement right-click drag-tuning
                        if (Math.abs(event.x - lastMouseDown.x) <= clickTolerance && event.which === 1) {
                            if (inPlotBounds(event.x, event.y) && !scope.ctrlKeyPressed) {
                                console.log("Tuned to " + event.x / 1000 + " KHz");
                                scope.doTune({cf: event.x});
                            }
                        } else if (Math.abs(event.x - lastMouseDown.x) >= clickTolerance && dragSelect(event.which)) {
                            dragTune(event);
                        }
                    };

                    /**
                     * Determine whether a select or  zoom action is being performed with the current drag operation,
                     * in accordance with the current rubberbox_action plot option setting.
                     *
                     * @param {Number} button the mouse button that is being pressed. 1: left; 2: middle; 3: right
                     * @returns {boolean} true if a select action is being performed, false if a zoom action is being performed.
                     */
                    var dragSelect = function(button) {
                        var activePlot = (scope.plotType === 'line'? plot: raster);
                        switch (RUBBERBOX_ACTION) {
                            case 'select' :
                                //true for left-click drag
                                return button === 1 && activePlot._Mx.warpbox.style !== activePlot._Mx.warpbox.alt_style;
                            case 'zoom' :
                                //true for ctrl-left-click drag
                                return button === 1 && activePlot._Mx.warpbox.style === activePlot._Mx.warpbox.alt_style;
                            default:
                                return false;
                        }
                    };

                    /* Tune to freq value at center of rectangle. In applications where bandwidth is selectable
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
                            scope.doTune({cf:(rect.x1 + rect.x2) / 2});
                            console.log("Tuned to sub-band from " + rect.x1 / 1000  + " KHz to " + rect.x2 / 1000 + " KHz");
                        }
                    };

                    /**
                     * Plot min/max values go beyond the plot boundary, to include the area where labels, etc are displayed.
                     * Here we detect whether clicking on actual plot or surrounding area.
                     */
                    var inPlotBounds = function(x, y) {
                        var activePlot = (scope.plotType === 'line'? plot: raster);
                        //zoom stack remembers min/max values at each zoom level, with current zoom values at end of stack
                        var zoomStack = activePlot._Mx.stk[activePlot._Mx.stk.length - 1];
                        var xmin = zoomStack.xmin;
                        var xmax = zoomStack.xmax;
                        var ymin = zoomStack.ymin;
                        var ymax = zoomStack.ymax;
                        // when clicking on any x position > xmax, x will be set to xmax. Same for y values
                        if (x >= xmax || x <= xmin || y >= ymax || y <= ymin) {
                            return false;
                        }
                        return true;
                    };

                    /**
                     * Show subband tuning by adding a feature to the plot which draws a different color trace
                     * for data in a specified x-value range
                     */
                    var showHighlight = function (cf) {
                        if (scope.url.indexOf('psd/narrowband') >= 0) {
                            cf = 0;//show baseband freq for narrowband plot, not RF
                            bw = 100e3//TODO get value from TuneFilterDecimate component
                        }
                        if (plot && cf !== undefined && plot.get_layer(plotLayer)) {
                            if (scope.url.indexOf('psd/wideband') >= 0 || scope.url.indexOf('psd/narrowband') >= 0) {
                                plot.get_layer(plotLayer).remove_highlight('subBand');
                                plot.get_layer(plotLayer).add_highlight(
                                    {
                                        xstart: cf - bw / 2,
                                        xend: cf + bw / 2,
                                        color: 'rgba(255,50,50,1)',
                                        id: 'subBand'
                                    }
                                );
                                plotAccordion.set_center(cf);
                                //width not visible since we're not drawing edge-lines, but still required
                                plotAccordion.set_width(bw);
                            }
                        }
                        if (rasterAccordion && cf !== undefined) {
                            rasterAccordion.set_center(cf);
                            rasterAccordion.set_width(bw);
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
                        var cf = data.keywords.CHAN_RF;
                        var xstart = data.xstart;
                        if (Math.abs(lastXStart - xstart) > 0) {
                            lastXStart = xstart;
                            showHighlight(cf);
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

                            showHighlight(cf);
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
                        if (plot || raster) {
                            reloadPlots(array);
                        }
                    };

                    var reloadPlots = function(data) {

                        if (scope.plotType === 'line' && plot && plotLayer === undefined) {
                            overlayPlot(scope.plotSettings);
                        } else if (scope.plotType === 'dots' && plotLayer === undefined) {
                            overlayPlot(scope.plotSettings, angular.extend(plotOptions, {line: 0, radius: 1, symbol: 1}));
                        } else if (scope.plotType === 'raster' && rasterLayer === undefined) {
                            angular.extend(scope.rasterSettings, {'yunits': 1});
                            overlayRaster(scope.rasterSettings, rasterOptions);
                        }

                        if (reloadSri) {
                            if (plot && plotLayer !== undefined) {
                                plot.reload(plotLayer, data, scope.plotSettings);
                                plot.refresh();
                            }
                            if (raster && rasterLayer !== undefined) {
                                raster.push(rasterLayer, data, scope.rasterSettings);
                                raster.refresh();
                            }
                            reloadSri = false;
                        } else {
                            if (plot && plotLayer !== undefined) {
                                plot.reload(plotLayer, data);
                                plot.refresh();
                            }
                            if (raster && rasterLayer !== undefined) {
                                raster.push(rasterLayer, data);
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
