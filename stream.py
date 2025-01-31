import re
import os
import json
import streamlit as st
from collections import defaultdict
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import nltk
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
nltk.download('wordnet')
nltk.download('omw-1.4')

## API KEY SET UP
working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))
API_KEY = config_data["openai_api_key"]
os.environ["openai_api_key"] = API_KEY

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Function to normalize names using NLP
def normalize_name(name):
    name = name.lower().strip()
    name = re.sub(r'[-.]', ' ', name)  # Replace dashes and dots with spaces
    name = re.sub(r'\b(i{1,3}|iv|v|vi{1,3}|ix|x)\b',
                  lambda m: str({'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10}[m.group()]),
                  name)  # Convert Roman numerals to numbers
    name = " ".join(lemmatizer.lemmatize(word) for word in name.split())  # Lemmatization
    return name

# Parse the markdown file and store data
def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    data = defaultdict(lambda: defaultdict(list))  # {district: {taluka: [villages]}}
    current_district = None
    current_taluka = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# '):  # District
            current_district = line[2:].strip()
            data[current_district] = defaultdict(list)
        elif line.startswith('## '):  # Taluka
            current_taluka = line[3:].strip()
            if current_district:
                data[current_district][current_taluka] = []
        elif line.startswith('- '):  # Village
            village = line[2:].strip()
            if current_district and current_taluka:
                data[current_district][current_taluka].append(village)    
    return data

# def search_village(data, query):
#     query = query.lower().strip()
#     for district, talukas in data.items():
#         for taluka, villages in talukas.items():
#             if query in (village.lower() for village in villages):
#                 return district, taluka
#     return None, None  # Always return a tuple

def search_village(data, query):
    query = normalize_name(query)
    best_match = None
    best_score = 0
    
    for district, talukas in data.items():
        for taluka, villages in talukas.items():
            for village in villages:
                normalized_village = normalize_name(village)
                score = fuzz.ratio(query, normalized_village)
                if score > best_score:
                    best_score = score
                    best_match = (district, taluka, village)
    
    if best_match and best_score > 80:  # Threshold for fuzzy matching
        return best_match
        # return best_match[0], best_match[1], best_match[2]
    return None # Always return a tuple 

# Load data once and keep it in memory
file_path = "data.md"  # Update this if the path is different
delhi_housing_data = parse_markdown(file_path)

# Set up LangChain prompt
llm = ChatOpenAI(temperature=0.7,openai_api_key=API_KEY)
prompt_template = PromptTemplate.from_template(
    "You are a helpful assistant that provides district and taluka information for villages in Delhi. Answer based on the provided dataset: {query}"
)
def get_response(query):
    result = search_village(delhi_housing_data, query)
    if result:
        district, taluka, village = result
        return f"Village '{village}' is in Taluka '{taluka}', District '{district}'."
    return f"Sorry, I couldn't find a match for '{query}'."
# Streamlit UI
st.title("Hello I'm MapMagnet: A Delhi Housing Chatbot")
st.write("Enter a village name, and I'll tell you its Taluka and District!")

user_input = st.text_input("Enter a village name:")
if user_input:
    response = get_response(user_input)
    st.write(response)

# Run Streamlit with: `streamlit run stream.py`
