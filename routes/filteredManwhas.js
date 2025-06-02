const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

router.get('/api/filtered-manwhas', async (req, res) => {
  try {
    const jsonPath = '/home/ubuntu/backend/data/jsonFiles';
    const folders = fs.readdirSync(jsonPath);
    const now = new Date();
    const allChapters = [];

    const toTitleCase = str => str.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    for (const folder of folders) {
      const descPath = path.join(jsonPath, folder, 'manwhaDescription.json');
      if (!fs.existsSync(descPath)) continue;

      const raw = fs.readFileSync(descPath);
      const json = JSON.parse(raw);
      const uploadList = json.uploadTime;
      const updateImage = json.updateChap;

      if (!uploadList || !Array.isArray(uploadList)) continue;

      for (const item of [...uploadList].reverse()) {
        const [hourMin, datePart] = item.time.split(' ');
        const [hour, minute] = hourMin.split(':');
        const [day, month, year] = datePart.split('/');

        const itemTime = new Date(Date.UTC(
          parseInt(year), parseInt(month) - 1, parseInt(day),
          parseInt(hour), parseInt(minute)
        ));

        const diffDays = (now - itemTime) / (1000 * 60 * 60 * 24);
        if (diffDays > 3) break;

        const diffSeconds = (now - itemTime) / 1000;
        let timeAgo = 'just now';
        if (diffSeconds < 3600) timeAgo = `${Math.floor(diffSeconds / 60)} minutes ago`;
        else if (diffSeconds < 86400) timeAgo = `${Math.floor(diffSeconds / 3600)} hours ago`;
        else timeAgo = `${Math.floor(diffSeconds / 86400)} days ago`;

        allChapters.push({
          manwhaName: folder,
          title: toTitleCase(json.name || folder),
          chapter: `Chapter ${item.chapter}`,
          time: item.time,
          timeAgo,
          timestamp: itemTime.getTime(),
          image: updateImage ? `https://server.manhwawut.online/${updateImage}` : ''
        });
      }
    }

    allChapters.sort((a, b) => b.timestamp - a.timestamp);
    res.json(allChapters);
  } catch (err) {
    console.error('❌ Error in /api/filtered-manwhas:', err);
    res.status(500).send('Server error');
  }
});

module.exports = router;
