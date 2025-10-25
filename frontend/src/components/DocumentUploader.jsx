import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocs } from "../api/client"; // Ensure correct function name is imported
import styles from "../styles/AppStyles.module.css"; // Import central styles

// Define accepted file types (aligns with backend and dropzone config)
const ACCEPTED_FILES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
  "application/msword": [".doc"], // Note: .doc extraction might be less reliable
  "text/plain": [".txt"],
};

/**
 * Handles document uploads using drag-and-drop or file selection.
 */
function DocumentUploader() {
  const [files, setFiles] = useState([]); // Holds File objects ready for upload
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success' | 'error', message: string }

  // Upload Function (memoized)
  const handleUpload = useCallback(async (filesToUpload) => {
    if (!filesToUpload || filesToUpload.length === 0) {
      setUploadStatus({ type: "error", message: "No valid files to upload." });
      return;
    }

    setIsUploading(true);
    setUploadStatus({
      type: "loading",
      message: `Uploading ${filesToUpload.length} file(s)...`,
    }); // Use loading type

    try {
      const response = await uploadDocs(filesToUpload); // Use correct function name
      setUploadStatus({
        type: "success",
        message: `Success: Ingested ${response.total_documents_ingested} file(s) as ${response.total_chunks_created} chunks.`,
      });
      setFiles([]); // Clear file list on success
    } catch (error) {
      const apiErrorMessage = error.response?.data?.detail || error.message;
      setUploadStatus({
        type: "error",
        message: apiErrorMessage || "Failed to upload documents",
      });
      console.error("Upload error:", error);
    } finally {
      setIsUploading(false);
    }
  }, []); // Only depends on imported function, so stable

  // Dropzone Callback
  const onDrop = useCallback(
    (acceptedFiles, rejectedFiles) => {
      // Combine new valid files with existing ones, preventing exact duplicates
      const newFiles = acceptedFiles.filter(
        (newFile) =>
          !files.some(
            (existingFile) =>
              existingFile.name === newFile.name &&
              existingFile.size === newFile.size,
          ),
      );
      if (newFiles.length > 0) {
        setFiles((prevFiles) => [...prevFiles, ...newFiles]);
      }

      // Set status based on rejections
      if (rejectedFiles?.length > 0) {
        setUploadStatus({
          type: "warning",
          message: `${rejectedFiles.length} file(s) rejected (invalid type or size).`,
        }); // Use warning type
        console.warn("Rejected files:", rejectedFiles);
      } else if (newFiles.length > 0) {
        setUploadStatus(null); // Clear previous status if only good files were added
      }

      // --- Auto-upload behavior (if desired) ---
      // If you want to upload *immediately* after dropping/selecting:
      // if (acceptedFiles.length > 0) {
      //   handleUpload(acceptedFiles); // Upload only the newly accepted files
      // }
      // --- End Auto-upload ---
    },
    [files, handleUpload],
  ); // Add handleUpload if using auto-upload

  // Configure react-dropzone hook
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILES,
    multiple: true,
    disabled: isUploading,
  });

  // Function to remove a file from the staging list
  const removeFile = (indexToRemove) => {
    setFiles((prevFiles) =>
      prevFiles.filter((_, index) => index !== indexToRemove),
    );
    // Clear status if the list becomes empty or if removing fixes an error state
    if (files.length - 1 === 0) {
      setUploadStatus(null);
    }
  };

  // Helper Functions
  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (fileName) => {
    const extension = fileName?.split(".").pop()?.toLowerCase() || "";
    switch (extension) {
      case "pdf":
        return "📄"; // PDF icon
      case "docx":
        return "📝"; // Word icon
      case "txt":
        return "📃"; // Text icon
      default:
        return "📎"; // Generic file icon
    }
  };

  // --- Dynamic Styling for Dropzone ---
  const getDropzoneClassName = () => {
    let baseStyle = styles.dropzone;
    if (isDragActive) baseStyle += ` ${styles.dropzoneActive}`;
    if (isDragAccept) baseStyle += ` ${styles.dropzoneAccept}`;
    if (isDragReject) baseStyle += ` ${styles.dropzoneReject}`;
    if (isUploading) baseStyle += ` ${styles.dropzoneDisabled}`;
    return baseStyle;
  };

  // --- Render ---
  return (
    <div className={styles.uploaderContainer}>
      {/* Dropzone Area */}
      <div {...getRootProps()} className={getDropzoneClassName()}>
        <input {...getInputProps()} />
        <div className={styles.dropzoneIcon}>📤</div> {/* Upload Icon */}
        <p className={styles.dropzoneText}>
          {isDragActive
            ? isDragAccept
              ? "Drop files here to add them"
              : "Unsupported file type..."
            : "Drag & drop files here"}
        </p>
        <p className={styles.dropzoneHint}>
          or click to browse • PDF, DOCX, TXT supported
        </p>
      </div>

      {/* Status Messages (Loading, Success, Error, Warning) */}
      {uploadStatus && (
        <div
          className={`
          ${styles.alert}
          ${uploadStatus.type === "success" ? styles.alertSuccess : ""}
          ${uploadStatus.type === "error" ? styles.alertError : ""}
          ${uploadStatus.type === "warning" ? styles.alertWarning : ""}
          ${uploadStatus.type === "loading" ? styles.loadingIndicator : ""}
          `}
          style={{
            textAlign: "left",
            marginTop: files.length > 0 ? "0" : "var(--spacing-lg)",
          }} // Adjust margin based on file list visibility
        >
          <span className={styles.alertIcon}>
            {uploadStatus.type === "success"
              ? "✓"
              : uploadStatus.type === "error"
                ? "⚠️"
                : uploadStatus.type === "warning"
                  ? "ℹ️"
                  : "⏳"}
          </span>
          <div className={styles.alertContent}>
            <p className={styles.alertTitle}>
              {uploadStatus.type.charAt(0).toUpperCase() +
                uploadStatus.type.slice(1)}
            </p>
            <p className={styles.alertMessage}>{uploadStatus.message}</p>
          </div>
        </div>
      )}

      {/* File Staging List (if files are selected) */}
      {files.length > 0 && (
        <>
          <h3 className={styles.fileListTitle}>Files Ready for Upload:</h3>
          <div className={styles.fileList}>
            {files.map((file, index) => (
              <div key={index} className={styles.fileItem}>
                <div className={styles.fileInfo}>
                  <span className={styles.fileIcon}>
                    {getFileIcon(file.name)}
                  </span>
                  <div className={styles.fileDetails}>
                    <p className={styles.fileName} title={file.name}>
                      {file.name}
                    </p>{" "}
                    {/* Add title for long names */}
                    <p className={styles.fileSize}>
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className={styles.removeButton}
                  aria-label="Remove file"
                  disabled={isUploading} // Disable remove during upload
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          {/* Upload Button */}
          <button
            onClick={() => handleUpload(files)} // Pass current file list
            disabled={isUploading}
            className={styles.uploadButton}
          >
            {isUploading
              ? "Uploading..."
              : `Upload ${files.length} File${files.length > 1 ? "s" : ""}`}
          </button>
        </>
      )}
    </div>
  );
}

export default DocumentUploader;
