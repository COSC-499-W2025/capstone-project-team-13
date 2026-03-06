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