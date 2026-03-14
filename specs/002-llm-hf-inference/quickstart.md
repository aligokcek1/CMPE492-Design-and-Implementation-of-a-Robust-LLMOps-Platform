# Quickstart: LLM Inference App with Hugging Face Integration

This guide explains how to set up and run the localhost Streamlit application.

## Prerequisites

- Python 3.11 or higher
- A Hugging Face account
- A Hugging Face User Access Token (with Write permissions if you intend to upload local models)

## Setup Instructions

1. **Clone the repository and navigate to the project root.**
   ```bash
   # (Assuming you are in the project root)
   ```

2. **Create a virtual environment and activate it.**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies.**
   ```bash
   # Ensure you have a requirements.txt file with streamlit, huggingface_hub, python-dotenv
   pip install -r requirements.txt
   ```

4. **Configure your environment.**
   Create a `.env` file in the root directory (or use the application's UI to save it, depending on implementation).
   ```env
   HF_TOKEN=your_hugging_face_token_here
   ```

5. **Initialize the local database.**
   *(If the application does not auto-initialize the SQLite database on startup)*
   ```bash
   python -c "from src.cache import ModelCache; ModelCache().init_db()"
   ```

## Running the Application

Start the Streamlit application:

```bash
streamlit run src/app.py
```

The application will open in your default web browser (typically at `http://localhost:8501`).

## Testing

To run the test suite:

```bash
pytest tests/
```
