import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Function to get the schema
export const fetchSchema = async () => {
  try {
    const response = await apiClient.get("/schema");
    return response.data;
  } catch (error) {
    console.error("Error fetching schema:", error);
    throw error;
  }
};

// Function to upload documents
export const uploadDocs = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  try {
    const response = await apiClient.post("/ingest/documents", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error uploading documents:", error);
    throw error;
  }
};

// Function to submit a query
export const submitQuery = async (queryText) => {
  try {
    const response = await apiClient.post("/query", { query: queryText });
    return response.data;
  } catch (error) {
    console.error("Error submitting query:", error);
    throw error;
  }
};
