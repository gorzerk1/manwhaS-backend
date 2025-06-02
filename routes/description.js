const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

router.get('/api/description/:mangaName', async (req, res) => {
  const { mangaName } = req.params;
  const descPath = `/home/ubuntu/backend/data/jsonFiles/${mangaName}/manwhaDescription.json`;

  try {
    if (!fs.existsSync(descPath)) {
      return res.status(404).json({ error: 'Description not found' });
    }

    const raw = fs.readFileSync(descPath, 'utf-8');
    const data = JSON.parse(raw);

    const latestUpload = data.uploadTime?.[data.uploadTime.length - 1]?.time || "--";
    const updatedOn = latestUpload.split(' ')[1] || "--";

    const domain = req.app.locals.domain || '';

    res.json({
      ...data,
      imagelogo: `${domain}/${data.imagelogo}`,
      sideImage: `${domain}/backend/sideImage/${mangaName}_sideimage.webp`,
      updatedOn
    });

  } catch (err) {
    console.error("❌ Error in /api/description:", err);
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
