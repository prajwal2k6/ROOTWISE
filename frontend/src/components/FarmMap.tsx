
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import { setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

export type FarmMapData = {
  latitude: number;
  longitude: number;
  boundary: [number, number][];
  areaAcres: number;
  areaHectares: number;
};

type FarmMapProps = {
  onSave?: (data: FarmMapData) => void;
};

export default function FarmMap({ onSave }: FarmMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const drawingRef = useRef(false);
  const boundaryRef = useRef<[number, number][]>([]);
  const farmLocationRef = useRef<[number, number] | null>(null);

  const [search, setSearch] = useState("");
  const [drawing, setDrawing] = useState(false);
  const [boundary, setBoundary] = useState<[number, number][]>([]);
  const [farmLocation, setFarmLocation] =
    useState<[number, number] | null>(null);
  const [area, setArea] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // Calculate farm area in acres.
  const calculateArea = useCallback(
    (points: [number, number][]) => {
      if (points.length < 3) return 0;

      const radius = 6378137;
      let total = 0;

      for (let i = 0; i < points.length; i++) {
        const current = points[i];
        const next = points[(i + 1) % points.length];

        total +=
          (next[0] - current[0]) *
          (Math.PI / 180) *
          (2 +
            Math.sin((current[1] * Math.PI) / 180) +
            Math.sin((next[1] * Math.PI) / 180));
      }

      const squareMeters = Math.abs((total * radius * radius) / 2);

      return squareMeters / 4046.8564224;
    },
    []
  );

  // Update the polygon displayed on the map.
  const updateBoundary = useCallback(
    (points: [number, number][]) => {
      boundaryRef.current = points;
      setBoundary(points);
      setArea(calculateArea(points));

      const map = mapRef.current;

      if (!map || !map.isStyleLoaded()) return;

      const source = map.getSource(
        "farm-boundary"
      ) as maplibregl.GeoJSONSource | undefined;

      if (!source) return;

      const coordinates =
        points.length >= 3 ? [...points, points[0]] : [];

      source.setData({
        type: "FeatureCollection",
        features:
          points.length >= 3
            ? [
                {
                  type: "Feature",
                  properties: {},
                  geometry: {
                    type: "Polygon",
                    coordinates: [coordinates],
                  },
                },
              ]
            : [],
      });
    },
    [calculateArea]
  );

  // Initialize MapLibre only once.
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          satellite: {
            type: "raster",
            tiles: [
              "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            attribution:
              "Imagery © Esri, Maxar, Earthstar Geographics",
          },
        },
        layers: [
          {
            id: "satellite-layer",
            type: "raster",
            source: "satellite",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [78.9629, 20.5937],
      zoom: 4,
      doubleClickZoom: false,
    });

    mapRef.current = map;

    map.addControl(
      new maplibregl.NavigationControl(),
      "top-right"
    );

    map.addControl(
      new maplibregl.ScaleControl(),
      "bottom-left"
    );

    map.on("load", () => {
      map.addSource("farm-boundary", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [],
        },
      });

      map.addLayer({
        id: "farm-fill",
        type: "fill",
        source: "farm-boundary",
        paint: {
          "fill-color": "#9bd477",
          "fill-opacity": 0.3,
        },
      });

      map.addLayer({
        id: "farm-outline",
        type: "line",
        source: "farm-boundary",
        paint: {
          "line-color": "#c7ed9a",
          "line-width": 3,
        },
      });

      // Restore any existing boundary.
      const existing = boundaryRef.current;

      if (existing.length >= 3) {
        const source = map.getSource(
          "farm-boundary"
        ) as maplibregl.GeoJSONSource;

        source.setData({
          type: "Feature",
          properties: {},
          geometry: {
            type: "Polygon",
            coordinates: [[...existing, existing[0]]],
          },
        });
      }

      // Handle map clicks.
      map.on("click", (event: maplibregl.MapMouseEvent) => {
        const point: [number, number] = [
          event.lngLat.lng,
          event.lngLat.lat,
        ];

        if (drawingRef.current) {
          updateBoundary([...boundaryRef.current, point]);
          return;
        }

        farmLocationRef.current = point;
        setFarmLocation(point);

        if (markerRef.current) {
          markerRef.current.setLngLat(point);
        } else {
          markerRef.current = new maplibregl.Marker({
            color: "#c0df91",
          })
            .setLngLat(point)
            .addTo(map);
        }

        setMessage("Farm location selected.");
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, [updateBoundary]);

  // Search for a village, town or district.
  async function searchLocation() {
    if (!search.trim()) {
      setMessage("Enter a village, town or district.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(search)}`
      );

      if (!response.ok) {
        throw new Error("Location search failed.");
      }

      const results = await response.json();

      if (!results.length) {
        setMessage("Location not found. Try another search.");
        return;
      }

      const longitude = Number(results[0].lon);
      const latitude = Number(results[0].lat);

      const point: [number, number] = [longitude, latitude];
      const map = mapRef.current;

      if (!map) return;

      map.flyTo({
        center: point,
        zoom: 16,
        essential: true,
      });

      farmLocationRef.current = point;
      setFarmLocation(point);

      if (markerRef.current) {
        markerRef.current.setLngLat(point);
      } else {
        markerRef.current = new maplibregl.Marker({
          color: "#c0df91",
        })
          .setLngLat(point)
          .addTo(map);
      }

      setMessage(
        "Location found. Click the map to refine the farm position."
      );
    } catch {
      setMessage("Unable to search right now. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Start boundary drawing.
  function startDrawing() {
    drawingRef.current = true;
    setDrawing(true);
    updateBoundary([]);
    setMessage("Click around your farm to mark its boundary.");
  }

  // Complete boundary drawing.
  function finishDrawing() {
    if (boundaryRef.current.length < 3) {
      setMessage("Mark at least three boundary points.");
      return;
    }

    drawingRef.current = false;
    setDrawing(false);
    setMessage("Farm boundary completed successfully.");
  }

  // Remove the last boundary point.
  function undoPoint() {
    updateBoundary(boundaryRef.current.slice(0, -1));
  }

  // Clear the boundary.
  function clearBoundary() {
    drawingRef.current = false;
    setDrawing(false);
    updateBoundary([]);
    setMessage("Farm boundary cleared.");
  }

  // Confirm the selected location and boundary, then pass them to the
  // parent form. The complete farm is saved only after the profile is filled.
  function confirmFarmLocation() {
    const location = farmLocationRef.current;
    const points = boundaryRef.current;

    if (!location) {
      setMessage("Please select your farm location first.");
      return;
    }

    if (points.length < 3) {
      setMessage("Please draw your farm boundary first.");
      return;
    }

    const acres = calculateArea(points);

    if (acres <= 0) {
      setMessage("The farm boundary area could not be calculated. Please redraw it.");
      return;
    }

    const selectedData: FarmMapData = {
      latitude: location[1],
      longitude: location[0],
      boundary: points,
      areaAcres: acres,
      areaHectares: acres * 0.4046856422,
    };

    onSave?.(selectedData);
    setMessage("Location and boundary confirmed. Continue to your farm profile.");
  }

  return (
    <div className="farm-map-container">
      <div className="farm-map-header">
        <div>
          <span className="farm-map-eyebrow">
            ROOTWISE · FARM MAPPING
          </span>

          <h2>Locate your farm.</h2>

          <p>
            Find your land, mark its location and outline its boundary.
          </p>
        </div>
      </div>

      <div className="farm-map-search">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") searchLocation();
          }}
          placeholder="Search village, town or district..."
        />

        <button onClick={searchLocation} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      <div className="farm-map-wrapper">
        <div
          ref={mapContainer}
          className="farm-map-canvas"
        />

        <div className="farm-map-tools">
          <button onClick={startDrawing}>
            Draw farm boundary
          </button>

          <button
            onClick={undoPoint}
            disabled={!boundary.length}
          >
            Undo point
          </button>

          <button
            onClick={finishDrawing}
            disabled={!drawing}
          >
            Finish boundary
          </button>

          <button onClick={clearBoundary}>
            Clear
          </button>
        </div>
      </div>

      <div className="farm-map-information">
        <div>
          <span>BOUNDARY AREA</span>
          <strong>{area.toFixed(3)} acres</strong>
          <small>
            {(area * 0.4046856422).toFixed(3)} hectares
          </small>
        </div>

        <div>
          <span>BOUNDARY POINTS</span>
          <strong>{boundary.length}</strong>
        </div>

        <div>
          <span>LOCATION</span>
          <strong>
            {farmLocation
              ? `${farmLocation[1].toFixed(5)}, ${farmLocation[0].toFixed(5)}`
              : "Not selected"}
          </strong>
        </div>
      </div>

      {message && (
        <p className="farm-map-message">{message}</p>
      )}

      <button
        className="farm-map-save"
        onClick={confirmFarmLocation}
      >
        Use this farm location →
      </button>

      <style jsx>{`
        .farm-map-container {
          background: #f5f5eb;
          color: #183629;
          padding: 22px;
          border-radius: 20px;
          width: 100%;
        }

        .farm-map-eyebrow {
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 2px;
          color: #668653;
        }

        .farm-map-header h2 {
          font-size: 28px;
          margin: 9px 0;
        }

        .farm-map-header p {
          color: #65766a;
          font-size: 14px;
        }

        .farm-map-search {
          display: flex;
          gap: 8px;
          margin: 18px 0;
        }

        .farm-map-search input {
          flex: 1;
          min-width: 0;
          padding: 13px;
          border: 1px solid #d8e2d1;
          border-radius: 9px;
          font-size: 14px;
        }

        .farm-map-search button,
        .farm-map-tools button {
          background: #183e2d;
          color: white;
          border: 0;
          border-radius: 9px;
          padding: 11px 15px;
          cursor: pointer;
          font-weight: 700;
        }

        .farm-map-wrapper {
          position: relative;
        }

        .farm-map-canvas {
          width: 100%;
          height: 470px;
          border-radius: 14px;
          overflow: hidden;
        }

        .farm-map-tools {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
          position: absolute;
          left: 12px;
          top: 12px;
          z-index: 5;
          max-width: calc(100% - 24px);
        }

        .farm-map-tools button {
          font-size: 11px;
          padding: 9px 11px;
          box-shadow: 0 2px 8px #0003;
        }

        .farm-map-tools button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .farm-map-information {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-top: 18px;
        }

        .farm-map-information div {
          background: white;
          border: 1px solid #e2e8dc;
          border-radius: 12px;
          padding: 14px;
          min-width: 0;
        }

        .farm-map-information span,
        .farm-map-information small {
          display: block;
          font-size: 10px;
          color: #718173;
        }

        .farm-map-information strong {
          display: block;
          font-size: 17px;
          margin: 8px 0;
          overflow-wrap: anywhere;
        }

        .farm-map-message {
          font-size: 13px;
          color: #486d3c;
          margin-top: 14px;
        }

        .farm-map-save {
          margin-top: 15px;
          width: 100%;
          padding: 15px;
          border: 0;
          border-radius: 99px;
          background: #183e2d;
          color: white;
          font-weight: 800;
          cursor: pointer;
        }

        .farm-map-save:disabled {
          opacity: 0.65;
          cursor: wait;
        }

        @media (max-width: 600px) {
          .farm-map-information {
            grid-template-columns: 1fr;
          }

          .farm-map-canvas {
            height: 390px;
          }

          .farm-map-tools button {
            font-size: 10px;
            padding: 8px;
          }
        }
      `}</style>
    </div>
  );
}
