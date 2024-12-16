import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import Papa from "papaparse";
import "./ResultCard.css";

function ResultCard({ result }) {
  const { sentiment_analysis, recommendations } = result;
  const [movieData, setMovieData] = useState([]);
  const [parsedContent, setParsedContent] = useState(null);
  const [matchedMovies, setMatchedMovies] = useState([]);

  // Parse sentiment analysis content
  useEffect(() => {
    try {
      const content =
        typeof sentiment_analysis.message.content === "string"
          ? JSON.parse(sentiment_analysis.message.content)
          : sentiment_analysis.message.content;
      setParsedContent(content);
    } catch (error) {
      console.error("Error parsing sentiment analysis content:", error);
      setParsedContent(null);
    }
  }, [sentiment_analysis]);

  // Load and parse CSV
  useEffect(() => {
    const loadCSV = async () => {
      try {
        const response = await fetch("/assets/films_data.csv");
        const csvText = await response.text();
        const parsed = Papa.parse(csvText, { header: true }).data;

        // Clean up data
        setMovieData(
          parsed.map((movie) => ({
            ...movie,
            ID: movie.ID?.trim(),
          }))
        );
      } catch (err) {
        console.error("Error loading or parsing CSV:", err);
      }
    };
    loadCSV();
  }, []);

  // Match recommendations with movie data
  useEffect(() => {
    if (movieData.length > 0) {
      const matches = movieData.filter((movie) =>
        recommendations.includes(movie.ID)
      );
      setMatchedMovies(matches);
    }
  }, [movieData, recommendations]);


  return (
    <div className="result">
      <h2 className="subHeader">Analysis Result:</h2>
      {parsedContent ? (
        <>
          <p><strong>Sentiment:</strong> {parsedContent.sentiment}</p>
          <p><strong>Score:</strong> {parsedContent.sentiment_score}</p>
          <p><strong>Genres:</strong> {parsedContent.genres.join(", ")}</p>
          <p><strong>Emotions:</strong> {parsedContent.emotions.join(", ") || "None"}</p>
        </>
      ) : (
        <p className="error">Failed to parse sentiment analysis content.</p>
      )}
      <h3 className="subHeader">Recommended Movies:</h3>
      {matchedMovies.length > 0 ? (
        <ul className="movie-list">
          {matchedMovies.map((movie, index) => (
            <li key={index} className="movie-item">
              <div className="movie-details">
                <a href={movie.Link} target="_blank" rel="noopener noreferrer">
                  <h4>{movie.Title}</h4>
                </a>
                <p>
                  <strong>Rating:</strong> {movie.Rate}
                </p>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>No matching recommendations found in the data.</p>
      )}
    </div>
  );
}

ResultCard.propTypes = {
  result: PropTypes.shape({
    sentiment_analysis: PropTypes.shape({
      message: PropTypes.shape({
        content: PropTypes.string.isRequired,
      }).isRequired,
    }).isRequired,
    recommendations: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
};

export default ResultCard;
