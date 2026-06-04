const map = L.map('map').setView([35.9, 14.4], 9);
const map = L.map('map', { zoomControl: false }).setView([35.9, 14.4], 9);
L.control.zoom({ position: 'topright' }).addTo(map);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let landData = null;
let bufferedData = null;
let limitLayer = null;
let landLayer = null;
let meMarker = null;
let catalog = [];

const countrySel = document.getElementById('country');
const islandSel = document.getElementById('island');
const dist = document.getElementById('dist');
const distVal = document.getElementById('distVal');
const statusEl = document.getElementById('status');

// Load catalog, build the Country dropdown
fetch('countries.json')
  .then(function (r) { return r.json(); })
  .then(function (list) {
    catalog = list;

    // unique list of countries
    const countries = [];
    list.forEach(function (c) {
      if (countries.indexOf(c.country) === -1) { countries.push(c.country); }
    });
    countries.sort();

    countries.forEach(function (name) {
      const o = document.createElement('option');
      o.value = name;
      o.textContent = name;
      countrySel.appendChild(o);
    });

    populateIslands(countries[0]);   // fill islands for first country
  });

// Fill the Island dropdown for a given country, then load the first island
function populateIslands(country) {
  islandSel.innerHTML = '';
  catalog
    .filter(function (c) { return c.country === country; })
    .forEach(function (c) {
      const o = document.createElement('option');
      o.value = c.id;
      o.textContent = c.name;
      islandSel.appendChild(o);
    });
  if (islandSel.value) { loadCountry(islandSel.value); }
}

countrySel.onchange = function (e) { populateIslands(e.target.value); };
islandSel.onchange  = function (e) { loadCountry(e.target.value); };

// Load an island's geojson and draw it
function loadCountry(id) {
  fetch('data/' + id + '.geojson')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      landData = data;
      if (landLayer) { map.removeLayer(landLayer); }
      landLayer = L.geoJSON(landData, {
        color: '#7a6f50',
        weight: 1,
        fillColor: '#e8dcc0',
        fillOpacity: 0.5
      }).addTo(map);
      drawLimit();
      map.fitBounds(landLayer.getBounds());
    });
}

// Buffer the land outward and draw the red limit line
function drawLimit() {
  if (!landData) { return; }
  const km = (Number(dist.value)) / 1000;
  bufferedData = turf.buffer(landData, km, { units: 'kilometers' });
  if (limitLayer) { map.removeLayer(limitLayer); }
  limitLayer = L.geoJSON(bufferedData, {
    color: 'red',
    weight: 2,
    dashArray: '6',
    fill: false
  }).addTo(map);
}

dist.oninput = function (e) {
  distVal.textContent = e.target.value;
  drawLimit();
  checkZone();
};

// Live GPS tracking
document.getElementById('locBtn').onclick = function () {
  if (!navigator.geolocation) {
    alert('Geolocation not supported on this device.');
    return;
  }
  navigator.geolocation.watchPosition(
    function (p) {
      const lat = p.coords.latitude;
      const lon = p.coords.longitude;
      const ll = [lat, lon];
      if (!meMarker) {
        meMarker = L.circleMarker(ll, {
          radius: 7,
          color: '#0066ff',
          fillColor: '#0066ff',
          fillOpacity: 1
        }).addTo(map);
      } else {
        meMarker.setLatLng(ll);
      }
      map.setView(ll);
      checkZone();
    },
    function (err) { alert('Location error: ' + err.message); },
    { enableHighAccuracy: true }
  );
};

// Decide which zone the GPS point is in: land / within limit / outside
function checkZone() {
  if (!meMarker || !bufferedData || !landData) { return; }

  const ll = meMarker.getLatLng();
  const pt = turf.point([ll.lng, ll.lat]);

  function isInside(geo) {
    const feat = geo.features ? geo.features[0] : geo;
    return turf.booleanPointInPolygon(pt, feat);
  }

  if (isInside(landData)) {
    statusEl.textContent = 'On land';
    statusEl.className = 'land';
  } else if (isInside(bufferedData)) {
    statusEl.textContent = 'Within limit';
    statusEl.className = 'inside';
  } else {
    statusEl.textContent = 'OUTSIDE limit';
    statusEl.className = 'outside';
  }
}
