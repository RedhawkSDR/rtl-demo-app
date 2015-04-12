/**
 * @license
 * File: sigplot.playback.js
 *
 * Copyright (c) 2012-2014, Michael Ihde, All rights reserved.
 * Copyright (c) 2012-2014, Axios Inc., All rights reserved.
 *
 * This file is part of SigPlot.
 *
 * SigPlot is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser
 * General Public License as published by the Free Software Foundation; either version 3.0 of the License, or
 * (at your option) any later version. This library is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
 * PURPOSE. See the GNU Lesser General Public License for more details. You should have received a copy of the
 * GNU Lesser General Public License along with SigPlot.
 */

/* global mx */
/* global m */
(function(sigplot, mx, m, undefined) {

    /**
     * @constructor
     * @param options
     * @returns {sigplot.ButtonPlugin}
     */
    sigplot.ButtonPlugin = function(options) {
        this.options = (options === undefined) ? {} : options;

        if (this.options.display === undefined) {
            this.options.display = true;
        }

        this.options.size = this.options.size || 25;
        this.options.lineWidth = this.options.lineWidth || 2;
        this.options.direction = this.options.direction || 'left';
        this.highlight = false;
        this.enabled = true;
    };

    sigplot.ButtonPlugin.prototype = {
        disabledStyle:  'rgb(70,70,70)',

        init: function(plot) {
            this.plot = plot;

            // Register for mouse events
            var self = this;
            var Mx = this.plot._Mx;
            this.onmousemove = function(evt) {
                if (Mx.warpbox) {
                    return;
                } // Don't highlight if a warpbox is being drawn

                // Ignore if the mouse is outside of the control area
                if (self.ismouseover(evt.xpos, evt.ypos) && self.enabled) {
                    self.set_highlight(true);
                } else {
                    self.set_highlight(false);
                }
            };
            this.plot.addListener("mmove", this.onmousemove);

            this.onmousedown = function(evt) {
                if (Mx.warpbox) {
                    return;
                } // Don't handle if a warpbox is being drawn

                // Ignore if the mouse is outside of the control area
                if (self.ismouseover(evt.xpos, evt.ypos) && self.enabled) {
                    evt.preventDefault();
                }
            };
            // Prevents zooms and stuff from occuring
            this.plot.addListener("mdown", this.onmousedown);

            this.onmouseclick = function(evt) {
                if (Mx.warpbox) {
                    return;
                } // Don't handle if a warpbox is being drawn

                // Ignore if the mouse is outside of the control area
                if (self.ismouseover(evt.xpos, evt.ypos) && self.enabled) {
                    self.select();
                    evt.preventDefault();
                }
            };
            this.plot.addListener("mclick", this.onmouseclick);
        },

        set_highlight: function(ishighlight) {
            if (ishighlight !== this.highlight) {
                this.highlight = ishighlight;
                this.plot.redraw();
            }
        },

        select: function() {
            if (this.plot && this.enabled) {
                var Mx = this.plot._Mx;
                var evt = document.createEvent('Event');
                if (this.options.id) {
                    evt.id = this.options.id;
                }
                evt.initEvent('selectevt', true, true);
                mx.dispatchEvent(Mx, evt);
            }
        },

        addListener: function(what, callback) {
            var Mx = this.plot._Mx;
            mx.addEventListener(Mx, what, callback, false);
        },

        removeListener: function(what, callback, passThrough) {
            var Mx = this.plot._Mx;
            mx.removeEventListener(Mx, what, callback, false);
        },

        ismouseover: function(xpos, ypos) {
            var position = this.position();
            var distance_from_ctr = Math.pow(xpos - position.x, 2) + Math.pow(ypos - position.y, 2);
            var R = this.options.size / 2;

            return (distance_from_ctr < Math.pow(R, 2));
        },

        position: function() {
            if (this.options.position) {
                return this.options.position;
            } else if (this.plot) {
                var Mx = this.plot._Mx;
                var R = this.options.size / 2;
                return {
                    x: Mx.l + R + this.options.lineWidth + 1,
                    y: Mx.t + R + this.options.lineWidth + 1
                };
            } else {
                return {
                    x: null,
                    y: null
                };
            }
        },

        bounds: function() {
            var bounds = {};
            var size = this.options.size;
            bounds.x = this.position().x - size/2;
            bounds.y = this.position().y - size/2;
            bounds.width = bounds.height = size + 3;
            return bounds;
        },

        refresh: function(canvas) {
            if (!this.options.display) {
                return;
            }
            var Gx = this.plot._Gx;
            var Mx = this.plot._Mx;

            var ctx = canvas.getContext("2d");

            ctx.lineWidth = this.options.lineWidth;
            var R = this.options.size / 2;

            if (this.highlight) {
                ctx.lineWidth += 2;
                R += 1;
            }

            var position = this.position();


            ctx.beginPath();
            ctx.arc(position.x, position.y, R - ctx.lineWidth, 0, Math.PI * 2, true);
            ctx.closePath();

            if (this.enabled) {
                ctx.strokeStyle = this.options.strokeStyle || Mx.fg;
            } else {
                ctx.strokeStyle = this.disabledStyle;
            }
            ctx.stroke();

            if (this.options.fillStyle) {
                ctx.fillStyle = this.options.fillStyle;
                ctx.fill();
            }

            var p1, p2, p3;

            if (this.options.direction === 'right') {
                p1 = {
                    x: R * 0.8,
                    y: R * 0.56
                };
                p2 = {
                    x: R * 1.45,
                    y: R
                };
                p3 = {
                    x: R * 0.8,
                    y: R * 1.45
                };
            } else  if (this.options.direction === 'left') {
                /* The center of the triangle is not the center of the circle, so
                 to flip it, we set the x values to the same distance from the right
                 side of hte circle as they were from the left side */
                p1 = {
                    x: 2 * R - R * 0.8,
                    y: R * 0.56
                };
                p2 = {
                    x: 2 * R  - R * 1.45,
                    y: R
                };
                p3 = {
                    x: 2 * R - R * 0.8,
                    y: R * 1.45
                };
            }

            p1.x += (position.x - R);
            p2.x += (position.x - R);
            p3.x += (position.x - R);
            p1.y += (position.y - R);
            p2.y += (position.y - R);
            p3.y += (position.y - R);

            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.closePath();

            ctx.fillStyle = this.enabled ? (this.options.strokeStyle || Mx.fg) : this.disabledStyle ;
            ctx.fill();

            ctx.restore();
        },

        setEnabled: function(enable) {
            this.enabled = enable;
        },

        isEnabled: function() {
            return this.enabled;
        },

        dispose: function() {
            this.plot = undefined;
            this.boxes = undefined;
        }
    };

}(window.sigplot = window.sigplot || {}, mx, m));
