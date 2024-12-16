import React, { useState } from "react";
import { analyzeText } from "./api";
import ResultCard from "./components/ResultCard";
import ErrorMessage from "./components/ErrorMessage";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyzeText = async () => {
    try {
      setError(null);
      const response = await analyzeText(text);
      setResult(response);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h1 className="header">Sentiment Analysis</h1>
        <textarea
          rows="5"
          cols="50"
          placeholder="Enter your text here"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="textarea"
        ></textarea>
        <div>
          <button onClick={handleAnalyzeText} className="button">
            Analyze
          </button>
        </div>
        {result && <ResultCard result={result} />}
        {error && <ErrorMessage message={error} />}
      </div>
    </div>
  );
}

export default App;
