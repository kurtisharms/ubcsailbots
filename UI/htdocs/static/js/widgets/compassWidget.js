console.info('Loaded compassWidget.js')


$(function() {
    var canvas = $("#compassWidgetCanvas");
    var canvasWidth = canvas.width();
    var canvasHeight = canvas.height();    
    
    canvas.drawArc({
        fillStyle: "lightgray",
        shadowColor: "#000",
        shadowBlur: 10,
        x: canvasWidth/2, y: canvasHeight/2,
        radius: canvasWidth/2-12
    });
    
    drawBoat(canvas,0);
});

function drawBoat(canvas, boatAngle, sailAngle) {
    var boatWidth = 40;
    var boatLength= 175; 
    var bowRadius = boatWidth/2;
    var boatStrokeWidth = 3;
    var sailLength = boatLength*0.7;
    // Draw main boat body
    canvas.drawRect({
        strokeStyle: "black",
        strokeWidth: boatStrokeWidth,
        x: canvas.width()/2, y: canvas.height()/2,
        width: boatWidth,
        height: boatLength - bowRadius,
        cornerRadius: 2,
        rotate: boatAngle
    });
    // Draw boat bow
    canvas.drawArc({
      strokeStyle:"black",
      strokeWidth: boatStrokeWidth,
      x: canvas.width()/2, y: canvas.height()/2-(boatLength-bowRadius)/2,
      radius: bowRadius,
      start: -90, end: 90,
      closed: false
    });
    
    
    // Draw Sail
    canvas.drawLine({
      strokeStyle: "black",
      strokeWidth: boatStrokeWidth-1,
      x1: canvas.width()/2, y1: canvas.height()/2-30,
      x2: (canvas.width()/2)+sailLength-15, y2: (canvas.height())/2+40
    });
}

function drawSailRig(canvasWidth, canvasHeight, boomAngle) {
}
