// Adatok betöltése AJAX-szal
async function fetchComponents(category) {
    try {
        const response = await fetch(`/api/components?category=${category}`);
        if (!response.ok) {
            throw new Error('Nem sikerült a komponensek betöltése');
        }
        return await response.json();
    } catch (error) {
        console.error('Hiba:', error);
        alert('Nem sikerült a komponensek betöltése. Próbáld újra később!');
    }
}

// Modális ablak megnyitása
function openModal(category) {
    console.log("openModal hívás:", category);
    const modalBody = document.getElementById('component-results');
    const filterForm = document.getElementById('filter-form');
    modalBody.innerHTML = '';
    
    // Modal megnyitása
    const modal = new bootstrap.Modal(document.getElementById('componentModal'));
    modal.show();

    // Közös szűrő minden kategóriához
    let filters = `
        <label for="manufacturer">Gyártó:</label>
        <select id="manufacturer" class="form-control mb-2">
            <option value="">Mind</option>
        </select>`;

    // Kategória-specifikus szűrők
    switch(category) {
        case 'Alaplap':
            filters += `
                <label for="form_factor">Méret:</label>
                <select id="form_factor" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="ATX">ATX</option>
                    <option value="Micro-ATX">Micro-ATX</option>
                    <option value="Mini-ITX">Mini-ITX</option>
                </select>
                <label for="socket">Foglalat:</label>
                <select id="socket" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="AM4">AM4</option>
                    <option value="AM5">AM5</option>
                    <option value="LGA1700">LGA1700</option>
                </select>`;
            break;

        case 'Processzor':
            filters += `
                <label for="socket">Foglalat:</label>
                <select id="socket" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="AM4">AM4</option>
                    <option value="AM5">AM5</option>
                    <option value="LGA1700">LGA1700</option>
                </select>`;
            break;

        case 'Processzorhűtés':
            filters += `
                <label for="type">Típus:</label>
                <select id="type" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Léghűtés">Léghűtés</option>
                    <option value="Vízhűtés">Vízhűtés</option>
                </select>
                <label for="rgb">RGB:</label>
                <select id="rgb" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Igen">Igen</option>
                    <option value="Nem">Nem</option>
                </select>`;
            break;

        case 'Memória':
            filters += `
                <label for="memory_type">Foglalat:</label>
                <select id="memory_type" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="DDR4">DDR4</option>
                    <option value="DDR5">DDR5</option>
                </select>
                <label for="type">Kit típus:</label>
                <select id="type" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Single">Single</option>
                    <option value="Kit">Kit</option>
                </select>`;
            break;

        case 'Merevlemez':
        case 'SSD':
            filters += `
                <label for="type">Típus:</label>
                <select id="type" class="form-control mb-2">
                    <option value="">Mind</option>
                    ${category === 'SSD' ? 
                        `<option value="SATA">SATA</option>
                         <option value="NVMe">NVMe</option>` :
                        `<option value="HDD">HDD</option>`}
                </select>`;
            break;

        case 'Számítógépház':
            filters += `
                <label for="form_factor">Formátum:</label>
                <select id="form_factor" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Full-Tower">Full-Tower</option>
                    <option value="Mid-Tower">Mid-Tower</option>
                    <option value="Mini-Tower">Mini-Tower</option>
                </select>`;
            break;

        case 'Tápegység':
            filters += `
                <label for="efficiency">Fogyasztás:</label>
                <select id="efficiency" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Bronze">Bronze</option>
                    <option value="Gold">Gold</option>
                    <option value="Platinum">Platinum</option>
                </select>
                <label for="modular">Modularitás:</label>
                <select id="modular" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Nem moduláris">Nem moduláris</option>
                    <option value="Félig moduláris">Félig moduláris</option>
                    <option value="Teljesen moduláris">Teljesen moduláris</option>
                </select>`;
            break;

        case 'Számítógép hűtő ventilátor':
            filters += `
                <label for="fan_size">Méret:</label>
                <select id="fan_size" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="120mm">120mm</option>
                    <option value="140mm">140mm</option>
                </select>
                <label for="rgb">RGB:</label>
                <select id="rgb" class="form-control mb-2">
                    <option value="">Mind</option>
                    <option value="Igen">Igen</option>
                    <option value="Nem">Nem</option>
                </select>`;
            break;
    }

    filterForm.innerHTML = filters;

    // Szűrők beállítása és kezdeti komponensek betöltése
    filterComponents(category, true);

    // Eseménykezelők hozzáadása az összes select elemhez
    const selectElements = filterForm.querySelectorAll('select');
    selectElements.forEach(select => {
        select.addEventListener('change', () => filterComponents(category, false));
    });
}

