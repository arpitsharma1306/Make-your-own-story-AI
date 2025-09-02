# Make Your Own Story AI

A full-stack AI storytelling platform that allows users to generate, explore, and interact with branching narratives using advanced AI.

## 🚀 Features

- Interactive Story Generation: Users can create unique stories and explore multiple branching outcomes.  
- AI-Powered Narrative: Integrated Google’s Gemini-1.5-Flash API for real-time story generation.  
- Full-Stack Architecture: Built with React (Vite) frontend, FastAPI backend, and persistent data storage using SQLAlchemy + SQLite.  
- Cloud Deployment: Frontend and backend hosted on Choreo Cloud with secure runtime configuration and API key management.  

## 💻 Tech Stack

- **Frontend:** React (Vite), Tailwind CSS, HTML, CSS, JavaScript  
- **Backend:** FastAPI, Python, SQLAlchemy, SQLite  
- **AI Integration:** Gemini-1.5-Flash API  
- **Deployment:** Choreo Cloud  

## 🛠️ Installation & Setup



```bash
git clone https://github.com/arpitsharma1306/Make-your-own-story-AI.git
cd Make-your-own-story-AI
pip install -r requirements.txt
cd frontend
npm install
API_KEY=your_gemini_api_key_here
uvicorn main:app --reload
npm run dev
