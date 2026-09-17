
import os
import time
from pypdf import PdfReader
from pptx import Presentation
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@app.route("/api/generate", methods=["POST"])
def generate():

    try:
        data = request.get_json()

        user_input = data.get("input", "").strip()
        mode = data.get("mode", "explain")

        # Check empty input
        if not user_input:
            return jsonify({
                "error": "Please enter something to study."
            }), 400


        # EXPLAIN
        if mode == "explain":

            prompt = f"""
You are MEMORA, an AI study assistant.

Explain the following topic in very simple language
for a college student.

Include:
1. Simple definition
2. How it works
3. One easy example
4. Three important points

Topic:
{user_input}
"""


        # SUMMARIZE
        elif mode == "summarize":

            prompt = f"""
You are MEMORA, an AI study assistant.

Summarize the following study material into
short, clear revision notes.

Use:
- Simple language
- Bullet points
- Important keywords
- Important facts

Study material:
{user_input}
"""
        # IMPORTANT POINTS
        elif mode == "important":
            prompt = f"""
You are MEMORA, an AI study assistant.

Extract the most important information from the
following study material for a college student.

Use exactly this structure:

## ⭐ Most Important Points

### 🔑 Core Concepts
Give the most important concepts in simple bullet points.

### 📌 Must Remember
Give the facts, definitions, formulas, or ideas
that the student should definitely remember.

### 🧠 Memory Tip
Give one simple trick to remember the main idea.

Keep the response concise and useful for revision.

Study material:
{user_input}
"""


        # QUIZ
        elif mode == "quiz":

            prompt = f"""
You are MEMORA, an AI study assistant.

Create 5 useful quiz questions from the following
study material.

Give:
- Question
- 4 options
- Correct answer
- Short explanation

Study material:
{user_input}
"""


        # IMPROVE ANSWER
        elif mode == "improve":

            prompt = f"""
You are MEMORA, an AI study assistant.

Analyze the student's answer below.

Give:
1. What is correct
2. What needs improvement
3. A better version of the answer
4. One tip for the student

Student answer:
{user_input}
"""


        # I DON'T GET IT
        elif mode == "simple":

            prompt = f"""
You are MEMORA's "I DON'T GET IT" mode.

The student is confused and needs the topic explained
as if they are learning it for the FIRST TIME.

IMPORTANT:
- Do NOT give a normal textbook explanation.
- Use very simple everyday words.
- Keep sentences short.
- Avoid unnecessary technical terminology.
- If a technical word is necessary, explain it immediately.
- Make the explanation friendly and encouraging.

Use exactly this structure:

## 😵 Let's Make It Super Easy

### 🧠 In One Sentence
Explain the topic in ONE very simple sentence.

### 🏠 Imagine This
Give a funny or relatable everyday-life analogy.

### 📦 Step-by-Step
Explain how it works in 3–5 very simple steps.

### 🎯 Easy Example
Give one small example that a college student can easily understand.

### 🧠 Remember It Like This
Give one short memory trick.

### ⚡ In Short
Give a final explanation in 1–2 simple sentences.

Topic:
{user_input}
"""


        # TEACH IT BACK
        elif mode == "teach":

            prompt = f"""
You are MEMORA's "Teach It Back" learning evaluator.

A student is trying to explain a topic in their own words.
Your job is to check how well they understand it.

Be supportive and encouraging.
Do not shame the student for mistakes.

Use exactly this structure:

## 🗣️ Teach It Back Feedback

### 🟢 What You Got Right
Mention the important ideas the student explained correctly.

### 🟡 What Is Missing
Mention important concepts or details that the student did not include.

### 🔴 What Needs Correction
Identify any incorrect statements and explain them simply.

### ✨ Better Explanation
Give a clear and simple version of the topic.

### 🧠 Memory Tip
Give one short trick to remember the important idea.

### 📊 Understanding Level
Give a simple rating:
- Excellent
- Good
- Needs More Practice

Topic:
{user_input}
"""


        else:

            return jsonify({
                "error": "Invalid study mode."
            }), 400


        response = None


        # Generate AI response
        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                break


            except Exception as error:

                # Gemini quota error
                if "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error):

                    print("ERROR: Gemini quota exceeded.")

                    return jsonify({
                        "error": "MEMORA AI limit has been reached. Please try again later."
                    }), 429


                # Temporary Gemini server error
                if "503" in str(error) and attempt < 2:

                    print("Gemini is busy. Retrying...")

                    time.sleep(3)


                else:

                    raise error


        return jsonify({
            "result": response.text
        })


    except Exception as error:

        print("ERROR:", error)

        return jsonify({
            "error": "MEMORA could not generate a response. Please try again."
        }), 500
        # ==========================================
