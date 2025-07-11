import tempfile
import google.generativeai as genai
from supabase import create_client, Client
import io

# Supabase configuration
SUPABASE_URL = "https://rizamamuiwyyplawssvr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpemFtYW11aXd5eXBsYXdzc3ZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjEzMDcwMiwiZXhwIjoyMDY3NzA2NzAyfQ.RYVgSqjNiHcWWTrhrmUl5BuCBxiZeZjfQwo3pI3EjFw"
BUCKET_NAME = "news-summary"

def upload_to_supabase_direct(content: str, file_name: str) -> str:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Write content to a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp.flush()  # Ensure all content is written
        tmp_path = tmp.name

    # Remove existing file if any
    try:
        supabase.storage.from_(BUCKET_NAME).remove([file_name])
    except Exception as e:
        print(f"⚠️ Skipped deletion (file may not exist): {e}")

    # Upload using local file path
    supabase.storage.from_(BUCKET_NAME).upload(file_name, tmp_path)

    # Return public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
    return public_url


def get_news_summary(stock_name: str, ticker_symbol: str, file_name: str = "generated_text.txt") -> str:
    API_KEY = "AIzaSyCw7R-FDCBts6kZF8F0rF5UVmgQljJ-dkM"
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = (
        f"Find all financial and stock-related news about {stock_name} ({ticker_symbol}) from the past 30 days. "
        "Summarize major developments, financial reports, partnerships, management changes, regulations, or trends."
    )

    response = model.generate_content(prompt)

    # Upload directly to Supabase
    file_url = upload_to_supabase_direct(response.text, file_name)

    print(f"✅ File uploaded to Supabase: {file_url}")
    return response.text
