const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

router.get('/api/chapter-data/:mangaName/:chapterNumber', async (req, res) => {
  const { mangaName, chapterNumber } = req.params;
  const chapterDir = `/home/ubuntu/backend/pictures/${mangaName}/chapter-${chapterNumber}`;
  const descPath = `/home/ubuntu/backend/data/jsonFiles/${mangaName}/manwhaDescription.json`;

  try {
    if (!fs.existsSync(chapterDir)) {
      return res.status(404).json({ error: 'Chapter folder not found' });
    }

    const domain = req.app.locals.domain; // 👈 dynamic base URL

    const imageFiles = fs.readdirSync(chapterDir).filter(f =>
      f.toLowerCase().match(/\.(webp|jpg|jpeg|png)$/)
    );

    const imageUrls = imageFiles.map(file =>
      `${domain}/backend/pictures/${mangaName}/chapter-${chapterNumber}/${file}`
    );

    let chapters = [];
    let maxChapter = null;

    if (fs.existsSync(descPath)) {
      const descRaw = fs.readFileSync(descPath, 'utf-8');
      const descData = JSON.parse(descRaw);

      chapters = (descData.uploadTime || [])
        .filter(e => e.chapter)
        .map(e => `chapter-${e.chapter}`)
        .reverse();

      maxChapter = descData.chaptersAmount || null;
    }

    res.json({
      images: imageUrls,
      chapters,
      maxChapter
    });

  } catch (err) {
    console.error("❌ Error in /api/chapter-data:", err);
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
