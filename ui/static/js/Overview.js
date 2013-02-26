var mapWidget;
var compassWidget;
//create map widget
$(function () {
  mapWidget = new MapWidget();
  mapWidget.setMapCenter();
  
  compassWidget = new CompassWidget();
  compassWidget.init();
})

setInterval('getlog()',1000);

function getlog(){

	    $.ajax({
        url: "api?request=overviewData",
        type: 'GET',
        dataType: "json",
        success: function (overviewData) {
        console.log(overviewData);
	        $("#telemetry-speedOverGroundCell").text(overviewData.telemetry.SOG)
	        $("#telemetry-windDirectionCell").text(overviewData.telemetry.AWA)
	        $("#telemetry-latitudeCell").text(overviewData.telemetry.latitude)
	        $("#telemetry-longitudeCell").text(overviewData.telemetry.longitude)
	        
	        // Update map widget
	     	mapWidget.update_boat_location(overviewData.telemetry.longitude, overviewData.telemetry.latitude);
	     	
	     	// Update compass widget
	     	compassWidget.setSheet(overviewData.telemetry.SheetPercent)
	     	compassWidget.setBoatHeading(overviewData.telemetry.Heading)
	     	compassWidget.setWindDirection(overviewData.telemetry.AWA)
    }
  });

}


