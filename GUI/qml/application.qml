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
	
	}


	Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:140


		Image {
         source: "strada.png"
    }

	}

		Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:260

		Image {
         source: "strada.png"
    }

	}

	Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:380



		Image {
         source: "strada.png"
    }

	}

		Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:500



		Image {
         source: "strada.png"
    }

	}

	
		Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:620



		Image {
         source: "strada.png"
    }

	}
	
		Rectangle{
		width:628
		height:70
		color:"white"
		x:20
		y:740



		Image {
         source: "strada.png"
    }

	}

	Rectangle
	{
		width:20
		height:20
		color:"red"
		x:20
		y:20
		id:prova

		Connections
		{
			target: QmlBridge
			onSendToQml: 
			{
				prova.x = position
				prova.y= street_id
			}
			//prova.y=street_id
			//prova.y=data.street_id
		}
	}
}

