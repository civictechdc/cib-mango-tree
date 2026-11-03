# Logging

The application uses a structured JSON logging system that provides consistent logging across all modules. The logging system automatically separates critical alerts from diagnostic information.

### Logging Architecture

- **Console Output**: Only `ERROR` and `CRITICAL` messages are displayed on stderr
- **File Output**: All messages from `INFO` level and above are written to log files
- **Log Format**: All logs are structured JSON for easy parsing and analysis
- **Log Rotation**: Log files automatically rotate at 10MB with 5 backup files retained
- **Log Location**: under the platform user-data directory (see the [Installation](../get-started/installation.md#project-storage) guide), in `logs/cib-mango-tree.log`

### Using the Logger in Your Code

#### Basic Usage

```python
from cibmangotree.app.logger import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened, but the program continues")
logger.error("A serious problem occurred")
logger.critical("A very serious error occurred, program may not be able to continue")
```

#### Example Log Output

**Console (stderr) - Only errors:**

```json
{"timestamp": "2025-07-30 16:42:33,914", "name": "cibmangotree.analyzers.hashtags", "level": "ERROR", "message": "Failed to process hashtags", "process_id": 12345, "thread_id": 67890, "app_version": "0.14.0"}
```

**Log File - INFO and above (default):**

```json
{"timestamp": "2025-07-30 16:42:33,910", "name": "cibmangotree.analyzers.hashtags", "level": "INFO", "message": "Starting hashtag analysis", "process_id": 12345, "thread_id": 67890, "app_version": "0.14.0"}
{"timestamp": "2025-07-30 16:42:33,914", "name": "cibmangotree.analyzers.hashtags", "level": "ERROR", "message": "Failed to process hashtags", "process_id": 12345, "thread_id": 67890, "app_version": "0.14.0"}
```

### Logging in Analyzers

When developing analyzers, add logging to help with debugging and monitoring:

```python
from cibmangotree.app.logger import get_logger

def main(context):
    logger = get_logger(__name__)

    input_reader = context.input()
    logger.info(
        "Starting analysis",
        extra={"input_parquet": str(input_reader.parquet_path)},
    )

    try:
        # Your analysis code here
        ...
        logger.info("Analysis completed successfully")
    except Exception:
        logger.error("Analysis failed", exc_info=True)
        raise
```

### Logging Best Practices

1. **Use Appropriate Log Levels**:
    
    - `DEBUG`: Detailed diagnostic information, only useful when debugging
    - `INFO`: General information about program execution
    - `WARNING`: Something unexpected happened, but the program continues
    - `ERROR`: A serious problem occurred
    - `CRITICAL`: A very serious error occurred, program may not be able to continue
2. **Include Context with `extra` Parameter**:
    
    ```python
    logger.info("Processing file", extra={
        "filename": filename,
        "file_size": file_size,
        "record_count": record_count
    })
    ```
    
3. **Log Exceptions Properly**:
    
    ```python
    try:
        risky_operation()
    except Exception as e:
        logger.error("Operation failed", exc_info=True)  # Includes stack trace
    ```
    
4. **Avoid Logging Sensitive Information**:
    
    - Never log passwords, API keys, or personal data
    - Be cautious with user-provided data

### Debugging with Logs

Launch with `uv run cibmt` (or `cibmangotree`). `__main__.py` calls `setup_logging` in `cibmangotree.app.logger` with file logging at **INFO** and above by default. There is no `--log-level` CLI flag today; use the log file under the platform user-data directory for diagnostics, or temporarily pass a lower level into `setup_logging` while developing.

### Log File Management

- Log files are automatically rotated when they reach 10MB
- Up to 5 backup files are kept (`cib-mango-tree.log.1`, `cib-mango-tree.log.2`, etc.)
- Older backup files are automatically deleted
- Log directory is created automatically if it doesn't exist

### Testing with Logs

When writing tests that involve logging:

```python
import logging
from cibmangotree.app.logger import get_logger

def test_my_function_logs_correctly(caplog):
    with caplog.at_level(logging.INFO):
        my_function()
        
    assert "Expected log message" in caplog.text
```

## Next Steps

Once you finish reading this it's recommended to check out the [architecture](../design-philosophy/architecture.md) section.