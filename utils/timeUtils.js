function toTitleCase(str) {
  return str.replace(/-/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
}

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

module.exports = { toTitleCase, getTimeAgo };
