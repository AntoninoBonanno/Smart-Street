package main

import ( 
	"fmt"
	
	"os"
	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/gui"
  //  "github.com/therecipe/qt/qml"
	"github.com/therecipe/qt/quick"
	"time"
	
	"encoding/json"
    "database/sql"
    _ "github.com/go-sql-driver/mysql"
    "log"
    "strconv"

	

)

type Route struct {
	CAR_ID   string    `json:"car_id"`
	ROUTE_LIST string `json:"route_list"`
	CURRENT_INDEX int `json:"current_index"`
	CURRENT_STREET_POSITION float64 `json:"current_street_position"`

}

type Street struct {
	STREET_ID   uint8    `json:"id"`
	LENGTH  int `json:"lenght"`

}

type Client struct {
	CAR_ID   string   
    POSITION  int 
    STREET_ID int

}

type QmlBridge struct {
	core.QObject

	_ func(position,street_id int)        `signal:"sendToQml"`
	_ func(data string) string `slot:"sendToGo"`
}

    
func main(){

	fmt.Println("Connessione a mysql")

    //apertura connessione
    db, err := sql.Open("mysql", "root:@tcp(127.0.0.1:3306)/street_smart")
    // check errori connessione 
    if err != nil {
		fmt.Println("Non funziona ")
		fmt.Println("Non funziona ")
		panic(err.Error())
		
    }

    //chiusura db
    defer db.Close()

    // query
     //mi estraggo quante strade ci sono 
    result,err:= db.Query("SELECT id,length FROM `streets`") //mi estraggo quante strade ci sono 
    // check errori su query
    if err != nil {
        fmt.Println("Non funziona ")
        panic(err.Error())
	}

    //route_array := make([]Route, 0)
    street_array:=make([]Street,0)
	
    for result.Next() {
        var my_st Street
        
        err=result.Scan(&my_st.STREET_ID,&my_st.LENGTH)
        street_array = append(street_array,my_st)
        // scansione risultati 
        fmt.Println(err)
        if err != nil {

            panic(err.Error()) 
		}
		
    
        log.Printf("Street id:  "+strconv.Itoa(my_st.LENGTH))
    }
    
	
    
    num_of_street:=len(street_array)

    log.Printf("Num of street :  "+ strconv.Itoa(num_of_street))
    //log.Printf("Num of route :  "+ strconv.Itoa(num_of_route))

    /*
	if t>0 {
	//generazione GUI
	gui.NewQGuiApplication(len(os.Args),os.Args)
	var app = qml.NewQQmlApplicationEngine(nil)
	view.RootContext().SetContextProperty("qmlBridge", qmlBridge)
	app.Load(core.NewQUrl3("qrc:///qml/app.qml",0))
	

	gui.QGuiApplication_Exec()
    }
    */
    
	//assumiamo per ora di utilizzare SOLO l'indice 0 
    if num_of_street >0{

    
   

	
    core.QCoreApplication_SetAttribute(core.Qt__AA_EnableHighDpiScaling, true)

	gui.NewQGuiApplication(len(os.Args), os.Args)

	var view = quick.NewQQuickView(nil)
	view.SetResizeMode(quick.QQuickView__SizeRootObjectToView)

	var qmlBridge = NewQmlBridge(nil)
	qmlBridge.ConnectSendToGo(func(data string) string {
		fmt.Println("go:", data)
		return "hello from go"
	})

	view.RootContext().SetContextProperty("QmlBridge", qmlBridge)
	view.SetSource(core.NewQUrl3("qrc:/qml/application.qml", 0))

	go func() {
		for t := range time.NewTicker(time.Second*5 ).C {
            _= t
            result, err := db.Query("SELECT car_id,route_list,current_index,current_street_position FROM `routes` WHERE finished_at IS NULL")
            if err != nil{
            
                panic(err.Error())
            }
            //log.Printf(strconv.Itoa(t))
            for result.Next() {
                var my_route Route
                
                err=result.Scan(&my_route.CAR_ID,&my_route.ROUTE_LIST,&my_route.CURRENT_INDEX,&my_route.CURRENT_STREET_POSITION)
                //route_array = append(route_array,my_route )

             
                fmt.Println(err)
                if err != nil {
                
                    panic(err.Error()) 
                }
                
                
            
                log.Printf("Targa Client :  "+my_route.CAR_ID)

                var c Client
                c.CAR_ID=my_route.CAR_ID
                var route_converted[]int
                var id_street int
                json.Unmarshal([]byte(my_route.ROUTE_LIST), &route_converted)
                id_street=route_converted[my_route.CURRENT_INDEX]
                c.POSITION=1
                st_len:=1
                for i := range street_array{
                if int(street_array[i].STREET_ID) == int(id_street){
                   st_len=street_array[i].LENGTH
                   c.POSITION=int(628*my_route.CURRENT_STREET_POSITION)/int(st_len)
                }
                }
                
                //per cambiare strada basta sommare 120
             
                switch id_street {
                case 1:
                    c.STREET_ID=20
                case 2:
                    c.STREET_ID=150
                case 3:
                    c.STREET_ID=270

                case 4:
                    c.STREET_ID=390
                case 5:
                    c.STREET_ID=510
                case 6:
                    c.STREET_ID=630
                case 7:
                    c.STREET_ID=750

                default:
                    c.STREET_ID=0
                }

             
                qmlBridge.SendToQml(c.POSITION,c.STREET_ID)
                
            }
            
            
           

          
		}
	}()

	view.Show()

    
    }
	gui.QGuiApplication_Exec()
	
}