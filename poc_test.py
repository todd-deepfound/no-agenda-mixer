#!/usr/bin/env python3
"""
POC: Test GROK AI for generating creative mix ideas
Start small, then build up
"""
import os
import json
from dotenv import load_dotenv
import openai

# Load environment
load_dotenv('config/.env')

# Initialize GROK client
client = openai.OpenAI(
    api_key=os.getenv('GROK_API_KEY'),
    base_url=os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
)

def test_basic_idea_generation():
    """Step 1: Just ask for mix ideas"""
    print("=== TEST 1: Basic Mix Ideas ===")
    
    prompt = """You're helping create end-of-show mixes for the No Agenda podcast.
    These are creative, funny audio compilations that used to close out the show.
    
    Come up with 3 creative mix ideas for Episode 1779. Be specific and fun!
    
    Examples of good mix types:
    - Supercuts of hosts saying a specific phrase
    - Musical remixes using show audio
    - Thematic compilations (all conspiracy talk, all jokes, etc.)
    - Callback montages (references to running gags)
    
    Format: Simple list with brief descriptions
    """
    
    response = client.chat.completions.create(
        model=os.getenv('GROK_MODEL', 'grok-3-latest'),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    print(response.choices[0].message.content)
    print("\n")
    return response.choices[0].message.content

def test_segment_identification():
    """Step 2: Identify specific segments to include"""
    print("=== TEST 2: Segment Identification ===")
    
    # Simulate having some show context
    show_context = """
    Episode 1779 topics included:
    - Discussion about UFO disclosures
    - Adam's rant about airline food
    - John's analysis of media manipulation
    - Multiple "In the morning!" greetings
    - Donation segment with funny donor names
    - Jingle: "COVID Booster Symphony"
    """
    
    prompt = f"""Given this No Agenda Episode 1779 context:
    {show_context}
    
    Create a JSON plan for a 2-minute "Best of Episode" mix with:
    - 5-6 specific segments to include
    - Suggested duration for each (5-30 seconds)
    - Why each segment is funny/interesting
    - Transition ideas between segments
    
    Be creative and specific!
    """
    
    response = client.chat.completions.create(
        model=os.getenv('GROK_MODEL', 'grok-3-latest'),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    mix_plan = json.loads(response.choices[0].message.content)
    print(json.dumps(mix_plan, indent=2))
    print("\n")
    return mix_plan

def test_creative_remix_idea():
    """Step 3: Generate a creative remix concept"""
    print("=== TEST 3: Creative Remix Concept ===")
    
    prompt = """Create a creative audio remix concept for No Agenda Episode 1779.
    
    Think like a DJ/producer. How would you remix show audio into something musical or artistic?
    
    Consider:
    - Using host catchphrases as rhythm/beats
    - Layering different conversations
    - Adding effects (reverb, echo, pitch shift)
    - Creating a musical structure (intro, verse, chorus, outro)
    - Telling a mini-story through audio clips
    
    Describe your remix concept in detail, including:
    1. Overall theme/vibe
    2. Key audio elements to use
    3. Basic structure/timeline
    4. Effects and transitions
    5. What makes it funny/entertaining
    """
    
    response = client.chat.completions.create(
        model=os.getenv('GROK_MODEL', 'grok-3-latest'),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    
    print(response.choices[0].message.content)
    print("\n")
    return response.choices[0].message.content

def test_mix_title_generator():
    """Step 4: Generate creative mix titles"""
    print("=== TEST 4: Mix Title Generator ===")
    
    prompt = """Generate 10 creative, funny titles for No Agenda end-of-show mixes.
    
    Style guide:
    - Puns are good
    - Pop culture references welcome
    - Play on show themes (media deconstruction, conspiracy theories, etc.)
    - Can reference hosts Adam Curry and John C. Dvorak
    - Should be catchy and memorable
    
    Examples of good titles:
    - "In The Morning: The Remix"
    - "Dimensional Shift Dance Party"
    - "The Amygdala Shrinking Shuffle"
    
    List 10 creative titles:
    """
    
    response = client.chat.completions.create(
        model=os.getenv('GROK_MODEL', 'grok-3-latest'),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    
    print(response.choices[0].message.content)
    print("\n")
    return response.choices[0].message.content

def main():
    """Run all POC tests"""
    print("No Agenda Mixer POC - Testing GROK AI Integration\n")
    
    try:
        # Test 1: Basic ideas
        ideas = test_basic_idea_generation()
        
        # Test 2: Specific segments
        segments = test_segment_identification()
        
        # Test 3: Creative remix
        remix = test_creative_remix_idea()
        
        # Test 4: Titles
        titles = test_mix_title_generator()
        
        print("=== POC COMPLETE ===")
        print("All tests passed! GROK is generating creative ideas successfully.")
        print("\nNext steps:")
        print("1. Parse actual show transcript/audio")
        print("2. Extract real timestamps")
        print("3. Create actual audio mixes based on AI suggestions")
        
    except Exception as e:
        print(f"Error during POC: {e}")
        print("Check your API key and connection")

if __name__ == "__main__":
    main()