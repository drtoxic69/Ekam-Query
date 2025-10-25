import { useState, useCallback } from "react"; // Added useCallback import
import DocumentUploader from "./components/DocumentUploader";
import QueryPanel from "./components/QueryPanel";
import ResultsView from "./components/ResultsView";
import { submitQuery } from "./api/client";
import styles from "./styles/AppStyles.module.css";

function App() {
  const [queryResults, setQueryResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Use useCallback for stable function references passed as props
  const handleQuerySubmit = useCallback(async (query) => {
    if (!query.trim()) {
      setError("Please enter a query");
      setQueryResults(null); // Clear previous results on validation error
      return;
    }

    setIsLoading(true);
    setError(null);
    setQueryResults(null); // Clear previous results before new query

    try {
      const response = await submitQuery(query);
      setQueryResults(response);
    } catch (err) {
      // Try to get a more specific error message from Axios if available
      const apiErrorMessage = err.response?.data?.detail || err.message;
      setError(
        apiErrorMessage || "An error occurred while processing your query",
      );
      setQueryResults(null);
    } finally {
      setIsLoading(false);
    }
  }, []); // Empty dependency array as it doesn't depend on component state directly

  // Callbacks to pass down for loading/error state if needed by QueryPanel
  // (QueryPanel currently doesn't use these, but good practice to have if needed later)
  // const handleLoadingChange = useCallback((loading) => setIsLoading(loading), []);
  // const handleSetError = useCallback((errorMessage) => {
  //   setError(errorMessage);
  //   if (errorMessage) setQueryResults(null);
  // }, []);

  return (
    <div className={styles.appContainer}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <header className={styles.header}>
          <h1 className={styles.headerTitle}>Document Ingestion</h1>
          <p className={styles.headerSubtitle}>
            Upload documents to query with AI
          </p>
        </header>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Upload Files</h2>
          {/* Pass setError to DocumentUploader if you want App to show upload errors */}
          <DocumentUploader />
        </section>
      </aside>

      {/* Main Content */}
      <main className={styles.mainContent}>
        {/* Pass the actual submit handler and loading state */}
        <QueryPanel onSubmit={handleQuerySubmit} isLoading={isLoading} />

        {/* --- Results Area --- */}
        {/* Error Display */}
        {error &&
          !isLoading && ( // Show error only when not loading
            <div className={styles.resultsContainer}>
              {" "}
              {/* Optional container */}
              <div className={`${styles.alert} ${styles.alertError}`}>
                <span className={styles.alertIcon}>⚠️</span>
                <div className={styles.alertContent}>
                  <p className={styles.alertTitle}>Error</p>
                  <p className={styles.alertMessage}>{error}</p>
                </div>
              </div>
            </div>
          )}

        {/* Loading Display */}
        {isLoading && (
          <div className={styles.loadingContainer}>
            <div className={styles.spinner}></div>
            <p className={styles.loadingText}>Processing your query...</p>
          </div>
        )}

        {/* Results Display (Only when not loading, no error, and results exist) */}
        {!isLoading && !error && queryResults && (
          // --- FIX: Pass prop as 'queryResult' ---
          <ResultsView queryResult={queryResults} />
          // --- END FIX ---
        )}

        {/* Initial/Empty State (Only when not loading, no error, and no results) */}
        {!isLoading && !error && !queryResults && (
          <div className={styles.emptyState}>
            <div className={styles.emptyStateIcon}>🔍</div>
            <p className={styles.emptyStateText}>
              Enter a query above to search your documents and database
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
