package main

import (
	"database/sql"
	"encoding/json"
	"io/ioutil"
	"os"
	"strconv"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/gui"
	"github.com/therecipe/qt/quick"
)

//Creazione delle struttura dati per mappare il database
type StreetDB struct {
	streetID int `json:"id"`
	length   int `json:"lenght"`
}
type RouteDB struct {
	carID                 string  `json:"car_id"`
	routeList             string  `json:"route_list"`
	currentSpeed          int     `json:"current_speed"`
	currentIndex          int     `json:"current_index"`
	currentStreetPosition float64 `json:"current_street_position"`
	connected             int     `json:"connected"`
}

type SignalDB struct {
	streetID int     `json:"street_id"`
	name     string  `json:"name"`
	position float64 `json:"position"`
	action   string  `json:"action"`
}

//Creazione di una struttura per effettuare il passaggio tra GO e QML attraverso dei segnali
type QmlBridge struct {
	core.QObject

	_ func(street int, length int)                                            `signal:"createStreet"`
	_ func(street int, car string, position int, message string, remove bool) `signal:"upsertCar"`
	_ func(street int, name string, position int, action string)              `signal:"createSignal"`
}

func main() {
	// Creo una nuova applicazione QT
	core.QCoreApplication_SetAttribute(core.Qt__AA_EnableHighDpiScaling, true)
	gui.NewQGuiApplication(len(os.Args), os.Args)

	// Aggiungo una view vuota
	var view = quick.NewQQuickView(nil)
	view.SetResizeMode(quick.QQuickView__SizeRootObjectToView)

	// Creo un bridge tra Go e Qml per passare le informazioni
	var qmlBridge = NewQmlBridge(nil)
	view.RootContext().SetContextProperty("QmlBridge", qmlBridge) //Setto il bridge come appartenente alla view Context

	view.SetSource(core.NewQUrl3("qrc:/qml/app.qml", 0)) //carico il QML principale

	go func() {
		connection := "root:@tcp(127.0.0.1:3306)/street_smart"

		//Recupero la configurazione per la connessione co il db
		jsonFile, err := os.Open("../../../../../config.json")

		if err == nil {
			byteValue, _ := ioutil.ReadAll(jsonFile)

			var res map[string]interface{}
			json.Unmarshal(byteValue, &res)
			mysql := res["mysql"].(map[string]interface{})

			// Avvio la connessione con il DB
			if len(mysql) != 0 {
				connection = mysql["user"].(string) + ":" + mysql["password"].(string) + "@tcp(" + mysql["host"].(string) + ":" + mysql["port"].(string) + ")/" + mysql["database"].(string)
			}
		}
		defer jsonFile.Close()

		db, err := sql.Open("mysql", connection)
		if err != nil {
			panic(err.Error())
		}
		defer db.Close()

		//Recupero le strade dal DB
		result, err := db.Query("SELECT id, length FROM `streets` WHERE `available` = 1")
		if err != nil {
			panic(err.Error())
		}

		// Iteriamo sui risultati della query
		for result.Next() {
			var streetDB StreetDB

			err = result.Scan(&streetDB.streetID, &streetDB.length)
			if err != nil {
				panic(err.Error())
			}

			// Passiamo i dati al QML
			qmlBridge.CreateStreet(streetDB.streetID, streetDB.length)
		}

		//Recupero i segnali stradali dal DB
		result, err = db.Query("SELECT street_id, name, position, action FROM `signals`")
		if err != nil {
			panic(err.Error())
		}

		// Iteriamo sui risultati della query per estrarre i segnali stradali
		for result.Next() {
			var signal SignalDB

			err = result.Scan(&signal.streetID, &signal.name, &signal.position, &signal.action)
			if err != nil {
				panic(err.Error())
			}

			// Passiamo i dati al QML
			qmlBridge.CreateSignal(signal.streetID, signal.name, int(signal.position), signal.action)
		}

		//Ogni due secondi recuperiamo le informazioni sulle route
		for t := range time.NewTicker(time.Second * 2).C {
			_ = t //t non viene usata

			//Recupero le route dal DB
			result, err := db.Query("SELECT car_id, route_list, current_index, current_speed, current_street_position, connected FROM `routes` WHERE finished_at IS NULL OR DATE(finished_at) = CURDATE()")
			if err != nil {
				panic(err.Error())
			}

			for result.Next() {
				var routeDB RouteDB

				err = result.Scan(&routeDB.carID, &routeDB.routeList, &routeDB.currentIndex, &routeDB.currentSpeed, &routeDB.currentStreetPosition, &routeDB.connected)
				if err != nil {
					panic(err.Error())
				}

				if routeDB.currentIndex > -1 {
					//Faccio il parse della stringa per convertirla in array
					var routeListConverted []int
					json.Unmarshal([]byte(routeDB.routeList), &routeListConverted)
					idStreet := routeListConverted[routeDB.currentIndex]

					message := "L'auto " + routeDB.carID + " è nella strada " + strconv.Itoa(idStreet) + ", posizione " + strconv.Itoa(int(routeDB.currentStreetPosition)) + " m, velocità " + strconv.Itoa(routeDB.currentSpeed) + " km/h, deve percorrere altre " + strconv.Itoa(len(routeListConverted)-routeDB.currentIndex-1) + " strade."
					// Passiamo i dati al QML per l'aggiornamento della posizione delle macchine
					qmlBridge.UpsertCar(idStreet, routeDB.carID, int(routeDB.currentStreetPosition), message, routeDB.connected == 0)
				}
			}
		}

	}()

	//view.Show()
	gui.QGuiApplication_Exec() //Avvio della GUI
}
