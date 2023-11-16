
import React, { useState } from 'react';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (event) => {
    event.preventDefault();
    setIsSearching(true);

    fetch(`http://home.danieltperry.me:5000/get_results?query=${encodeURIComponent(searchTerm)}`)
      .then(response => response.json())
      .then(data => setSearchResults(data))
      .catch(error => console.error('Error:', error))
      .finally(() => setIsSearching(false));
  };

    return (
      <div>
        <h1>Text-Based Steam Search</h1>
        <div class="source">
        <img src={process.env.PUBLIC_URL + "/GitHub-logo.png"} style={{ maxWidth: '24px', height: 'auto' }} /><strong>Source:</strong><a href="https://github.com/Netruk44/steam-text-search">Netruk44/steam-text-search</a>
        </div>
        <p>Describe the kind of game you're looking for, see what you get!</p>
        <p><i>e.g. "An open world exploration-based game featuring resource gathering."</i></p>
        <p><strong>Tip:</strong> Try being descriptive. Describe an imaginary game. What is it about? What do you do? What's the ✨vibe✨?</p>
        <p><i>Disclaimer:</i> The search database is not yet fully populated. Only a randomly selected ~15k games can be found here.</p>
        <p><i>Disclaimer:</i> No filtering has been applied to the game list. The search results may contain adult content.</p>
        <form onSubmit={handleSearch}>
          <label htmlFor="search">Description:</label> 
          <input type="text" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} />
          <button type="submit" disabled={isSearching}>{isSearching ? 'Searching...' : 'Search'}</button><br />
        </form>
      <hr />
      <h2>Results</h2>
      <p><strong>Note:</strong> Scores below 80% are usually not great matches.</p>
      <p><strong>Note for the note:</strong> Scores above 80% do not guarantee a good match either 😊.</p>
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
                <td>{(result.score * 100).toFixed(2)}%</td>
              </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
