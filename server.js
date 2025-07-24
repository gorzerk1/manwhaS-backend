require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();

// === Set your backend domain (IP or hostname) ===
app.locals.domain = "https://server.manhwawut.online";

// === CORS Setup ===
app.use(cors({
  origin: ["https://manhwawut.online", "http://localhost:3000"]
}));

app.use(express.json());

// === Serve Static Files ===
app.use('/data/jsonFiles', express.static('/home/ubuntu/backend/data/jsonFiles'));
app.use('/backend/manwhaTitle', express.static('/home/ubuntu/backend/manwhaTitle'));
app.use('/backend/sideImage', express.static('/home/ubuntu/backend/sideImage'));
app.use('/backend/updateChap', express.static('/home/ubuntu/backend/updateChap'));
app.use('/backend/pictures', express.static('/home/ubuntu/backend/pictures'));

// === Routes ===
app.use(require('./routes/filteredManwhas'));
app.use(require('./routes/latestUpdates'));
app.use(require('./routes/chapterData'));
app.use(require('./routes/description'));
app.use('/users', require('./routes/users'));


// === Start Server ===
const PORT = 4000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Backend server running at http://localhost:${PORT}`);
});
