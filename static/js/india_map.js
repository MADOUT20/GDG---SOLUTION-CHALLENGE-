/* ---------------------------------------------------------------
   india_map.js  –  Interactive Leaflet map for the Heatmap tab
   --------------------------------------------------------------- */

const INDIA_CITIES = {
    Mumbai:     { lat: 19.0760, lng: 72.8777 },
    Thane:      { lat: 19.2183, lng: 72.9781 },
    Pune:       { lat: 18.5204, lng: 73.8567 },
    Nagpur:     { lat: 21.1458, lng: 79.0882 },
    Nashik:     { lat: 19.9975, lng: 73.7898 },
    Aurangabad: { lat: 19.8762, lng: 75.3433 },
};

const SEVERITY_COLORS = {
    critical: { main: "#d32f2f", glow: "rgba(211,47,47,0.35)", grad: "linear-gradient(135deg,#d32f2f,#ff6b6b)" },
    high:     { main: "#ff9800", glow: "rgba(255,152,0,0.35)",  grad: "linear-gradient(135deg,#ff9800,#ffb74d)" },
    medium:   { main: "#ffc107", glow: "rgba(255,193,7,0.35)",  grad: "linear-gradient(135deg,#ffc107,#ffe082)" },
    low:      { main: "#4caf50", glow: "rgba(76,175,80,0.35)",  grad: "linear-gradient(135deg,#4caf50,#81c784)" },
};

let _leafletMap = null;
let _mapMarkerLayer = null;

/* ---- public: first-time init ---- */
function initIndiaMap(containerId, regions) {
    if (_leafletMap) {
        _leafletMap.remove();
        _leafletMap = null;
        _mapMarkerLayer = null;
    }

    _leafletMap = L.map(containerId, {
        center: [20.0, 76.0],
        zoom: 6,
        minZoom: 4,
        maxZoom: 15,
        zoomControl: false,
        scrollWheelZoom: true,
        maxBounds: [[5, 65], [38, 98]],
        maxBoundsViscosity: 0.9,
    });

    L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: "abcd",
            maxZoom: 20,
        }
    ).addTo(_leafletMap);

    L.control.zoom({ position: "topright" }).addTo(_leafletMap);

    /* reset-view button */
    const ResetControl = L.Control.extend({
        options: { position: "topright" },
        onAdd: function () {
            const btn = L.DomUtil.create("div", "leaflet-bar leaflet-control map-reset-btn");
            btn.innerHTML = '<a href="#" title="Reset view" role="button" aria-label="Reset view">⟳</a>';
            L.DomEvent.disableClickPropagation(btn);
            btn.querySelector("a").addEventListener("click", function (e) {
                e.preventDefault();
                _leafletMap.fitBounds([[15.6, 72.4], [22.2, 81.0]], { padding: [40, 40] });
            });
            return btn;
        },
    });
    new ResetControl().addTo(_leafletMap);

    _mapMarkerLayer = L.layerGroup().addTo(_leafletMap);
    _placeMarkers(regions);
    _leafletMap.fitBounds([[15.6, 72.4], [22.2, 81.0]], { padding: [40, 40] });
}

/* ---- public: update markers with fresh data ---- */
function refreshMapMarkers(regions) {
    if (!_leafletMap || !_mapMarkerLayer) return;
    _placeMarkers(regions);
    _leafletMap.invalidateSize();
}

/* ---- internal: draw markers ---- */
function _placeMarkers(regions) {
    _mapMarkerLayer.clearLayers();

    regions.forEach(function (region) {
        var coords = INDIA_CITIES[region.name];
        if (!coords) return;

        var colors = SEVERITY_COLORS[region.severity] || SEVERITY_COLORS.low;

        var icon = L.divIcon({
            className: "map-marker-wrapper",
            html:
                '<div class="map-marker-pulse" style="background:' + colors.glow + '"></div>' +
                '<div class="map-marker-dot" style="background:' + colors.grad + ';box-shadow:0 0 10px ' + colors.glow + '"></div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20],
        });

        var marker = L.marker([coords.lat, coords.lng], { icon: icon });

        marker.bindPopup(_popupHTML(region, colors), {
            className: "map-custom-popup",
            maxWidth: 280,
            minWidth: 200,
            autoPan: true,
            autoPanPadding: L.point(30, 30),
            autoPanSpeed: 8,
            closeButton: true,
        });

        marker.bindTooltip(region.name, {
            className: "map-custom-tooltip",
            direction: "auto",
            permanent: false,
            opacity: 1,
            offset: [0, -22],
        });

        _mapMarkerLayer.addLayer(marker);
    });
}

/* ---- popup HTML ---- */
function _popupHTML(region, colors) {
    var needs = Number(region.needs || 0).toLocaleString("en-IN");
    var vols  = Number(region.volunteers || 0).toLocaleString("en-IN");
    return (
        '<div class="popup-inner">' +
            '<div class="popup-head">' +
                '<h4>' + _esc(region.name) + '</h4>' +
                '<span class="popup-badge" style="background:' + colors.grad + '">' + _esc(region.severity_label) + '</span>' +
            '</div>' +
            '<div class="popup-grid">' +
                '<div class="popup-cell"><span class="popup-cell-label">Needs</span><span class="popup-cell-val" style="color:' + colors.main + '">' + needs + '</span></div>' +
                '<div class="popup-cell"><span class="popup-cell-label">Volunteers</span><span class="popup-cell-val">' + vols + '</span></div>' +
                '<div class="popup-cell"><span class="popup-cell-label">Score</span><span class="popup-cell-val">' + region.score + '%</span></div>' +
            '</div>' +
            '<div class="popup-bar-track"><div class="popup-bar-fill" style="width:' + region.score + '%;background:' + colors.grad + '"></div></div>' +
            (region.focus ? '<div class="popup-focus">' + _esc(region.focus) + '</div>' : '') +
        '</div>'
    );
}

function _esc(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
