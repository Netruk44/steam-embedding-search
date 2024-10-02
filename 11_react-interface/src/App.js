
import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [instruction, setInstruction] = useState('');
  const [numResults, setNumResults] = useState(25);
  const [type, setType] = useState('all');
  const formRef = useRef(null);

  // Azure Host:
  // const API_BASE_URL = 'https://steamvibe-api.azurewebsites.net';

  // Personal Host:
  const API_BASE_URL = 'https://storage.danieltperry.me/steam_search';

  const doSearch = () => {
    setIsSearching(true);

    fetch(`${API_BASE_URL}/get_results?query=${encodeURIComponent(searchTerm)}&instruction=${encodeURIComponent(instruction)}&num_results=${numResults}&type=${type}`)
      .then(response => response.json())
      .then(data => {
        setSearchResults(data)
      })
      .catch(error => console.error('Error:', error))
      .finally(() => setIsSearching(false));
  }

  const doManualSearch = (searchTerm) => {
    setIsSearching(true);
    setSearchTerm(searchTerm);

    fetch(`${API_BASE_URL}/get_results?query=${encodeURIComponent(searchTerm)}&instruction=${encodeURIComponent(instruction)}&num_results=${numResults}&type=${type}`)
      .then(response => response.json())
      .then(data => {
        setSearchResults(data)
      })
      .catch(error => console.error('Error:', error))
      .finally(() => setIsSearching(false));
  }

  const handleSearch = (event) => {
    event.preventDefault();
    doSearch();
  };

  useEffect(() => {
    if (searchResults.length > 0) {
      formRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [searchResults]);

  return (
    <div>
      <h1>Embedding-Based Steam Search</h1>
      <div className="source">
        <img src={process.env.PUBLIC_URL + "/GitHub-logo.png"} style={{ maxWidth: '24px', height: 'auto' }} /><strong>Source:</strong><a href="https://github.com/Netruk44/steam-embedding-search">Netruk44/steam-embedding-search</a><br />
        <img src="https://www.danieltperry.me/ico/favicon-32x32.png" style={{ maxWidth: '24px', height: 'auto' }} /><strong>Dev Journal:</strong> On my <a href="https://www.danieltperry.me/post/instructor-as-search-engine/">personal website</a>.<br /><br />
        Game database last updated:<strong>2024-08-21</strong>
      </div>
      <p>Describe the kind of game you're looking for, see what you get!</p>
      <p><strong>Tips:</strong></p>
      <ul>
        <li>Longer descriptions tend to get better results. Short descriptions like "amazing visuals" and "farming sim" tend to return bad results.</li>
        <li>The limit is around 400 words for your description. That's about the length of a 5 paragraph essay. You have <em>LOTS</em> of space to write.</li>
        <li>Try describing an imaginary game. What is it about? What do you do? What's the ✨vibe✨? What would people enjoy about it?</li>
        <li>Try writing a review for the imaginary game. What would people say about it?</li>
        <li>Try asking ChatGPT (or similar) to expand a few key points into a more complete picture of a game.</li>
      </ul>
      <p><i>e.g. "An open-world exploration game where you are a lone pioneer in an untamed wilderness. Gather resources, craft tools, and build shelter as you explore diverse biomes, from lush forests to arid deserts. Survival depends on balancing food, water, and supplies, with tools degrading over time, encouraging careful planning. As you venture deeper, you’ll uncover ancient technologies and hidden ruins that reveal the world's forgotten history. Unlock advanced crafting and shape the land to your will in this immersive, resource-driven survival experience."</i></p>
      <p><strong>Alternatively:</strong></p>
      <ul>
        <li>Try entering the appid of a game you like to see the most similar games.</li>
        <li>To get the appid of a game, go to the Steam Store page for it:</li>
        <li><img src={process.env.PUBLIC_URL + "/appid.png"} style={{ maxWidth: '100%', height: 'auto' }} /></li>
      </ul>
      <form onSubmit={handleSearch} id="search-form" ref={formRef}>
        <label htmlFor="search">Description / AppID:</label>
        <textarea 
          rows="4" 
          cols="50" 
          value={searchTerm} 
          onChange={(event) => setSearchTerm(event.target.value)} 
        />
        {isAdvancedOpen && (
          <div className="advanced-section">
            <h3>Advanced Options</h3>
            <label htmlFor="instruction">Instruction:</label>
            <input type="text" value={instruction} onChange={(event) => setInstruction(event.target.value)} placeholder="Represent a video game that has a description of:" />
            <label htmlFor="numResults">Number of Results:</label>
            <input type="number" value={numResults} onChange={(event) => setNumResults(event.target.value)} min="1" max="100" /> <br />
            <label htmlFor="type">Type:</label>
            <select id="type" value={type} onChange={(event) => setType(event.target.value)}>
              <option value="all">All</option>
              <option value="description">Description</option>
              <option value="review">Review</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>
        )}
        <button type="submit" disabled={isSearching}>{isSearching ? 'Searching...' : 'Search'}</button>
        <button type="button" className='btn-clear' onClick={() => setSearchTerm('')}>Clear</button>
        <button type="button" className='btn-advanced' onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}>
          {isAdvancedOpen ? 'Hide Advanced' : 'Open Advanced'}
        </button>
      </form>
      <hr />
      <h2>Results</h2>
      <div className="results-container">
        {searchResults.map((result, index) => (
            <div className="results-card" key={index}>
              <a href={`https://store.steampowered.com/app/${result.appid}`} target="_blank" >
                <div className="result-info">
                  <img src={`https://cdn.akamai.steamstatic.com/steam/apps/${result.appid}/header.jpg`} />
                  <div>
                    <h3>{result.name}</h3>
                    <span>App ID:</span> {result.appid}<br />
                    <span>Match Type:</span> {result.match_type}<br />
                    <span>Score:</span> <span className="score">{(result.score * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </a>
              <div className="result-navigation">
                <button className="more-like-this-button" onClick={() => {
                  doManualSearch(result.appid);
                }}>More like this</button>
              </div>
            </div>
        ))}
      </div>
    </div>
  );
}

export default App;
