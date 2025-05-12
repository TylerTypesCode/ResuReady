import logging

# Setup logging
def setup_logging():
    # Create a custom logger
    logger = logging.getLogger('flask_app')
    logger.setLevel(logging.DEBUG)  # Set minimum level of logging

    # Create a file handler that logs messages to a file (adjust path as needed)
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)  # Write INFO level and above to file

    # Create a console handler for logs to be output to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Display DEBUG level and above in console

    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Initialize logging
logger = setup_logging()