class PDFProcessingError(Exception):
    """Raised when an error occurs during PDF parsing or handling."""
    pass


class ExtractionValidationError(Exception):
    """Raised when extracted structured data fails schema validation."""
    pass


class PipelineExecutionError(Exception):
    """Raised when pipeline orchestration fails."""
    pass
