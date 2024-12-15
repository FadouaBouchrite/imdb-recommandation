// frontend/src/App.js
import React, { useState } from "react";
import axios from "axios";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const analyzeText = async () => {
    try {
      setError(null);
      const response = await axios.post("http://localhost:5000/analyze", { comment: text });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.header}>Sentiment Analysis</h1>
        <textarea
          rows="5"
          cols="50"
          placeholder="Enter your text here"
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={styles.textarea}
        ></textarea>
        <div>
          <button onClick={analyzeText} style={styles.button}>
            Analyze
          </button>
        </div>

        {result && (
  <div style={styles.result}>
    <h2 style={styles.subHeader}>Analysis Result:</h2>
    {(() => {
      let parsedContent;
      try {
        parsedContent = typeof result.sentiment_analysis.message.content === "string"
          ? JSON.parse(result.sentiment_analysis.message.content)
          : result.sentiment_analysis.message.content;
      } catch {
        parsedContent = null;
      }

      if (parsedContent) {
        return (
          <>
            <p style={styles.resultText}><strong>Sentiment:</strong> {parsedContent.sentiment}</p>
            <p style={styles.resultText}><strong>Score:</strong> {parsedContent.sentiment_score}</p>
            <p style={styles.resultText}><strong>Genres:</strong> {parsedContent.genres.join(", ")}</p>
            <p style={styles.resultText}><strong>Emotions:</strong> {parsedContent.emotions.join(", ")}</p>
          </>
        );
      } else {
        return <p style={styles.error}>Failed to parse sentiment analysis content.</p>;
      }
    })()}

    <h3 style={styles.subHeader}>Recommendations:</h3>
    <ul>
      {result.recommendations.map((rec, index) => (
        <li key={index} style={styles.resultText}>
        <a href={`https://www.imdb.com/title/${rec}`} target="_blank" rel="noopener noreferrer">
          {rec}
        </a>
      </li>
      
      ))}
    </ul>
  </div>
)}

        {error && (
          <div style={styles.error}>
            <p>{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f0f2f5",
    fontFamily: "'Roboto', sans-serif",
  },
  card: {
    backgroundColor: "white",
    padding: "30px",
    borderRadius: "8px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
    width: "100%",
    maxWidth: "600px",
  },
  header: {
    fontSize: "2rem",
    color: "#333",
    textAlign: "center",
    marginBottom: "20px",
  },
  textarea: {
    width: "100%",
    padding: "10px",
    fontSize: "16px",
    border: "1px solid #ccc",
    borderRadius: "5px",
    marginBottom: "20px",
    resize: "none",
  },
  button: {
    padding: "12px 25px",
    backgroundColor: "#007BFF",
    color: "white",
    border: "none",
    borderRadius: "5px",
    cursor: "pointer",
    fontSize: "16px",
    transition: "background-color 0.3s ease",
  },
  buttonHover: {
    backgroundColor: "#0056b3",
  },
  result: {
    marginTop: "20px",
    padding: "15px",
    backgroundColor: "#e9f7ff",
    borderRadius: "8px",
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
  },
  subHeader: {
    fontSize: "1.5rem",
    color: "#333",
  },
  resultText: {
    fontSize: "1rem",
    color: "#555",
  },
  error: {
    marginTop: "20px",
    padding: "10px",
    backgroundColor: "#ffe6e6",
    color: "#d9534f",
    borderRadius: "5px",
    fontWeight: "bold",
  },
};

export default App;
