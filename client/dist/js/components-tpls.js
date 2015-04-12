angular.module('rtl-demo-app').run(['$templateCache', function($templateCache) {
  'use strict';

  $templateCache.put('components/redhawk-audio/templates/stream.html',
    "<style>.vert-child {\n" +
    "    display: inline-block;\n" +
    "    vertical-align: middle;\n" +
    "    float: none;\n" +
    "  }\n" +
    "  .audio-stream-timestamp {\n" +
    "    text-align: center;\n" +
    "    font-size: smaller;\n" +
    "  }\n" +
    "  .audio-stream > .well {\n" +
    "    background-color: #bebebe;\n" +
    "    border-color: #aaaaaa;\n" +
    "    color: #202020;\n" +
    "    margin: 0;\n" +
    "    padding: 7px;\n" +
    "  }</style><audio class=player autoplay=true><source class=stream src=\"{{url}}\"></audio><div class=audio-stream><div class=\"well well-sm\"><div class=\"container-fluid audio-stream\"><div class=row><div class=\"col-md-2 vert-child\"><button class=\"btn btn-xs glyphicon glyphicon-play\" ng-class=\"{'glyphicon-play': player.paused, 'glyphicon-stop': !player.paused}\" ng-click=togglePlay()></button></div><div class=\"col-md-4 vert-child\"><div class=audio-stream-timestamp ng-if=!player.paused>{{currentTime}}</div><div class=audio-stream-timestamp ng-if=player.paused>Stopped</div></div><div class=\"col-md-2 vert-child\"><button ng-click=mute() class=\"btn btn-xs glyphicon\" ng-class=\"{'glyphicon glyphicon-volume-up': !muted, 'glyphicon glyphicon-volume-off': muted}\"></button></div><div class=\"col-md-3 col-sm-6 vert-child\"><input type=range min=0 max=100 ng-model=volume></div></div></div></div></div>"
  );


  $templateCache.put('components/rtl-rest/templates/device-status.html',
    "<span ng-class=\"{'text-success': device.status == 'ready', 'text-danger': device.status != 'ready'}\"><strong><span class=glyphicon ng-class=\"{'glyphicon-ok-sign': device.status == 'ready', 'glyphicon-remove-sign': device.status != 'ready'}\"></span> {{device.type | uppercase}}</strong></span>"
  );

}]);
