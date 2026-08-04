# Skyhook
Skyhook is a ground-station software suite for flight planning, real-time telemetry acquisition, data logging, and post-flight analysis.

## UI:
 - vuejs
 - websockets
 - multi instance support
 - DataStore: Pinia
 - Cool visuals
  - For charts: Apexcharts.js
  - 3D graphics: Three.js

## Backend:
 - python
 - websockets: socket.io
 - APs
 - Antenna
   - ebyte e220 400m30s (Narrowband)
   - WiFi-Link (UniFi) between Ground station and launch pad station
   - broadband module unknown
 - Database (sqlite)
