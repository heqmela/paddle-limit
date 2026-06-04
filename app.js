const map = L.map('map').setView([35.9, 14.4], 9);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let landData = null;
let bufferedData = null;
let limitLayer = null;
let landLayer = null;
let meMarker = null;

const sel = document.getElementById('country');
const dist = document.getElementById('dist');
const distVal = document.getElementById('distVal');
const statusEl = document.getElementById('status');

// Load island list into the dropdown
fetch('countries.json')
  .then(function (r) { return r.json(); })
  .then(function (list) {
    list.forEach(function (c) {
      const o = document.createElement('option');
      o.value = c.id;
      o.textContent = c.name;
      sel.appendChild(o);
    });
    if (list.length) { loadCountry(list[0].id); }
  });

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

sel.onchange = function (e) { loadCountry(e.target.value); };

dist.oninput = function (e) {
  distVal.textContent = e.target.value;
  drawLimit();
  checkInside();
};

// Live GPS + inside/outside check
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
      checkInside();
    },
    function (err) { alert('Location error: ' + err.message); },
    { enableHighAccuracy: true }
  );
};

// Determine which zone the GPS point is in: land / within limit / outside
function checkZone() {
  if (!meMarker || !bufferedData || !landData) { return; }

  const ll = meMarker.getLatLng();
  const pt = turf.point([ll.lng, ll.lat]);

  // helper: is the point inside a GeoJSON polygon/multipolygon?
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
