import QtQuick 2.7
import QtQuick.Controls 2.1

ApplicationWindow{

	background: Rectangle{color: "#3d3d3d"}
	title: "Streets"
	visible:true
	width:1000
	height:900
	//flags:Qt.FramelessWindowHint

	Rectangle{

		width:628
		height:70
		color:"white"
		x:20
		y:20

	Image {
         source: "strada.png"
    }
	Rectangle
	{
		width:20
		height:20
		color:"red"
		x:0
		y:35
		id:prova

		Connections
		{
			target: QmlBridge
			onSendToQml: prova.x = data
		}
	}
	}


	Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:140

		Text{
			text:"Hello World"
		}

		Image {
         source: "strada.png"
    }

	}

		Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:270

		Text{
			text:"Hello World"
		}

		Image {
         source: "strada.png"
    }

	}
}

