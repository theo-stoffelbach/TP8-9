const fs = require('fs');

const NUM_ORDERS = 20000;
const ORDERS_PER_FILE = 5000;
const MAX_CUSTOMER_ID = 9000;
const MAX_PRODUCT_ID = 100000;

function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

let orderCount = 0;
let fileCount = 1;

while (orderCount < NUM_ORDERS) {
    const orders = [];
    const loopLimit = Math.min(ORDERS_PER_FILE, NUM_ORDERS - orderCount);

    for (let i = 0; i < loopLimit; i++) {
        // Entre 1 et 15 produits
        const numProducts = getRandomInt(1, 15);
        const items = [];

        for (let j = 0; j < numProducts; j++) {
            items.push({
                product_id: getRandomInt(1, MAX_PRODUCT_ID),
                quantity: getRandomInt(1, 10)
            });
        }

        orders.push({
            customer_id: getRandomInt(1, MAX_CUSTOMER_ID),
            items: items
        });
    }

    const fileName = `mock_orders_data_${fileCount}.json`;
    // On écrit les données en format JSON (indenté avec 2 espaces pour lisibilité)
    fs.writeFileSync(fileName, JSON.stringify(orders, null, 2));
    console.log(`✅ Fichier ${fileName} généré avec ${orders.length} commandes.`);

    fileCount++;
    orderCount += loopLimit;
}

console.log("Terminé ! Vous avec vos 20 000 commandes !");
 