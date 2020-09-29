package main

import (
	"database/sql"
	"fmt"
	"os"
	"strconv"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/qml"
	"github.com/therecipe/qt/quick"
	"github.com/therecipe/qt/widgets"
)

type StreetDB struct {
	STREET_ID int `json:"id"`
	LENGTH    int `json:"lenght"`
}

type QmlBridge struct {
	core.QObject

	_ func(data int) `signal:"sendToQml"`
}

func main() {
	fmt.Println("Connessione a mysql")

	//apertura connessione
	db, err := sql.Open("mysql", "root:@tcp(127.0.0.1:3306)/street_smart")
	// check errori connessione
	if err != nil {
		fmt.Println("Non funziona ")
		panic(err.Error())
	}

	//chiusura db
	defer db.Close()

	result, err := db.Query("SELECT id, length FROM `streets`") //mi estraggo quante strade ci sono
	// check errori su query
	if err != nil {
		fmt.Println("Non funziona ")
		panic(err.Error())
	}

	Streets := ""
	i := 0
	for result.Next() {

		var streetDB StreetDB

		err = result.Scan(&streetDB.STREET_ID, &streetDB.LENGTH)
		if err != nil {
			panic(err.Error())
		}

		strID := strconv.Itoa(streetDB.STREET_ID)
		Streets = Streets + `				
			Rectangle{
				id: street` + strID + `

				width: ` + strconv.Itoa(streetDB.LENGTH) + `
				height:70

				color:"#3d3d3d"

				x:0
				y:` + strconv.Itoa(i*80) + `

				Text {
					text: "Strada ` + strID + `"
					font.pointSize: 10
					color: "white"
				}
			}
		`
		i = i + 1
	}

	widgets.NewQApplication(len(os.Args), os.Args)

	var view = quick.NewQQuickView(nil)
	view.SetResizeMode(quick.QQuickView__SizeRootObjectToView)

	var qmlBridge = NewQmlBridge(nil)
	view.RootContext().SetContextProperty("QmlBridge", qmlBridge)
	var mainComponent = qml.NewQQmlComponent2(view.Engine(), nil)
	mainComponent.ConnectStatusChanged(func(status qml.QQmlComponent__Status) {
		if status == qml.QQmlComponent__Ready {

			var item = quick.NewQQuickItemFromPointer(mainComponent.Create(view.RootContext()).Pointer()) //create item and "cast" it to QQuickItem
			item.SetParent(view)                                                                          //add invisible item to invisible parent (for auto-deletion ...)
			item.SetParentItem(view.ContentItem())                                                        //add visible item to visible parent

		} else {
			fmt.Println("failed with status:", status)
			for _, e := range mainComponent.Errors() {
				fmt.Println("error:", e.ToString())
			}
		}
	})

	var qmlString = `
		import QtQuick 2.0
		import QtQuick.Controls 2.0
		Rectangle {
			anchors.fill: parent //fill the view.ContentItem
			id: rootItem	
			color: "#D2FEA6"
			
			width:1000
			height:1000

			` + Streets + `

			Connections
			{
				target: QmlBridge
				onSendToQml: {
					var component = Qt.createQmlObject('
						import QtQuick 2.0; 
						Rectangle {
							color: "blue"; 							
							height: 20
							width: 20

							radius: width*0.5

							x: 20
							y: 20
						}', 

						street1, 
						"ciao"
					);
					component.x = data
				}
			}
		}
	`

	mainComponent.SetData(core.NewQByteArray2(qmlString, -1), core.NewQUrl())

	go func() {
		for t := range time.NewTicker(time.Second * 1).C {
			_ = t
			qmlBridge.SendToQml(100)
		}
	}()

	view.Show()
	widgets.QApplication_Exec()
}
