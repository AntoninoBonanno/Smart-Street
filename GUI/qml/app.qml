import QtQuick 2.7
import QtQuick.Controls 2.1

ApplicationWindow{

	background: Rectangle{color: "#3d3d3d"}
	visible:true
	width:800
	height:600
	flags:Qt.FramelessWindowHint

	Rectangle{
		width:300
		height:200
		color:"white"
		x:20
		y:20

		Text{
			text:"Hello World"
		}

	}
}

