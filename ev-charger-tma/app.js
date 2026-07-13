// EV Charger Map - Telegram Mini App
// Initialize Telegram Web App
const tg = window.Telegram.WebApp;

// Expand the WebApp to full viewport
tg.expand();

// Sample EV charger data (in a real app, this would come from an API)
const sampleChargers = [
    {
        id: 1,
        name: "Tesla Supercharger - Downtown",
        type: "tesla",
        address: "123 Main St, City Center",
        lat: 51.505,
        lng: -0.09,
        power: "250 kW",
        availability: "available",
        connectors: ["CCS", "Tesla"],
        price: "$0.25/kWh",
        distance: 0.5
    },
    {
        id: 2,
        name: "EVgo Fast Charging Hub",
        type: "fast",
        address: "456 Oak Ave, Industrial Park",
        lat: 51.51,
        lng: -0.1,
        power: "150 kW",
        availability: "busy",
        connectors: ["CCS", "CHAdeMO"],
        price: "$0.30/kWh",
        distance: 1.2
    },
    {
        id: 3,
        name: "City Plaza Standard Chargers",
        type: "standard",
        address: "789 Pine St, Shopping Center",
        lat: 51.50,
        lng: -0.08,
        power: "7 kW",
        availability: "available",
        connectors: ["Type 2"],
        price: "$0.18/kWh",
        distance: 0.8
    },
    {
        id: 4,
        name: "Highway Rest Stop",
        type: "fast",
        address: "I-95 Exit 45, Rest Area",
        lat: 51.52,
        lng: -0.07,
        power: "350 kW",
        availability: "available",
        connectors: ["CCS", "CHAdeMO", "Tesla"],
        price: "$0.28/kWh",
        distance: 2.5
    },
    {
        id: 5,
        name: "Hotel Grand EV Parking",
        type: "standard",
        address: "101 Luxury Blvd, Hotel Grand",
        lat: 51.495,
        lng: -0.095,
        power: "11 kW",
        availability: "available",
        connectors: ["Type 2", "Tesla"],
        price: "$0.20/kWh",
        distance: 0.3
    },
    {
        id: 6,
        name: "Mall of the City",
        type: "fast",
        address: "2020 Shopping Ave, Mega Mall",
        lat: 51.49,
        lng: -0.11,
        power: "100 kW",
        availability: "busy",
        connectors: ["CCS", "Type 2"],
        price: "$0.22/kWh",
        distance: 1.8
    }
];

// Initialize map
let map;
let userMarker;
let chargerMarkers = [];
let currentLocation = { lat: 51.505, lng: -0.09 };

function initMap() {
    // Default to London coordinates
    map = L.map('map').setView([currentLocation.lat, currentLocation.lng], 13);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Add user marker
    userMarker = L.marker([currentLocation.lat, currentLocation.lng], {
        icon: L.divIcon({
            className: 'user-marker',
            html: '📍',
            iconSize: [30, 30]
        }),
        zIndexOffset: 1000
    }).addTo(map);
    
    // Add sample chargers to map
    addChargersToMap(sampleChargers);
    
    // Update charger list
    updateChargerList(sampleChargers);
    
    // Fit map to show all markers
    fitMapToMarkers();
}

// Custom icons for different charger types
function getChargerIcon(type, availability) {
    let iconUrl;
    let iconSize = [32, 32];
    
    switch(type) {
        case 'tesla':
            iconUrl = 'https://cdn-icons-png.flaticon.com/512/5977/5977597.png';
            break;
        case 'fast':
            iconUrl = 'https://cdn-icons-png.flaticon.com/512/1046/1046857.png';
            break;
        case 'standard':
        default:
            iconUrl = 'https://cdn-icons-png.flaticon.com/512/2983/2983847.png';
            break;
    }
    
    return L.icon({
        iconUrl: iconUrl,
        iconSize: iconSize,
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });
}

function addChargersToMap(chargers) {
    // Clear existing markers
    chargerMarkers.forEach(marker => map.removeLayer(marker));
    chargerMarkers = [];
    
    chargers.forEach(charger => {
        const icon = getChargerIcon(charger.type, charger.availability);
        
        const marker = L.marker([charger.lat, charger.lng], { icon: icon })
            .addTo(map)
            .bindPopup(`
                <div class="popup-content">
                    <h4>${charger.name}</h4>
                    <p><strong>Type:</strong> ${charger.type.charAt(0).toUpperCase() + charger.type.slice(1)}</p>
                    <p><strong>Power:</strong> ${charger.power}</p>
                    <p><strong>Status:</strong> <span class="${charger.availability}">${charger.availability.charAt(0).toUpperCase() + charger.availability.slice(1)}</span></p>
                    <p><strong>Connectors:</strong> ${charger.connectors.join(', ')}</p>
                    <p><strong>Price:</strong> ${charger.price}</p>
                    <p><strong>Address:</strong> ${charger.address}</p>
                    <p><strong>Distance:</strong> ${charger.distance} miles</p>
                </div>
            `);
        
        chargerMarkers.push(marker);
    });
}

