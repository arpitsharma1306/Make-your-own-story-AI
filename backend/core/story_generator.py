from sqlalchemy.orm import Session

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from core.config import settings
from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()

class StoryGenerator:
    @classmethod
    def _extract_json(cls, text: str) -> str:
        """
        Extract valid JSON from text that might contain additional content.
        This handles cases where the model outputs text before or after the JSON.
        """
        # Try to find JSON by looking for matching braces
        try:
            # Find the first opening brace
            start_idx = text.find('{')
            if start_idx == -1:
                print("No JSON object found in response")
                return text
                
            # Track brace depth to find the matching closing brace
            depth = 0
            in_string = False
            escape_next = False
            
            for i in range(start_idx, len(text)):
                char = text[i]
                
                # Handle string literals and escaping
                if char == '\\' and not escape_next:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                escape_next = False
                
                # Only count braces outside of strings
                if not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        
                    # When we find the matching closing brace, extract the JSON
                    if depth == 0 and i > start_idx:
                        json_str = text[start_idx:i+1]
                        print(f"Extracted JSON object of length {len(json_str)}")
                        
                        # Validate it's proper JSON by parsing it
                        json.loads(json_str)  # This will raise an exception if invalid
                        return json_str
            
            # If we get here, we didn't find a matching closing brace
            print("No complete JSON object found")
            return text
            
        except Exception as e:
            print(f"Error extracting JSON: {str(e)}")
            return text
    
    @classmethod
    def _call_gemini_api(cls, prompt: str) -> str:
        """Call the Gemini API directly with robust error handling."""
        api_key = settings.GOOGLE_API_KEY
        model = "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            }
        }
        
        try:
            print("Sending request to Gemini API...")
            response = requests.post(url, json=payload, timeout=60)  # Increased timeout to 60 seconds
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            response_json = response.json()
            print(f"Received response with status code: {response.status_code}")
            
            if 'candidates' in response_json and len(response_json['candidates']) > 0:
                content = response_json['candidates'][0]['content']
                if 'parts' in content and len(content['parts']) > 0:
                    text = content['parts'][0]['text']
                    # Clean the response to extract only the JSON part
                    print("Cleaning response text to extract JSON")
                    return cls._extract_json(text)
            
            # If we got a response but no candidates, check for error
            if 'error' in response_json:
                error_msg = response_json['error'].get('message', 'Unknown API error')
                print(f"Error in Gemini API response: {error_msg}")
                print(f"Response JSON: {json.dumps(response_json)[:200]}...")
                raise Exception(f"Gemini API error: {error_msg}")
                
            print("No valid candidates in response")
            return "No valid response from Gemini API"
            
        except requests.exceptions.RequestException as e:
            # Handle network errors, timeouts, etc.
            print(f"Network error when calling Gemini API: {str(e)}")
            raise Exception(f"Network error when calling Gemini API: {str(e)}")
        except Exception as e:
            # Handle any other errors
            print(f"Error calling Gemini API: {str(e)}")
            raise Exception(f"Error calling Gemini API: {str(e)}")

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy")-> Story:
        # Create the full prompt
        full_prompt = f"{STORY_PROMPT}\n\nCreate the story with this theme: {theme}\n\nPlease format your response as a JSON object with the following structure:\n{{\n  \"title\": \"Story Title\",\n  \"rootNode\": {{\n    \"content\": \"Node content text\",\n    \"isEnding\": false,\n    \"isWinningEnding\": false,\n    \"options\": [{{\n      \"text\": \"Option text\",\n      \"nextNode\": {{\n        \"content\": \"Next node content\",\n        \"isEnding\": false,\n        \"isWinningEnding\": false,\n        \"options\": []\n      }}\n    }}]\n  }}\n}}"
        
        # Call Gemini API directly
        try:
            print(f"Calling Gemini API for theme: {theme}")
            response_text = cls._call_gemini_api(full_prompt)
            print(f"Received response from Gemini API, length: {len(response_text)}")
            
            # Parse the response into our expected format
            try:
                # Try to parse as JSON
                json_data = json.loads(response_text)
                print("Successfully parsed JSON response")
                # Validate the story structure against our model
                story_structure = StoryLLMResponse.model_validate(json_data)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Response text (first 100 chars): {response_text[:100]}...")
                # If JSON parsing fails, create a simple story structure
                story_structure = StoryLLMResponse(
                    title=f"{theme.capitalize()} Story",
                    rootNode=StoryNodeLLM(
                        content=response_text[:500],  # Use first 500 chars as content
                        isEnding=True,
                        isWinningEnding=True,
                        options=[]
                    )
                )
            except Exception as e:
                print(f"Model validation error: {str(e)}")
                # If model validation fails, create a simple story structure
                story_structure = StoryLLMResponse(
                    title=f"{theme.capitalize()} Story",
                    rootNode=StoryNodeLLM(
                        content=response_text[:500],  # Use first 500 chars as content
                        isEnding=True,
                        isWinningEnding=True,
                        options=[]
                    )
                )
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            # If API call fails, create a fallback story
            story_structure = StoryLLMResponse(
                title=f"Error: {theme.capitalize()} Story",
                rootNode=StoryNodeLLM(
                    content=f"We encountered an error while generating your story: {str(e)}",
                    isEnding=True,
                    isWinningEnding=False,
                    options=[]
                )
            )

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content if hasattr(node_data, "content") else node_data["content"],
            is_root=is_root,
            is_ending=node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"],
            is_winning_ending=node_data.isWinningEnding if hasattr(node_data, "isWinningEnding") else node_data["isWinningEnding"],
            options=[]
        )
        db.add(node)
        db.flush()

        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(db, story_id, next_node, False)

                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            node.options = options_list

        db.flush()
        return node