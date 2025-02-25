let pickupMap, dropMap;
let pickupMarker, dropMarker;
let pickupLocation = null;
let dropLocation = null;

// Default coordinates (Chennai)
const DEFAULT_LAT = 13.0827;
const DEFAULT_LNG = 80.2707;
const DEFAULT_ZOOM = 13;

document.addEventListener('DOMContentLoaded', function() {
    initializeMaps();
    setupFormListener();
    
    // Set minimum departure time to current time
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('departure-time').min = now.toISOString().slice(0,16);
});

function initializeMaps() {
    try {
        // Initialize pickup map
        pickupMap = L.map('pickup-map').setView([DEFAULT_LAT, DEFAULT_LNG], DEFAULT_ZOOM);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(pickupMap);

        // Initialize drop map
        dropMap = L.map('drop-map').setView([DEFAULT_LAT, DEFAULT_LNG], DEFAULT_ZOOM);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(dropMap);

        // Create search provider
        const provider = new GeoSearch.OpenStreetMapProvider({
            params: {
                'accept-language': 'en',
                countrycodes: 'in',
                viewbox: '68.1,8.0,97.4,37.6',
                bounded: 1
            }
        });

        // Add search control to pickup map
        const pickupSearchControl = new GeoSearch.GeoSearchControl({
            provider: provider,
            style: 'bar',
            showMarker: false,
            searchLabel: 'Search pickup location...',
            notFoundMessage: 'Location not found',
            autoComplete: true,
            autoCompleteDelay: 250,
            animateZoom: true,
            retainZoomLevel: false,
            updateMap: true,
            position: 'topleft'
        });
        pickupMap.addControl(pickupSearchControl);

        // Add search control to drop map
        const dropSearchControl = new GeoSearch.GeoSearchControl({
            provider: provider,
            style: 'bar',
            showMarker: false,
            searchLabel: 'Search drop location...',
            notFoundMessage: 'Location not found',
            autoComplete: true,
            autoCompleteDelay: 250,
            animateZoom: true,
            retainZoomLevel: false,
            updateMap: true,
            position: 'topleft'
        });
        dropMap.addControl(dropSearchControl);

        // Handle search results
        pickupMap.on('geosearch/showlocation', function(e) {
            const { location } = e;
            const latlng = { lat: location.y, lng: location.x };
            updateLocation('pickup', latlng, location.label);
        });

        dropMap.on('geosearch/showlocation', function(e) {
            const { location } = e;
            const latlng = { lat: location.y, lng: location.x };
            updateLocation('drop', latlng, location.label);
        });

        // Try to get user's current location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                const latlng = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latlng.lat}&lon=${latlng.lng}&format=json`)
                    .then(response => response.json())
                    .then(data => {
                        updateLocation('pickup', latlng, data.display_name);
                        pickupMap.setView([latlng.lat, latlng.lng], 16);
                    });
            });
        }

    } catch (error) {
        console.error('Error initializing maps:', error);
    }
}

function updateLocation(type, latlng, address) {
    const map = type === 'pickup' ? pickupMap : dropMap;
    const marker = type === 'pickup' ? pickupMarker : dropMarker;
    
    if (marker) {
        map.removeLayer(marker);
    }

    const newMarker = L.marker([latlng.lat, latlng.lng], {
        draggable: true
    }).addTo(map);

    // Handle marker drag
    newMarker.on('dragend', function(e) {
        const newLatLng = e.target.getLatLng();
        fetch(`https://nominatim.openstreetmap.org/reverse?lat=${newLatLng.lat}&lon=${newLatLng.lng}&format=json`)
            .then(response => response.json())
            .then(data => {
                if (type === 'pickup') {
                    pickupLocation = {
                        coordinates: [newLatLng.lat, newLatLng.lng],
                        address: data.display_name
                    };
                    document.getElementById('pickup').value = data.display_name;
                } else {
                    dropLocation = {
                        coordinates: [newLatLng.lat, newLatLng.lng],
                        address: data.display_name
                    };
                    document.getElementById('drop').value = data.display_name;
                }
            });
    });
    
    if (type === 'pickup') {
        pickupMarker = newMarker;
        pickupLocation = {
            coordinates: [latlng.lat, latlng.lng],
            address: address
        };
    } else {
        dropMarker = newMarker;
        dropLocation = {
            coordinates: [latlng.lat, latlng.lng],
            address: address
        };
    }

    document.getElementById(type).value = address;
}

function reverseGeocode(latlng, type) {
    const geocoder = L.Control.Geocoder.nominatim();
    geocoder.reverse(latlng, pickupMap.options.crs.scale(18), results => {
        if (results && results.length > 0) {
            const result = results[0];
            document.getElementById(type).value = result.name;
            if (type === 'pickup') {
                pickupLocation.address = result.name;
            } else {
                dropLocation.address = result.name;
            }
        }
    });
}

function clearLocation(type) {
    const map = type === 'pickup' ? pickupMap : dropMap;
    const marker = type === 'pickup' ? pickupMarker : dropMarker;
    
    if (marker) {
        map.removeLayer(marker);
    }
    
    document.getElementById(type).value = '';
    if (type === 'pickup') {
        pickupMarker = null;
        pickupLocation = null;
    } else {
        dropMarker = null;
        dropLocation = null;
    }
}

function setupFormListener() {
    document.getElementById('ride-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!pickupLocation || !dropLocation) {
            alert('Please select both pickup and drop locations');
            return;
        }

        const formData = {
            name: document.getElementById('name').value,
            phone: document.getElementById('phone').value,
            pickupLocation: pickupLocation,
            dropLocation: dropLocation,
            departureTime: document.getElementById('departure-time').value,
            genderPreference: document.getElementById('gender-preference').value,
            additionalNotes: document.getElementById('additional-notes').value
        };

        try {
            const response = await fetch('/api/rides', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Ride request created successfully!');
                window.location.href = data.redirect_url;
            } else {
                alert(data.error || 'Failed to create ride request');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to create ride request');
        }
    });
} 