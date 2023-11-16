
import React, { useState } from 'react';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = (event) => {
    event.preventDefault();

    fetch(`http://home.danieltperry.me:5000/get_results?query=${encodeURIComponent(searchTerm)}`)
      .then(response => response.json())
      .then(data => setSearchResults(data))
      .catch(error => console.error('Error:', error));
  };

  return (
    <div>
      <h1>Steam ✨Vibe✨ Search</h1>
      <p>Describe the kind of game you're looking for, see what you get!</p>
      <form onSubmit={handleSearch}>
        <label htmlFor="search">Search:</label>
        <input type="text" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} />
        <button type="submit">Search</button>
      </form>
      <hr />
      <h2>Results</h2>
      <table>
        <thead>
          <tr>
            <th>App ID</th>
            <th>Icon</th>
            <th>Name</th>
            <th>Match Type</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {searchResults.map((result, index) => (
            <tr key={index}>
              <td>{result.appid}</td>
              <td><img src={`https://cdn.akamai.steamstatic.com/steam/apps/${result.appid}/header.jpg`} style={{ maxWidth: '240px', height: 'auto' }} /></td>
              <td><a href={`https://store.steampowered.com/app/${result.appid}`}>{result.name}</a></td>
              <td>{result.match_type}</td>
              <td>{result.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
