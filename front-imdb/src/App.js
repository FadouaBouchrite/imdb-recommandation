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
      const response = await axios.post("http://localhost:5000/analyze", { comment:text });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred");
    }
  };

  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: "20px" }}>
      <h1>Sentiment Analysis</h1>
      <textarea
        rows="5"
        cols="50"
        placeholder="Enter your text here"
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ marginBottom: "10px", padding: "10px", fontSize: "16px" }}
      ></textarea>
      <br />
      <button
        onClick={analyzeText}
        style={{
          padding: "10px 20px",
          backgroundColor: "#007BFF",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
        }}
      >
        Analyze
      </button>

      {result && (
        <div style={{ marginTop: "20px" }}>
          <h2>Analysis Result:</h2>
          <p><strong>Sentiment:</strong> {result.sentiment}</p>
        </div>
      )}

      {error && (
        <div style={{ marginTop: "20px", color: "red" }}>
          <p>Error: {error}</p>
        </div>
      )}
    </div>
  );
}

export default App;
