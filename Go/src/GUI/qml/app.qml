import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import "helper.js" as Helper

//Finestra principale
ApplicationWindow {
    title: "SMART STREET"
	visible:true
	width: 1040
	height: 500

    Rectangle {
        anchors.fill: parent 
        id: rootItem	
        color: "#3d3d3d"
        
        width: 1040
        height: 1000

        Text {
            anchors.fill: parent
            text: "SMART STREET"
            font.pointSize: 24
            color: "white"
            horizontalAlignment: Text.AlignHCenter
        }

        //Gestione dei segnali ricevuti dal bridge
        Connections
        {
            target: QmlBridge
            onCreateStreet: {
                Helper.upsertStreet(street, length);
            }
            onUpsertCar: {
                Helper.upsertCar(street, car, position, message, remove);
            }
            onCreateSignal: {
                Helper.upsertSignal(street, name, position, action);
            }
        }

        GridLayout {
            id: textContainer
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.bottom;
         
            columns: 1
        }
    }
}