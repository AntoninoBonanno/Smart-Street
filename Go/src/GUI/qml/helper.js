
var streets = {};
var cars = {};

/**
 * Mostra una strada nell GUI se la strada esiste aggiorna la sua lunghezza
 * @param {int} street_id id della strada
 * @param {int} length  lunghezza della strada
 */
function upsertStreet(street_id, length) {
    if (!streets.hasOwnProperty(street_id)) {
        //Recupero il qml della strada e lo aggiungo alla GUI
        var component = Qt.createComponent("street.qml");
        var y = (Object.keys(streets).length * 120) + 50;
        streets[street_id] = component.createObject(rootItem, { "width": length, "y": y });

        //Aggiungo il nome della strada nella GUI della strada
        var component2 = Qt.createComponent("text.qml");
        component2.createObject(streets[street_id], { "text": ("Strada " + street_id) });
        return;
    }
    streets[street_id].width = length;
}

/**
 * Mostra o aggiorna una macchinna nella GUI
 * @param {int} street_id id della strada
 * @param {string} car_id id della macchina (targa)
 * @param {int} position posizione della macchina
 * @param {bool} remove se la macchina deve essere rimossa dalla grafica
 */
function upsertCar(street_id, car_id, position, remove) {
    if (!streets.hasOwnProperty(street_id)) return; //se non ho strade return 

    if (!cars.hasOwnProperty(car_id)) { //se non ho già la macchina nella GUI la creo 
        if (remove) return;

        //Recupero il qml della macchina e lo aggiungo alla GUI
        var component = Qt.createComponent("car.qml");
        cars[car_id] = {};
        cars[car_id].street = street_id; //memorizzo in quale strada è attualmente la macchina
        cars[car_id].component = component.createObject(streets[street_id], { "x": position - 60 });

        //Aggingo il testo alla macchina
        var component2 = Qt.createComponent("text.qml");
        component2.createObject(cars[car_id].component, { "text": car_id });
        return;
    }

    //se la strada è diversa o voglio rimuovere la macchina, elimino la macchina dalla GUI e dalla variabile
    if (cars[car_id].street != street_id || remove) {
        cars[car_id].component.destroy();
        delete cars[car_id];
    } else cars[car_id].component.x = position - 60; //aggiorno la posizione (- 60 perchè considero la lunghezza della macchina nella GUI)
}


/**
 * Mostra un segnale stradale nella GUI (se la strada esiste) e la relativa azione
 * @param {int} street_id id della strada
 * @param {string} name nome del segnale
 * @param {int} position posizione del segnale nella strada
 * @param {string} action azione del segnale 
 */
function upsertSignal(street_id, name, position, action) {
    //controllo se esiste l'id della strada 
    if (!streets.hasOwnProperty(street_id)) return;

    //Recupero il qml del segnale e lo aggiungo alla GUI
    if (name == 'stop') {
        var component = Qt.createComponent("stop.qml");
        component.createObject(streets[street_id], { "x": position - 34 });
        return;
    }

    if (name == 'speed_limit') {
        var component = Qt.createComponent("speed_limit.qml");
        var object = component.createObject(streets[street_id], { "x": position });

        var component2 = Qt.createComponent("text.qml");
        component2.createObject(object, { "text": ("Max " + action), "color": "white" });
        return;
    }

    var component = Qt.createComponent("semaphore.qml");
    component.createObject(streets[street_id], { "x": position });
}
