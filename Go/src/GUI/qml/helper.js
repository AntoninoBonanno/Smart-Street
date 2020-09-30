
var streets = {};
var cars = {};

function upsertStreet(street_id, length) {
    if (!streets.hasOwnProperty(street_id)) {
        var component = Qt.createComponent("street.qml");
        streets[street_id] = component.createObject(rootItem, { "width": length, "y": (Object.keys(streets).length * 120) });

        var component2 = Qt.createComponent("text.qml");
        component2.createObject(streets[street_id], { "text": ("Strada " + street_id) });
        return;
    }
    streets[street_id].width = length;
}

function upsertCar(street_id, car_id, position) {
    if (!streets.hasOwnProperty(street_id)) return;

    if (!cars.hasOwnProperty(car_id)) {
        var component = Qt.createComponent("car.qml");
        cars[car_id] = {};
        cars[car_id].street = street_id;
        cars[car_id].component = component.createObject(streets[street_id], { "x": position });

        var component2 = Qt.createComponent("text.qml");
        component2.createObject(cars[car_id].component, { "text": car_id });
        return;
    }

    if (cars[car_id].street != street_id) {
        cars[car_id].component.destroy();
        delete cars[car_id];
    } else cars[car_id].component.x = position;
}