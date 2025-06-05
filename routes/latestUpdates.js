const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

router.get('/api/latest-updates', async (req, res) => {
  const manhwaList = require('../json/manhwa_list.json');
  const folders = Object.keys(manhwaList);

  function getTimeAgo(timeString) {
    if (!timeString) return '';
    const [time, date] = timeString.split(' ');
    const [hour, minute] = time.split(':').map(Number);
    const [day, month, year] = date.split('/').map(Number);
    const chapterDate = new Date(year, month - 1, day, hour, minute);
    const now = new Date();
    const diffMs = now - chapterDate;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);
    const diffMonth = Math.floor(diffDay / 30);
    const diffYear = Math.floor(diffDay / 365);
    if (diffYear > 0) return `${diffYear} year${diffYear > 1 ? 's' : ''} ago`;
    if (diffMonth > 0) return `${diffMonth} month${diffMonth > 1 ? 's' : ''} ago`;
    if (diffDay > 0) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    if (diffHr > 0) return `${diffHr} hour${diffHr > 1 ? 's' : ''} ago`;
    if (diffMin > 0) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    return "just now";
  }

  function toTitleCase(str) {
    return str.replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1));
  }

  const result = await Promise.all(
    folders.map(async (folder) => {
      try {
        const filePath = path.join('/home/ubuntu/backend/data/jsonFiles', folder, 'manwhaDescription.json');
        if (!fs.existsSync(filePath)) return null;

        const raw = fs.readFileSync(filePath);
        const data = JSON.parse(raw);

        const chapters = (data.uploadTime || [])
          .filter(c => c.chapter && c.time)
          .slice(-3)
          .reverse()
          .map(c => ({
            number: c.chapter,
            name: `Chapter ${c.chapter}`,
            time: getTimeAgo(c.time)
          }));

        const latestRawTime = data.uploadTime?.[data.uploadTime.length - 1]?.time || "";
        const [h, d] = latestRawTime.split(" ");
        const [hour, min] = h?.split(":") || [];
        const [day, month, year] = d?.split("/") || [];
        const latestTimestamp = new Date(`${year}-${month}-${day}T${hour}:${min}:00`).getTime() || 0;

        return {
          key: folder,
          title: toTitleCase(data.name || folder),
          image: data.imagelogo,
          chapters,
          latestTimestamp
        };
      } catch (err) {
        console.error(`❌ Failed processing ${folder}`, err);
        return null;
      }
    })
  );

  const sorted = result.filter(Boolean).sort((a, b) => b.latestTimestamp - a.latestTimestamp);
  res.json(sorted);
});

module.exports = router;
