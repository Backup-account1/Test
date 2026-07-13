# EV Charger Map - Telegram Mini App

A sample Telegram Mini App (TMA) that displays a map of electric vehicle charging stations with filtering and search capabilities.

## Features

- **Interactive Map**: View EV charging stations on an OpenStreetMap
- **Search**: Find chargers by name or address
- **Filters**: Filter by charger type (Tesla, Fast, Standard) and availability
- **Location**: Locate yourself and find nearby chargers
- **Charger Details**: View detailed information about each charging station
- **Responsive Design**: Works on mobile and desktop
- **Dark Mode Support**: Automatically adapts to Telegram's theme

## Project Structure

```
ev-charger-tma/
├── index.html      # Main HTML file
├── styles.css      # CSS styles
├── app.js          # JavaScript logic
└── README.md       # This file
```

## How to Use

### 1. Local Development

Simply open `index.html` in a web browser to test the app locally.

### 2. Deploy as Telegram Mini App

To deploy this as a Telegram Mini App:

1. **Host the files**: Upload the contents of this folder to a web server (e.g., GitHub Pages, Netlify, Vercel, or any static hosting)

2. **Create a Telegram Bot**:
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot with `/newbot` command
   - Get your bot token

3. **Set up the Web App**:
   - Talk to [@BotFather](https://t.me/BotFather)
   - Use `/setmenu` to set up your bot menu
   - Use `/setwebapp` to link your web app URL

4. **Configure the Web App**:
   - Your web app URL should point to where you hosted the `index.html` file
   - Telegram will inject the `telegram-web-app.js` script automatically

### 3. Testing in Telegram

1. Send a message to your bot
2. Click the menu button or use a command to open the web app
3. The EV Charger Map should load within Telegram

## Customization

### Adding Real Data

Replace the `sampleChargers` array in `app.js` with real data from an API. Here are some EV charger APIs you can use:

- [Open Charge Map API](https://openchargemap.org/site/develop/api)
- [PlugShare API](https://www.plugshare.com/developers)
- [ChargePoint API](https://developer.chargepoint.com/)

### Example API Integration

```javascript
// Replace the sampleChargers with API call
async function fetchChargers(lat, lng, radius = 10) {
    const response = await fetch(
        `https://api.openchargemap.io/v3/poi/?key=YOUR_API_KEY&latitude=${lat}&longitude=${lng}&distance=${radius}&distanceunit=km`
    );
    const data = await response.json();
    return data.map(item => ({
        id: item.ID,
        name: item.AddressInfo.Title,
        type: getChargerType(item),
        address: item.AddressInfo.AddressLine1,
        lat: item.AddressInfo.Latitude,
        lng: item.AddressInfo.Longitude,
        power: getPowerLevel(item),
        availability: item.StatusType?.IsOperational ? 'available' : 'busy',
        connectors: item.Connections?.map(c => c.ConnectionType.Title) || [],
        price: item.UsageCost || 'Unknown',
        distance: calculateDistance(lat, lng, item.AddressInfo.Latitude, item.AddressInfo.Longitude)
    }));
}
```

### Styling

Edit `styles.css` to customize the appearance. The app supports both light and dark modes automatically based on Telegram's theme.

### Map Provider

The app currently uses OpenStreetMap. You can switch to other tile providers by changing the tile layer URL in `app.js`:

```javascript
// Google Maps (requires API key)
L.tileLayer('https://mt.google.com/vt?x={x}&y={y}&z={z}', {
    attribution: '© Google Maps'
}).addTo(map);

// Mapbox (requires API key)
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: '© Mapbox',
    id: 'mapbox/streets-v11',
    accessToken: 'YOUR_MAPBOX_TOKEN'
}).addTo(map);
```

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Telegram WebView (iOS & Android)

## Dependencies

- [Leaflet](https://leafletjs.com/) - Interactive maps
- [Telegram WebApp JS](https://core.telegram.org/bots/webapps) - Telegram integration
- [OpenStreetMap](https://www.openstreetmap.org/) - Map tiles

All dependencies are loaded from CDNs, so no build process is required.

## License

This is a sample project. Feel free to use it as a starting point for your own Telegram Mini App.

## Screenshots

The app includes:
- A header with the app title
- Search box for finding chargers
- Filter dropdowns for charger type and availability
- Interactive map showing charger locations
- List of nearby chargers with details
- Locate me button to find your current position

## Notes

- For production use, replace the sample data with real API calls
- Consider adding error handling for network requests
- Implement proper loading states for better UX
- Add caching for offline support
- Consider adding user authentication if needed
