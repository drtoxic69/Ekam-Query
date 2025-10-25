import { useState } from "react";
import styles from "../styles/AppStyles.module.css";

function QueryPanel({ onSubmit, isLoading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Cmd/Ctrl + Enter
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={styles.queryContainer}>
      <h1 className={styles.queryTitle}>Query Your Data</h1>
      <p className={styles.querySubtitle}>
        Ask questions about your documents or database in natural language
      </p>

      <form onSubmit={handleSubmit} className={styles.queryForm}>
        <div className={styles.queryInputWrapper}>
          <textarea
            className={styles.queryInput}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="What would you like to know? (e.g., 'Show me all users from last month' or 'Summarize the key points from the uploaded documents')"
            disabled={isLoading}
          />
          <button
            type="submit"
            className={styles.queryButton}
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? "Searching..." : "Submit"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default QueryPanel;
