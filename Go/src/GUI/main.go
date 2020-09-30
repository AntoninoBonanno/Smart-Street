package main

import (
	"database/sql"
	"encoding/json"
	"os"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/gui"
	"github.com/therecipe/qt/quick"
)

type StreetDB struct {
	streetID int `json:"id"`
	length   int `json:"lenght"`
}
type RouteDB struct {
	carID                 string  `json:"car_id"`
	routeList             string  `json:"route_list"`
	currentIndex          int     `json:"current_index"`
	currentStreetPosition float64 `json:"current_street_position"`
}

type QmlBridge struct {
	core.QObject

	_ func(street int, length int)               `signal:"createStreet"`
	_ func(street int, car string, position int) `signal:"upsertCar"`
}

func main() {
	core.QCoreApplication_SetAttribute(core.Qt__AA_EnableHighDpiScaling, true)
	gui.NewQGuiApplication(len(os.Args), os.Args)

	var view = quick.NewQQuickView(nil)
	view.SetResizeMode(quick.QQuickView__SizeRootObjectToView)

	var qmlBridge = NewQmlBridge(nil)
	view.RootContext().SetContextProperty("QmlBridge", qmlBridge)

	view.SetSource(core.NewQUrl3("qrc:/qml/app.qml", 0))

	go func() {
		db, err := sql.Open("mysql", "root:@tcp(127.0.0.1:3306)/street_smart")
		if err != nil {
			panic(err.Error())
		}
		defer db.Close()

		result, err := db.Query("SELECT id, length FROM `streets` WHERE `available` = 1") //recupero le strade
		if err != nil {
			panic(err.Error())
		}

		for result.Next() {
			var streetDB StreetDB

			err = result.Scan(&streetDB.streetID, &streetDB.length)
			if err != nil {
				panic(err.Error())
			}

			qmlBridge.CreateStreet(streetDB.streetID, streetDB.length)
		}

		for t := range time.NewTicker(time.Second * 5).C {
			_ = t
			result, err := db.Query("SELECT car_id, route_list, current_index, current_street_position FROM `routes` WHERE finished_at IS NULL")
			if err != nil {
				panic(err.Error())
			}

			for result.Next() {
				var routeDB RouteDB

				err = result.Scan(&routeDB.carID, &routeDB.routeList, &routeDB.currentIndex, &routeDB.currentStreetPosition)
				if err != nil {
					panic(err.Error())
				}

				var routeListConverted []int
				json.Unmarshal([]byte(routeDB.routeList), &routeListConverted)
				idStreet := routeListConverted[routeDB.currentIndex]

				qmlBridge.UpsertCar(idStreet, routeDB.carID, int(routeDB.currentStreetPosition))
			}
		}

	}()

	//view.Show()
	gui.QGuiApplication_Exec()
}
