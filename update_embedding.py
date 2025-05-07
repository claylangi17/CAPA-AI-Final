import re

# Read the file
file_path = 'd:\\Coding\\CAPA AI Final - Copy\\CAPA AI Assistant\\ai_learning.py'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Define the pattern to find the embedding function
old_pattern = r"""try:\s+result = embedding_model\.embed_content\(text\)\s+return result\["embedding"\]\s+except Exception as e:"""

# Define the replacement
new_code = """try:
                    # Use the correct embedding method based on the Gemini API
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result["embedding"]
                except Exception as e:"""

# Replace all occurrences
updated_content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

# Write the updated content back to the file
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(updated_content)

print("Updated embedding functions in ai_learning.py")
