/**
 * Created by rpcanno on 10/22/14.
 */
angular.module('redhawk-audio-directives', [])
  .directive('streamingAudio', [
    function(){
      return {
        restrict: 'E',
        scope: {
          url: "="
        },
        templateUrl: 'components/redhawk-audio/templates/stream.html',
        link: function (scope, element, attrs) {
          var sec2time = function (seconds) {
            var sec_num = Math.floor(seconds); // don't forget the second param
            var hours   = Math.floor(sec_num / 3600);
            var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
            var seconds = sec_num - (hours * 3600) - (minutes * 60);

            if (hours   < 10) {hours   = "0"+hours;}
            if (minutes < 10) {minutes = "0"+minutes;}
            if (seconds < 10) {seconds = "0"+seconds;}

            var time    = (hours > 0 ? hours+':' : '' ) + minutes+':'+seconds;
            return time;
          };

          scope.player = element.find('.player')[0];
          scope.stream = element.find('.stream')[0];

          scope.currentTime = sec2time(0);
          scope.beffered = sec2time(0);
          scope.volume = 100;

          scope.$watch("volume", function(volume){
            if(volume) {
              scope.player.volume = volume / 100;
            }
          });

          scope.msg = function(text) {
            console.log("AudioPlayer::"+scope.url+": "+text);
          };

          scope.player.ontimeupdate = function() {
            scope.currentTime = sec2time(scope.player.currentTime);
            if(scope.player.buffered)
              scope.buffered = sec2time(scope.player.buffered.end(0));
            else
              scope.buffered = sec2time(0)
          };

          scope.player.onstalled = function() {
            scope.msg("Stalled");
          };
          scope.stream.onerror = function(dat) {
            scope.msg("Error");
            console.log(dat);
          };

          scope.mute = function() {
            scope.player.muted = !scope.player.muted;
            scope.muted = scope.player.muted;
          };
          scope.togglePlay = function() {
            var player = scope.player;

            if(player.paused) {
              player.src = scope.url;
              player.play();
            }
            else {
              player.pause();
              scope.currentTime = 0;
              player.src = "";
            }
          };
        }
      };
    }
  ])
;