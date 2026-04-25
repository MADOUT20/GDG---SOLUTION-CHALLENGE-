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

/* Badge colors for numbered markers */
const BADGE_COLORS = {
    critical: { bg: "#e53935", border: "#b71c1c" },
    high:     { bg: "#ff9800", border: "#e65100" },
    medium:   { bg: "#8bc34a", border: "#558b2f" },
    low:      { bg: "#66bb6a", border: "#2e7d32" },
};

let _leafletMap = null;
let _mapMarkerLayer = null;
let _heatLayer = null;

/* ---- public: first-time init ---- */
function initIndiaMap(containerId, regions) {
    if (_leafletMap) {
        _leafletMap.remove();
        _leafletMap = null;
        _mapMarkerLayer = null;
        _heatLayer = null;
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

    /* Standard road-map style tiles */
    L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: "abcd",
            maxZoom: 20,
        }
    ).addTo(_leafletMap);

    L.control.zoom({ position: "bottomleft" }).addTo(_leafletMap);

    /* reset-view button */
    var ResetControl = L.Control.extend({
        options: { position: "bottomleft" },
        onAdd: function () {
            var btn = L.DomUtil.create("div", "leaflet-bar leaflet-control map-reset-btn");
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
    _buildHeatLayer(regions);
    _placeMarkers(regions);
    _leafletMap.fitBounds([[15.6, 72.4], [22.2, 81.0]], { padding: [40, 40] });
}

/* ---- public: update markers with fresh data ---- */
function refreshMapMarkers(regions) {
    if (!_leafletMap || !_mapMarkerLayer) return;
    _buildHeatLayer(regions);
    _placeMarkers(regions);
    _leafletMap.invalidateSize();
}

/* ---- internal: build canvas heat overlay ---- */
function _buildHeatLayer(regions) {
    if (_heatLayer) {
        _leafletMap.removeLayer(_heatLayer);
        _heatLayer = null;
    }
    if (typeof L.heatLayer === "undefined") return;

    var heatPoints = [];

    regions.forEach(function (region) {
        var coords = INDIA_CITIES[region.name];
        if (!coords) return;

        var intensity = Math.min(1, (region.score || 0) / 100);

        /* Dense center cluster */
        heatPoints.push([coords.lat, coords.lng, intensity]);
        var innerCount = 6;
        for (var k = 0; k < innerCount; k++) {
            var ia = (Math.PI * 2 * k) / innerCount;
            heatPoints.push([
                coords.lat + Math.sin(ia) * 0.04,
                coords.lng + Math.cos(ia) * 0.04,
                intensity * 0.9,
            ]);
        }

        /* Primary spread ring */
        var spread = 0.18 + intensity * 0.30;
        var count  = 14 + Math.round(intensity * 20);
        for (var i = 0; i < count; i++) {
            var angle  = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
            var dist   = spread * (0.25 + Math.random() * 0.75);
            heatPoints.push([
                coords.lat + Math.sin(angle) * dist,
                coords.lng + Math.cos(angle) * dist,
                intensity * (0.3 + Math.random() * 0.5),
            ]);
        }

        /* Outer faint glow */
        var outerCount = 10 + Math.round(intensity * 12);
        for (var j = 0; j < outerCount; j++) {
            var a2 = (Math.PI * 2 * j) / outerCount + (Math.random() - 0.5) * 0.7;
            var d2 = spread * (1.0 + Math.random() * 0.8);
            heatPoints.push([
                coords.lat + Math.sin(a2) * d2,
                coords.lng + Math.cos(a2) * d2,
                intensity * (0.08 + Math.random() * 0.15),
            ]);
        }
    });

    _heatLayer = L.heatLayer(heatPoints, {
        radius: 50,
        blur: 35,
        maxZoom: 10,
        max: 1.0,
        minOpacity: 0.4,
        gradient: {
            0.0:  "#0000cc",
            0.15: "#6600ff",
            0.3:  "#9900ff",
            0.4:  "#0066ff",
            0.5:  "#00cccc",
            0.6:  "#00ff66",
            0.7:  "#ccff00",
            0.8:  "#ffcc00",
            0.9:  "#ff6600",
            1.0:  "#ff0000",
        },
    }).addTo(_leafletMap);
}

/* ---- internal: draw numbered badge markers ---- */
function _placeMarkers(regions) {
    _mapMarkerLayer.clearLayers();

    regions.forEach(function (region) {
        var coords = INDIA_CITIES[region.name];
        if (!coords) return;

        var colors = SEVERITY_COLORS[region.severity] || SEVERITY_COLORS.low;
        var badge  = BADGE_COLORS[region.severity] || BADGE_COLORS.low;

        /* Needs count shortened for badge */
        var label = _shortNum(region.needs);

        var icon = L.divIcon({
            className: "map-marker-wrapper",
            html:
                '<div class="map-badge-ring" style="border-color:' + badge.border + '"></div>' +
                '<div class="map-badge" style="background:' + badge.bg + ';border-color:' + badge.border + '">' +
                    '<span>' + label + '</span>' +
                '</div>',
            iconSize: [42, 42],
            iconAnchor: [21, 21],
        });

        var marker = L.marker([coords.lat, coords.lng], { icon: icon, zIndexOffset: 1000 });

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
            offset: [0, -24],
        });

        _mapMarkerLayer.addLayer(marker);
    });
}

/* ---- short number helper ---- */
function _shortNum(n) {
    n = Number(n) || 0;
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "k";
    return String(n);
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
