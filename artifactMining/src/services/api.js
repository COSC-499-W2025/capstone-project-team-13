import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000"
});

export const uploadResume = (data) =>
  API.post("/upload", data);

export const getResumes = () =>
  API.get("/resumes");

export const getScore = (id) =>
  API.get(`/score/${id}`);

export const getPortfolio = () => {
  const token = localStorage.getItem("token");
  return API.get("/portfolio", {
    headers: { Authorization: `Bearer ${token}` }
  });
};
export const generatePortfolio = () => {
  const token = localStorage.getItem("token");
  return API.post("/portfolio/generate", {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
};