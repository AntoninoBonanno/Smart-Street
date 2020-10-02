import QtQuick 2.0; 

Rectangle{
    width: 1000
    height:122

    color:"#3d3d3d"

    x:20
    y:100

    Image {
        anchors.fill: parent
        source: "images/street.png"
        sourceSize.width: 1000
        sourceSize.height: 119
    }
}