function filterComponents(category, isInitialLoad = false) {
    const filters = {
        manufacturer: document.getElementById('manufacturer')?.value || '',
        socket: document.getElementById('socket')?.value || '',
        type: document.getElementById('type')?.value || '',
        rgb: document.getElementById('rgb')?.value || '',
        memory_type: document.getElementById('memory_type')?.value || '',
        form_factor: document.getElementById('form_factor')?.value || '',
        efficiency: document.getElementById('efficiency')?.value || '',
        modular: document.getElementById('modular')?.value || ''
    };

    // Esemény megakadályozása ha nem kezdeti betöltés
    if (!isInitialLoad) {
        event?.preventDefault();
    }

    const modalBody = document.getElementById('component-results');
    modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Betöltés...</span></div></div>';

    fetch(`/api/components?category=${category}&${new URLSearchParams(filters)}`)
        .then(response => response.json())
        .then(components => {
            modalBody.innerHTML = '';
            if (components.length === 0) {
                modalBody.innerHTML = '<div class="alert alert-info">Nincs találat a megadott szűrési feltételekkel.</div>';
            } else {
                renderComponents(components, modalBody, category);
            }
            
            // Gyártók listájának frissítése csak kezdeti betöltésnél
            if (isInitialLoad) {
                const manufacturerSelect = document.getElementById('manufacturer');
                const manufacturers = [...new Set(components.map(comp => comp.manufacturer))].sort();
                manufacturerSelect.innerHTML = '<option value="">Mind</option>';
                manufacturers.forEach(manufacturer => {
                    manufacturerSelect.innerHTML += `<option value="${manufacturer}">${manufacturer}</option>`;
                });
            }
        })
        .catch(error => {
            console.error('Hiba:', error);
            modalBody.innerHTML = '<div class="alert alert-danger">Hiba történt az adatok betöltése közben.</div>';
        });
}

// Komponensek renderelése
function renderComponents(components, container, category) {
    if (components.length > 0) {
        components.forEach(component => {
            const card = document.createElement('div');
            card.className = 'd-flex align-items-center mb-2';
            card.innerHTML = `
                <img src="${component.image_url}" class="img-thumbnail me-3" style="width: 80px; height: 80px;" alt="${component.name}">
                <div>
                    <h5 class="card-title mb-1">${component.name}</h5>
                    <button class="btn btn-primary btn-sm" onclick="addToConfig('${category}', ${component.id}, '${component.name}', ${component.price})">Hozzáadás</button>
                </div>`;
            container.appendChild(card);
        });
    } else {
        container.innerHTML = '<p class="text-muted">Nincsenek elérhető komponensek a megadott feltételekkel.</p>';
    }
}

// Komponens hozzáadása a konfigurációhoz
function addToConfig(category, id, name, price) {
    const configList = document.getElementById('config-list');
    if (!configList) {
        console.error('A config-list nem található!');
        return;
    }

    const listItem = document.createElement('li');
    listItem.className = 'list-group-item';
    listItem.textContent = `${category}: ${name}`;
    listItem.dataset.category = category;
    listItem.dataset.name = name;
    listItem.dataset.price = price;
    configList.appendChild(listItem);

    updateSummary(price);
}

// Összegzés frissítése
function updateSummary(price) {
    const totalElement = document.getElementById('total-price');
    const currentTotal = parseInt(totalElement.textContent, 10) || 0;
    totalElement.textContent = currentTotal + price;
}

// Egyéb kérés mező kezelése
function submitOrder() {
    // Összegyűjtjük a kiválasztott komponenseket
    const components = [];
    document.querySelectorAll('#config-list li').forEach(item => {
        components.push({
            category: item.dataset.category,
            name: item.dataset.name,
            price: item.dataset.price
        });
    });

    // Összegyűjtjük az egyéb kéréseket
    const requests = document.getElementById('special-requests').value;

    // Elküldjük a szervernek
    fetch('/send_summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            components: components,
            requests: requests
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            if (data.error.includes('profil adatait')) {
                window.location.href = '/profile';
            }
        } else {
            alert('Konfiguráció sikeresen elküldve!');
            // Opcionális: form resetelése
            document.getElementById('config-list').innerHTML = '';
            document.getElementById('special-requests').value = '';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Hiba történt a küldés során!');
    });
}