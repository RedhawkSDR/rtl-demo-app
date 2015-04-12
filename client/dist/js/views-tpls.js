angular.module('rtl-demo-app').run(['$templateCache', function($templateCache) {
  'use strict';

  $templateCache.put('views/overview.html',
    "<div class=container><div class=row><div class=col-md-5><div class=row><div class=col-md-12><div ng-show=ready class=rhweb-survey-controls><form class=form-inline role=form><div class=form-group><label class=sr-only for=frequency>Frequency</label><div class=\"input-group frequency-input\"><input class=form-control id=frequency placeholder=Frequency ng-model=\"form.frequency\"><div class=input-group-addon>MHz</div></div></div><div class=form-group><label class=sr-only for=processing>Processing</label><select ng-model=form.processing class=form-control id=processing ng-options=\"p for p in processors\"></select></div><button type=submit class=\"btn btn-success\" ng-click=tuneContext.handleTune() ng-show=running>Tune</button> <button class=\"btn btn-success\" ng-show=!running ng-click=task()>Start</button> <button class=\"btn btn-danger\" ng-show=running ng-click=halt()>Halt</button></form></div></div></div><div ng-if=running class=row><div class=col-md-8><div style=\"width: 100%\" class=rhweb-survey-controls><b><small>Audio Stream</small></b><streaming-audio url=audioUrl></streaming-audio></div></div></div></div><div ng-if=running class=col-md-7><div class=row><div class=col-md-12><div class=row><div class=input-group><div class=\"input-group-addon rhweb-rds-addon\">Call Sign</div><input class=form-control id=rdsCall ng-model=\"rds.Call_Sign\"></div></div><div class=row><div class=input-group><div class=\"input-group-addon rhweb-rds-addon\">Station Type</div><input class=form-control id=rdsText ng-model=\"rds.Station_Type\"></div></div><div class=row><div class=input-group><div class=\"input-group-addon rhweb-rds-addon\">Now Playing</div><input class=form-control id=rdsInfo ng-model=\"rds.Full_Text\"></div></div></div></div></div></div><div ng-show=\"ready && connected && !running\" ng-class=row><div class=col-sm-8><button class=\"btn btn-xs btn-info\" ng-click=toggleSimulator()>Toggle Simulator</button></div></div><div ng-show=false class=row><div class=\"col-sm-3 col-sm-offset-3\"><p class=\"text-center rhweb-display-labels\">Frequency</p><div class=\"well well-sm\"><p class=\"text-center text-info rhweb-display-values\"><strong ng-if=survey.frequency>{{survey.frequency}} MHz</strong></p></div></div><div class=col-sm-3><p class=\"text-center rhweb-display-labels\">Processing</p><div class=\"well well-sm\"><p class=\"text-center text-info rhweb-display-values\"><strong>{{survey.processing | uppercase}}</strong></p></div></div></div><div ng-if=running class=row><div class=col-sm-12><div class=rhweb-plotting-toolbar><div class=\"btn-group btn-group-xs\"><button class=\"btn btn-xs btn-default text-muted\" data-template=views/partials/plot-help-wideband.html data-trigger=hover data-animation=am-flip-x data-auto-close=1 bs-popover><i class=\"fa fa-question-circle\"></i></button></div><div class=\"btn-group btn-group-xs pull-right\"><button class=\"btn btn-default\" ng-class=\"{'btn-primary': widebandMode == 'line'}\" ng-click=\"setWidebandMode('line')\">Wideband (Line)</button> <button class=\"btn btn-default\" ng-class=\"{'btn-primary': widebandMode == 'raster'}\" ng-click=\"setWidebandMode('raster')\">Wideband (Raster)</button></div></div><div class=\"well well-sm text-center rhweb-plot-container\"><div ng-if=\"widebandMode == 'line'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" tune-context=tuneContext form=form width=auto height=300px type=float url=/rtl/output/psd/wideband cmode=D2 plot-type=line></rtl-plot></div><div ng-if=\"widebandMode == 'raster'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" tune-context=tuneContext form=form width=auto height=300px type=float url=/rtl/output/psd/wideband cmode=D2 plot-type=raster></rtl-plot></div></div></div></div><div ng-if=running class=row><div class=col-sm-12><div class=rhweb-plotting-toolbar><div class=\"btn-group btn-group-xs\"></div><div class=\"btn-group btn-group-xs pull-right\"><button class=\"btn btn-default\" ng-class=\"{'btn-primary': detailPlotMode == 'narrowband'}\" ng-click=\"setDetailPlotMode('narrowband')\">Narrowband</button> <button class=\"btn btn-default\" ng-class=\"{'btn-primary': detailPlotMode == 'demod_freq'}\" ng-click=\"setDetailPlotMode('demod_freq')\">Demodulated</button> <button class=\"btn btn-default\" ng-class=\"{'btn-primary': detailPlotMode == 'demod_constellation'}\" ng-click=\"setDetailPlotMode('demod_constellation')\">Constellation</button> <button class=\"btn btn-default\" ng-class=\"{'btn-primary': detailPlotMode == 'demod_bit_raster'}\" ng-click=\"setDetailPlotMode('demod_bit_raster')\">Bit Raster</button> <button class=\"btn btn-default\" ng-class=\"{'btn-primary': detailPlotMode == 'demod_time'}\" ng-click=\"setDetailPlotMode('demod_time')\">Audio</button></div></div><div class=\"well well-sm text-center rhweb-plot-container\"><div ng-if=\"detailPlotMode == 'narrowband'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" width=auto height=300px type=float url=/rtl/output/psd/narrowband cmode=D2 plot-type=line></rtl-plot></div><div ng-if=\"detailPlotMode == 'demod_freq'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" width=auto height=300px type=float url=/rtl/output/psd/fm cmode=D2 plot-type=line></rtl-plot></div><div ng-if=\"detailPlotMode == 'demod_constellation'\"><rtl-plot width=auto height=300px type=float url=/rtl/output/psk/float cmode=IR plot-type=dots autol=5></rtl-plot></div><div ng-if=\"detailPlotMode == 'demod_bit_raster'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" width=auto height=300px type=short url=/rtl/output/psk/short cmode=D2 plot-type=raster></rtl-plot></div><div ng-if=\"detailPlotMode == 'demod_time'\"><rtl-plot do-tune=\"doTune(rf_cf, if_cf)\" width=auto height=300px type=float cmode=RE use-gradient=false url=/rtl/output/audio plot-type=line></rtl-plot></div></div></div></div></div><div ng-hide=connected><div class=container><div class=row><div class=\"col-md-8 col-md-offset-2\"><div class=\"panel panel-danger\"><div class=panel-heading>Connection Error</div><div class=\"panel-body bg-danger text-center\"><h2><i class=\"fa fa-5x fa-meh-o\"></i></h2><h3>Unable to connect to the backend server.</h3><p>Try typing <code>sudo service redhawk-web start</code> in the command-line.</p></div></div></div></div></div></div><div ng-hide=\"ready || !connected\"><div class=container><div class=row><div class=\"col-md-8 col-md-offset-2\"><div class=\"panel panel-danger\"><div class=panel-heading>Device Error</div><div class=\"panel-body bg-danger text-center\"><h2><i class=\"fa fa-5x fa-meh-o\"></i></h2><h3>The {{device.type | uppercase}} is currently {{device.status}}.</h3><p>If the device is unplugged, please plug it in.</p></div></div></div></div><div class=row><div class=\"col-md-6 col-md-offset-3\"><div class=\"panel panel-info\" ng-show=!device.simulator><div class=\"panel-body bg-info text-center\"><p>Switch to a FM Simulator instead of using the {{device.type}} hardware device.</p><button class=\"btn btn-sm btn-info\" ng-click=toggleSimulator()>Switch to Simulator</button></div></div></div></div></div></div>"
  );


  $templateCache.put('views/partials/plot-help-wideband.html',
    "<div class=popover><div class=arrow></div><h3 class=popover-title>Controls</h3><div class=popover-content><div><div class=plotting-help-control>Left Click</div><div class=plotting-help-function>Tune to the frequency under the mouse</div><div class=plotting-help-control>Left-Click Drag</div><div class=plotting-help-function>Tune to the frequency at the center of the box</div><div class=plotting-help-control>Ctrl Left-Click Drag</div><div class=plotting-help-function>Zoom into the plot</div><div class=plotting-help-control>Right Click</div><div class=plotting-help-function>Undo the most recent zoom</div><div class=plotting-help-control>Middle Click</div><div class=plotting-help-function>Show the plotting menu</div><div class=plotting-help-control>F</div><div class=plotting-help-function>Show the plot in fullscreen</div></div></div></div>"
  );

}]);