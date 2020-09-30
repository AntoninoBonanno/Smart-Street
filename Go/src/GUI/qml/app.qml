import QtQuick 2.0
import QtQuick.Controls 2.0

import "helper.js" as Helper

ApplicationWindow {
    title: "Streets"
	visible:true
	width:1000
	height:900

    Rectangle {
        anchors.fill: parent //fill the view.ContentItem
        id: rootItem	
        color: "#3d3d3d"
        
        width:1000
        height:1000

        Connections
        {
            target: QmlBridge
            onCreateStreet: {
                Helper.upsertStreet(street, length);
            }
            onUpsertCar: {
                Helper.upsertCar(street, car, position);
            }
        }
    }
}