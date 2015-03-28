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
angular.module('SubscriptionSocketService', []) 
  .service('SubscriptionSocket', ['$rootScope', 'Modernizr', function ($rootScope, Modernizr) {
    var getWSBasePath = function() {
      var loc = window.location, new_uri;
      console.log("location: " + loc);
      console.log("host: " + loc.host);
      if (loc.protocol === "https:") {
        new_uri = "wss:";
      } else {
        new_uri = "ws:";
      }
      new_uri += "//" + loc.host;
      console.log("uri: " + new_uri);
      return new_uri;
    };

    var WebSocket = null;
    var doBinary = false;
    if("WebSocket" in window) {
      WebSocket = window.WebSocket;

      // Lifted from Modernizr
      doBinary = (function() {
        var protocol = 'https:'==location.protocol?'wss':'ws',
          protoBin;

        if('WebSocket' in window) {
          if( protoBin = 'binaryType' in WebSocket.prototype ) {
            return protoBin;
          }
          try {
            return !!(new WebSocket(protocol+'://.').binaryType);
          } catch (e){}
        }

        return false;
      })();
    }
    else if("MozWebSocket" in window) {
      WebSocket = window.MozWebSocket;
    }

    var Socket = function() {
      if(!Modernizr.websockets) {
        console.log("ERROR: SubscriptionSocket: Not supported by this browser.");
        return;
      }

      var self = this;
      this.callbacks = {
        message: [],
        json: [],
        binary: []
      };
      this._call = function (callbacks, data) {
        var scope = this.ws;
        angular.forEach(callbacks, function (callback) {
          //console.log("Service calling callback");
          $rootScope.$apply(function () {
            callback.call(scope, data);
          });
        });
      };
      this.connect = function (path, callback) {
        console.log("Socket connect: "+path);

        if(!path.match(/^ws(s?)\:/))
          path = getWSBasePath() + path;

        self.path = path;
        self.ws = null;
        if(WebSocket)
          self.ws = new WebSocket(path);

        self.ws.onopen = function (data) {
          console.log("Socket opened: "+self.path);
          self.ws.binaryType = "arraybuffer";
          callback.call(this.ws, data);
        };
        self.ws.onmessage = function (e) {
          //console.log("Service got message: ");
          //console.log(e.data);
          self._call(self.callbacks.message);

          if (e.data instanceof ArrayBuffer) {
            self._call(self.callbacks.binary, e.data)
          } else {
            var reg = /:\s?(Infinity|-Infinity|NaN)\s?\,/g;
            var myData = e.data.replace(reg, ": \"$1\", ");
            self._call(self.callbacks.json, JSON.parse(myData));
          }
        };
      };
      this.addListener = function (callback) {
        this.callbacks.message.push(callback);
      };
      this.addJSONListener = function (callback) {
        this.callbacks.json.push(callback);
      };
      this.addBinaryListener = function (callback) {
        if(!doBinary) {
          console.log("WARN:: Socket: Browser does not support binary sockets");
        }
        this.callbacks.binary.push(callback);
      };
      this.send = function (data) {
        var self = this;
        self.ws.send(data);
      };
      this.close = function() {
        console.log("Socket closed: "+self.path);
        self.ws.close();
      }
    };

    //var supportedBrowser = ("WebSocket" in window);

    return {
      createNew: function() { return new Socket(); },
      isSupported: function() { return Modernizr.websockets; },
      isBinarySupported: function() { return doBinary; }
    }
  }]);
