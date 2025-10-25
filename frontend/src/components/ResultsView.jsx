import React from "react";
import PropTypes from "prop-types";
import styles from "../styles/AppStyles.module.css"; // Import central styles

/**
 * Renders the SQL result as an HTML table with error handling.
 */
const SqlTable = ({ sqlResult }) => {
  // Handle cases: no result, error reported by backend, or empty rows
  if (!sqlResult) {
    return (
      <p className={styles.noResults}>
        No SQL query was executed for this request.
      </p>
    );
  }
  if (sqlResult.columns.length === 1 && sqlResult.columns[0] === "Error") {
    return (
      <>
        {sqlResult.generated_query &&
          sqlResult.generated_query !== "Failed" && (
            <p className={styles.metaItem}>
              <em>Generated Query (Failed Execution):</em>{" "}
              <code className={styles.generatedSql}>
                {sqlResult.generated_query}
              </code>
            </p>
          )}
        {sqlResult.generated_query === "Failed" && (
          <p className={styles.metaItem}>
            <em>SQL generation failed.</em>
          </p>
        )}
        <p className={`${styles.noResults} ${styles.errorText}`}>
          <strong>SQL Error:</strong>{" "}
          {sqlResult.rows[0]?.[0] || "Unknown database error"}
        </p>
      </>
    );
  }
  if (!sqlResult.rows || sqlResult.rows.length === 0) {
    return (
      <>
        <p className={styles.metaItem}>
          <em>Generated Query:</em>{" "}
          <code className={styles.generatedSql}>
            {sqlResult.generated_query || "N/A"}
          </code>
        </p>
        <p className={styles.noResults}>The query returned 0 rows.</p>
      </>
    );
  }

  // Render the table if data is valid
  return (
    <>
      <p className={styles.metaItem}>
        <em>Generated Query:</em>{" "}
        <code className={styles.generatedSql}>
          {sqlResult.generated_query || "N/A"}
        </code>
      </p>
      <div className={styles.tableWrapper}>
        <table className={styles.resultsTable}>
          <thead>
            <tr>
              {sqlResult.columns.map((col, index) => (
                <th key={index} className={styles.sqlTableTh}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sqlResult.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className={styles.sqlTableTd}>
                    {cell === null || cell === undefined ? (
                      <em className={styles.nullValue}>NULL</em>
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p
        className={styles.metaItem}
        style={{ marginTop: "var(--spacing-sm)", fontSize: "0.8em" }}
      >
        Showing {sqlResult.rows.length} row
        {sqlResult.rows.length !== 1 ? "s" : ""}
      </p>
    </>
  );
};

// PropTypes for SqlTable
SqlTable.propTypes = {
  sqlResult: PropTypes.shape({
    columns: PropTypes.arrayOf(PropTypes.string).isRequired,
    rows: PropTypes.arrayOf(PropTypes.array).isRequired,
    generated_query: PropTypes.string,
  }),
};

/**
 * Renders the document results (extracted answers) as cards.
 */
const DocumentCards = ({ documentResults }) => {
  if (!documentResults || documentResults.length === 0) {
    return (
      <p className={styles.noResults}>No relevant answer found in documents.</p>
    );
  }

  // Expecting only one result now with the extracted answer
  const doc = documentResults[0];

  return (
    // We display only the single best answer card now
    <div className={styles.documentCard}>
      <div className={styles.documentCardHeader}>
        <h4 className={styles.documentCardTitle}>
          <span
            className={styles.documentIcon}
            role="img"
            aria-label="Document"
          >
            📄
          </span>
          {doc.source_file || "Unknown Source"}
        </h4>
        <span className={styles.scorebadge}>
          Relevance: {(doc.similarity_score * 100).toFixed(1)}%{" "}
          {/* Assuming score is 0-1 range */}
        </span>
      </div>

      {/* Apply the specific style for the extracted answer */}
      <div className={styles.documentCardContent}>
        {" "}
        {/* Container for answer */}
        <div className={styles.extractedAnswer}>{doc.answer}</div>
      </div>

      <div className={styles.documentCardFooter}>
        <span>Source Chunk: {doc.chunk_index ?? "N/A"}</span>
        {/* Add other footer info if needed */}
      </div>
    </div>
  );
};

// Update PropTypes for the change from content to answer
DocumentCards.propTypes = {
  documentResults: PropTypes.arrayOf(
    PropTypes.shape({
      source_file: PropTypes.string,
      chunk_index: PropTypes.number.isRequired,
      answer: PropTypes.string.isRequired, // Expecting the answer field
      similarity_score: PropTypes.number.isRequired,
    }),
  ),
};

/**
 * Main component to display query results using CSS Modules for styling.
 */
function ResultsView({ queryResult }) {
  // Expects queryResult prop
  // Don't render if no result yet
  if (!queryResult) {
    return null;
  }

  const {
    query_type,
    sql_result,
    document_results,
    cache_status,
    performance_metrics,
  } = queryResult; // Destructure from the correct prop name

  // Helper to format query type nicely
  const formatQueryType = (type) => {
    const types = {
      sql: "Database",
      document: "Documents",
      hybrid: "Database + Documents",
      unknown: "Unknown (Default Document)",
    };
    return types[type] || type;
  };

  // Determine cache status class dynamically
  const cacheStatusClass =
    cache_status === "hit" ? styles.cacheHit : styles.cacheMiss;

  return (
    // Use resultsContainer for specific result section styling if needed, otherwise fragment is fine
    <div className={styles.resultsContainer}>
      {/* Header with Metadata */}
      <div className={styles.resultsHeader}>
        {/* Optional Title for the results section */}
        {/* <h2 className={styles.resultsTitle}>Query Results</h2> */}
        <div className={styles.resultsMeta}>
          <span className={styles.metaBadge}>
            <span className={styles.metaBadgeLabel}>Type:</span>
            <span className={styles.metaBadgeValue}>
              {formatQueryType(query_type)}
            </span>
          </span>
          {performance_metrics?.total_time_seconds !== undefined && (
            <span className={styles.metaBadge}>
              <span className={styles.metaBadgeLabel}>Time:</span>
              <span className={styles.metaBadgeValue}>
                {performance_metrics.total_time_seconds.toFixed(2)}s
              </span>
            </span>
          )}
          {cache_status && (
            <span className={`${styles.metaBadge} ${cacheStatusClass}`}>
              {/* Icon for cache status */}
              <span style={{ marginRight: "var(--spacing-xs)" }}>
                {cache_status === "hit" ? "⚡" : "⏳"}
              </span>
              Cache {cache_status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* Conditionally Render SQL Section */}
      {(query_type === "sql" || query_type === "hybrid") && (
        <section className={styles.resultSection}>
          <h3 className={styles.resultSectionTitle}>
            <span
              className={styles.resultSectionIcon}
              role="img"
              aria-label="Database"
            >
              🗄️
            </span>
            Database Result
          </h3>
          <SqlTable sqlResult={sql_result} />
        </section>
      )}

      {/* Conditionally Render Document Section */}
      {(query_type === "document" ||
        query_type === "hybrid" ||
        query_type === "unknown") && (
        <section className={styles.resultSection}>
          <h3 className={styles.resultSectionTitle}>
            <span
              className={styles.resultSectionIcon}
              role="img"
              aria-label="Books"
            >
              📚
            </span>
            Document Answer
          </h3>
          <DocumentCards documentResults={document_results} />
        </section>
      )}

      {/* Handle case where query ran but found nothing in either source */}
      {(!sql_result || !sql_result.rows || sql_result.rows.length === 0) &&
        (!document_results || document_results.length === 0) &&
        query_type !== "sql" &&
        query_type !== "document" &&
        query_type !== "hybrid" && ( // Avoid showing if one part succeeded
          <div className={styles.emptyState} style={{ minHeight: "150px" }}>
            {" "}
            {/* Smaller empty state */}
            <div className={styles.emptyStateIcon}>🤷</div>
            <p className={styles.emptyStateText}>
              No results found for your query in the database or documents.
            </p>
          </div>
        )}
    </div>
  );
}

// Main component PropTypes, ensure it matches App.jsx prop name
ResultsView.propTypes = {
  queryResult: PropTypes.shape({
    // Expects queryResult
    query_type: PropTypes.oneOf(["sql", "document", "hybrid", "unknown"]),
    sql_result: PropTypes.object,
    document_results: PropTypes.array,
    cache_status: PropTypes.oneOf(["hit", "miss"]),
    performance_metrics: PropTypes.shape({
      total_time_seconds: PropTypes.number,
    }),
  }),
};

export default ResultsView;
