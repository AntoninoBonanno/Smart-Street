package main

import ( 
	"os"
	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/gui"
	"github.com/therecipe/qt/qml"

)
import "fmt"
func main(){
	gui.NewQGuiApplication(len(os.Args),os.Args)
	var app = qml.NewQQmlApplicationEngine(nil)
	app.Load(core.NewQUrl3("qrc:///qml/app.qml",0))
	
	fmt.Println("ciao")
	gui.QGuiApplication_Exec()
	
	fmt.Println("ri-ciao")
}