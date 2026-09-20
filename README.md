# 🧠 MEMORA

### Learn it. Understand it. Remember it.

MEMORA is an AI-powered personalized learning platform designed to help students understand difficult topics, revise faster, plan their studies, and learn from their own study materials.

## 🌐 Live Demo

https://memora-learning-ai.onrender.com

## 📌 Problem

Students often use different applications for different study needs:

- Understanding difficult concepts
- Summarizing notes
- Preparing for quizzes
- Planning study time
- Revising before exams
- Learning from PDFs and presentations

Switching between different tools can make studying less organized and time-consuming.

## 💡 Solution

MEMORA brings these learning activities together in one student-focused platform.

Students can enter a topic or provide study material, and MEMORA uses AI to generate useful learning content in a simple and understandable format.

## ✨ Features

### 🧠 AI Study Tools

- Explain difficult topics simply
- Summarize study content
- Generate quizzes
- Improve written answers
- Explain concepts in an easier way
- Help students when they don't understand a topic

### ⚡ Quick Study

Students can enter a topic and choose a short study duration.

MEMORA creates a focused mini learning session containing:

- Core concept
- Important points
- Simple example
- Quick practice
- Memory trick
- Final recap

### 📅 Study Planner

Students can enter:

- Exam name
- Exam date
- Subjects
- Available study hours

MEMORA generates a structured study plan with specific study topics and activities.

### 🍅 Pomodoro Focus Mode

A built-in study timer helps students organize focused study sessions and breaks.

Available modes include:

- 25 / 5
- 50 / 10
- 15 / 5

### 📎 Upload & Study

Students can upload study material including:

- PDF
- PPT
- PPTX
- TXT
- JPG
- JPEG
- PNG
- WEBP

The uploaded content can then be used for learning activities such as:

- Summarization
- Simple explanations
- Important points
- Quiz generation

## 🤖 AI Integration

MEMORA uses the Gemini API to generate personalized learning content.

The application uses structured prompts instead of treating the AI as a generic chatbot.

Different learning tasks use different instructions so that the generated response is appropriate for the student's goal.

Examples include:

- Explanation prompts
- Summary prompts
- Quiz prompts
- Study-planning prompts
- Quick-study prompts
- Learning-material prompts

## 🛠️ Technology Stack

### Frontend

- HTML
- CSS
- JavaScript

### Backend

- Python
- Flask
- Flask-CORS

### AI

- Google Gemini API

### Document Processing

- PyPDF
- python-pptx

### Deployment

- GitHub
- Render

## 🔄 How MEMORA Works

```text
Student
   ↓
Enter topic / upload study material
   ↓
Select learning activity
   ↓
MEMORA processes the request
   ↓
Structured prompt sent to Gemini
   ↓
AI-generated learning content
   ↓
Student learns, practices and revises