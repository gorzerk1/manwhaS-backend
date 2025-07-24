const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./users.db');

// Register user (insert)
function registerUser(username, password) {
  const query = `INSERT INTO users (username, password) VALUES (?, ?)`;
  db.run(query, [username, password], function (err) {
    if (err) {
      console.error("❌ Register failed:", err.message);
    } else {
      console.log("✅ User registered with ID:", this.lastID);
    }
  });
}

// Get user by username (for login)
function getUserByUsername(username, callback) {
  const query = `SELECT * FROM users WHERE username = ?`;
  db.get(query, [username], (err, row) => {
    if (err) {
      console.error("❌ Query failed:", err.message);
      callback(null);
    } else {
      callback(row);
    }
  });
}

module.exports = { registerUser, getUserByUsername };