# IMAGE STUDY 📷🧠
# ==========================================

@app.route("/api/study-image", methods=["POST"])
def study_image():

    try:

        # Check if image was uploaded
        if "image" not in request.files:
            return jsonify({
                "error": "Please upload an image."
            }), 400

        image = request.files["image"]

        # Check filename
        if image.filename == "":
            return jsonify({
                "error": "Please choose an image."
            }), 400

        # Read image data
        image_data = image.read()

        # Send image + instruction to Gemini
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                """
You are MEMORA, an AI study assistant.

Look at the uploaded study image and help the student
understand the material.

Give the answer using this structure:

## 🧠 What This Image Contains

Briefly explain what the image is about.

## 📚 Simple Explanation

Explain the important information in very simple language.

## ⭐ Important Points

Give the most important points the student should remember.

## 🧠 Memory Tip

Give one easy trick to remember the information.

## ❓ Quick Questions

Give 3 simple questions the student can use to test
their understanding.

Be clear, friendly and useful for a college student.
""",
                genai.types.Part.from_bytes(
                    data=image_data,
                    mime_type=image.content_type
                )
            ]
        )

        return jsonify({
            "result": response.text
        })

    except Exception as error:

        print("IMAGE ERROR:", error)

        if "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error):

            return jsonify({
                "error": "MEMORA AI limit has been reached. Please try again later."
            }), 429

        return jsonify({
            "error": "MEMORA could not study this image."
        }), 500
# ==========================================
# STUDY PDF 📄🧠
# ==========================================

@app.route("/api/study-pdf", methods=["POST"])
def study_pdf():

    try:

        # Check if PDF was uploaded
        if "file" not in request.files:
            return jsonify({
                "error": "Please upload a PDF."
            }), 400

        pdf_file = request.files["file"]

        # Check filename
        if pdf_file.filename == "":
            return jsonify({
                "error": "Please choose a PDF."
            }), 400

        # Read PDF
        reader = PdfReader(pdf_file)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        # Check whether text was extracted
        if not text.strip():
            return jsonify({
                "error": "MEMORA could not find readable text in this PDF."
            }), 400

        # For now, return extracted text
        return jsonify({
            "result": text
        })

    except Exception as error:

        print("PDF ERROR:", error)

        return jsonify({
            "error": "MEMORA could not read this PDF."
        }), 500
        # ==========================================
# STUDY POWERPOINT 📊🧠
# ==========================================

@app.route("/api/study-ppt", methods=["POST"])
def study_ppt():

    try:

        # Check if presentation was uploaded
        if "file" not in request.files:
            return jsonify({
                "error": "Please upload a PowerPoint file."
            }), 400

        ppt_file = request.files["file"]

        # Check filename
        if ppt_file.filename == "":
            return jsonify({
                "error": "Please choose a PowerPoint file."
            }), 400

        # Open PowerPoint
        presentation = Presentation(ppt_file)

        text = ""

        # Read every slide
        for slide_number, slide in enumerate(
            presentation.slides, start=1
        ):

            text += f"\n--- Slide {slide_number} ---\n"

            for shape in slide.shapes:

                if hasattr(shape, "text"):

                    if shape.text.strip():

                        text += shape.text + "\n"

        # Check whether text was extracted
        if not text.strip():
            return jsonify({
                "error": "MEMORA could not find readable text in this presentation."
            }), 400

        # Return extracted text
        return jsonify({
            "result": text
        })

    except Exception as error:

        print("PPT ERROR:", error)

        return jsonify({
            "error": "MEMORA could not read this presentation."
        }), 500
        # ==========================================
# STUDY TEXT FILE 📝🧠
# ==========================================

@app.route("/api/study-txt", methods=["POST"])
def study_txt():

    try:

        if "file" not in request.files:
            return jsonify({
                "error": "Please upload a text file."
            }), 400

        txt_file = request.files["file"]

        if txt_file.filename == "":
            return jsonify({
                "error": "Please choose a text file."
            }), 400

        text = txt_file.read().decode("utf-8", errors="replace")

        if not text.strip():
            return jsonify({
                "error": "MEMORA could not find any readable text in this file."
            }), 400

        return jsonify({
            "result": text
        })

    except Exception as error:

        print("TXT ERROR:", error)

        return jsonify({
            "error": "MEMORA could not read this text file."
        }), 500

        

if __name__ == "__main__":
    app.run(debug=True)

