import axios from "axios";

const API_URL = "http://localhost:5000/analyze";

export const analyzeText = async (text) => {
  try {
    const response = await axios.post(API_URL, { comment: text });
    return response.data;
  } catch (err) {
    throw new Error(err.response?.data?.error || "An error occurred while fetching data");
  }
};