function updateChargerList(chargers) {
    const container = document.getElementById('charger-items');
    container.innerHTML = '';
    
    // Sort by distance
    const sortedChargers = [...chargers].sort((a, b) => a.distance - b.distance);
    
    sortedChargers.forEach(charger => {
        const item = document.createElement('div');
        item.className = 'charger-item';
        item.innerHTML = `
            <h4>${charger.name}</h4>
            <p><strong>Type:</strong> ${charger.type} | <strong>Power:</strong> ${charger.power}</p>
            <p><strong>Status:</strong> <span class="${charger.availability}">${charger.availability}</span> | <strong>Distance:</strong> <span class="distance">${charger.distance} miles</span></p>
            <p><strong>Price:</strong> ${charger.price} | <strong>Connectors:</strong> ${charger.connectors.join(', ')}</p>
        `;
        
        item.addEventListener('click', () => {
            map.setView([charger.lat, charger.lng], 16);
            // Find the corresponding marker and open popup
            chargerMarkers.forEach(marker => {
                if (marker.getLatLng().lat === charger.lat && marker.getLatLng().lng === charger.lng) {
                    marker.openPopup();
                }
            });
        });
        
        container.appendChild(item);
    });
}

function fitMapToMarkers() {
    const group = new L.featureGroup([userMarker, ...chargerMarkers]);
    map.fitBounds(group.getBounds(), { padding: [50, 50] });
}

// Search functionality
document.getElementById('search-btn').addEventListener('click', () => {
    const query = document.getElementById('search-input').value.trim();
    if (query) {
        // In a real app, this would call a geocoding API
        // For demo purposes, we'll just filter the existing chargers
        const filtered = sampleChargers.filter(charger => 
            charger.name.toLowerCase().includes(query.toLowerCase()) ||
            charger.address.toLowerCase().includes(query.toLowerCase())
        );
        
        if (filtered.length > 0) {
            addChargersToMap(filtered);
            updateChargerList(filtered);
            fitMapToMarkers();
        } else {
            tg.showAlert('No chargers found matching your search.');
        }
    }
});

// Enter key for search
document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('search-btn').click();
    }
});

// Filter functionality
document.getElementById('charger-type').addEventListener('change', applyFilters);
document.getElementById('availability').addEventListener('change', applyFilters);

function applyFilters() {
    const typeFilter = document.getElementById('charger-type').value;
    const availabilityFilter = document.getElementById('availability').value;
    
    let filtered = [...sampleChargers];
    
    if (typeFilter !== 'all') {
        filtered = filtered.filter(charger => charger.type === typeFilter);
    }
    
    if (availabilityFilter !== 'all') {
        filtered = filtered.filter(charger => charger.availability === availabilityFilter);
    }
    
    addChargersToMap(filtered);
    updateChargerList(filtered);
    fitMapToMarkers();
}

// Locate me functionality
document.getElementById('locate-me').addEventListener('click', () => {
    // In a real app, use the browser's geolocation API
    if (navigator.geolocation) {
        document.getElementById('locate-me').textContent = '🔄 Locating...';
        document.getElementById('locate-me').disabled = true;
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Update user marker
                userMarker.setLatLng([currentLocation.lat, currentLocation.lng]);
                
                // Recalculate distances (in a real app, this would be done server-side)
                const updatedChargers = sampleChargers.map(charger => {
                    // Simple distance calculation (not accurate, just for demo)
                    const distance = Math.sqrt(
                        Math.pow(charger.lat - currentLocation.lat, 2) +
                        Math.pow(charger.lng - currentLocation.lng, 2)
                    ) * 69; // Approximate miles
                    return { ...charger, distance: distance.toFixed(1) };
                });
                
                addChargersToMap(updatedChargers);
                updateChargerList(updatedChargers);
                
                map.setView([currentLocation.lat, currentLocation.lng], 14);
                
                document.getElementById('locate-me').textContent = '📍 Locate Me';
                document.getElementById('locate-me').disabled = false;
                
                tg.showAlert('Location updated! Showing chargers near you.');
            },
            (error) => {
                document.getElementById('locate-me').textContent = '📍 Locate Me';
                document.getElementById('locate-me').disabled = false;
                tg.showAlert('Unable to get your location: ' + error.message);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    } else {
        tg.showAlert('Geolocation is not supported by your browser.');
    }
});

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if Telegram WebApp is ready
    if (tg.initDataUnsafe) {
        // User data is available
        console.log('Telegram user:', tg.initDataUnsafe.user);
    }
    
    // Initialize the map
    initMap();
    
    // Send main button text to Telegram if needed
    tg.MainButton.setText('Share Location');
    tg.MainButton.onClick(() => {
        tg.sendData(JSON.stringify({
            action: 'share_location',
            location: currentLocation
        }));
    });
    
    // Show the main button
    tg.MainButton.show();
});

// Handle Telegram WebApp expansion
tg.onEvent('viewportChanged', () => {
    // Resize map when viewport changes
    if (map) {
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }
});
