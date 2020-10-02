# GUI

The Graphic User Interface allows you to graphically view all the components of the project, was built using a Qt library binding for Go.

As for the backend, that is the part that retrieves the data from the Database, it was written in GoLang while the part relating to the graphics and its management was written with Qml and Javascript.


![alt text](https://github.com/AntoninoBonanno/Smart-Street/blob/master/Go/screenshot.PNG?raw=true)

## Dependencies

* [qt](https://github.com/therecipe/qt)
* [MySQL](https://github.com/go-sql-driver/mysql)


## Installation

0) Preparation of the environment

    After installing [goLang](https://golang.org/doc/install?download=go1.13.4.windows-amd64.msi), sets the GOPATH environment variable to point to the **Go** folder. Make sure you don't have too long a path.

    Windows 10 and Windows 8
    - In Search, search for and then select: System (Control Panel)
    - Click the Advanced system settings link.
    - Click Environment Variables. In the section User Variables find the GOPATH environment variable and select it. Click Edit. 
    - In the Edit System Variable window, specify the value of the PATH environment variable. Click OK. Close all remaining windows by clicking OK.


1) Install qt

   `> set GO111MODULE=off `

   `> go get -v github.com/therecipe/qt/cmd/... && for /f %v in ('go env GOPATH') do %v\bin\qtsetup test && %v\bin\qtsetup -test=false`

    Inside the Go folder the bin, pkg folders will be generated. Inside the src folder, the github.com, golang.org folders will be generated

2) Install MySQL 

    `> go get -u github.com/go-sql-driver/mysql`


# Building

If you want to make changes or the .exe file won't start (else skip this step)

`> cd Go\src`

`> qtdeploy test desktop GUI`

# Execution

Run this command:

`> Go\src\GUI\deploy\windows\GUI.exe`

or double click at "Go\src\GUI\deploy\windows\GUI.exe"

## Authors

[Bonanno Antonino](https://github.com/AntoninoBonanno), [Castagnolo Giulia](https://github.com/yuko95)

