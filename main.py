from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import requests
import subprocess
import urllib.parse
import os
from zipfile import ZipFile
import pandas as pd
import json
import re
import sqlite3



AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')
AIPROXY_URL ='https://aiproxy.sanand.workers.dev/openai/v1/chat/completions'

PWD = os.getcwd()




def query_LLM(query:str):
    response = requests.post(
        url=AIPROXY_URL,
        headers= { 'Content-Type': 'application/json', 'Authorization': f'Bearer {AIPROXY_TOKEN}'},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Keep your answers precise, do not explain the procces also avoid any markdown in it."},
                {"role": "system", "content": "Also if any files are asked to be downloaded consider that all of them were downloaded before the query and are save in \'/tmp\' folder."},
                {"role": "user", "content": query}
            ]
        }
    )
    return response.json()['choices'][0]['message']['content']

def create_py(fname, code):
    with open(fname, 'w') as pyfile:
        pyfile.write(code)
    return run_command(f'python {fname}').strip()

def extract_zip(file, output_folder='tmp'):
    with ZipFile(file, 'r') as zp:
        zp.printdir()
        zp.extractall(output_folder)

def csv_to_df(csvfile):
    df = pd.read_csv(csvfile)
    return df

def sort_json(input_json):
    if not(isinstance(input_json, str)):
        input_json = json.dumps(input_json)
    data = json.loads(input_json)
    sorted_data = sorted(data, key=lambda x: (x["age"], x["name"]))
    return json.dumps(sorted_data, separators=(",", ":"))

def mv_name_getsha256sum(extract_folder):
    for root, _, files in os.walk(extract_folder):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore', newline='') as f:
                content = f.read()
            modified_content = re.sub(r'(?i)IITM', 'IIT Madras', content)
            with open(file_path, 'w', encoding='utf-8', errors='ignore', newline='') as f:
                f.write(modified_content)
    return run_command('cd mv && cat * | sha256sum').strip()

def run_command(command):
    return subprocess.check_output(command, shell=True, text=True)

def api_calls(method: str, url: str, data: dict=None, heads : dict=None):
    if method == 'GET':
        response = requests.get(url=url).json()
    if method == 'POST':
        response = requests.post(url=url, headers=heads, json=data)
    return response

def encode_url(url, params):
    url = url + '?' + urllib.parse.urlencode(params)
    return url

def compare_file(file1, file2):
    run_command(f'cd q4 && diff -y --suppress-common-lines {file1} {file2} | wc -l')

def query_db(db, query):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()[0]
    return result if result else 0

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

tool_list = tool_list = [
    {
        "type": "function",
        "function": {
            "name": "query_LLM",
            "description": "Queries the LLM with a given input string and returns a response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The input query to be processed by the LLM."}
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_py",
            "description": "Creates a Python file with given code and executes it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fname": {"type": "string", "description": "The filename of the Python script."},
                    "code": {"type": "string", "description": "The Python code to write into the file."}
                },
                "required": ["fname", "code"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_zip",
            "description": "Extracts a ZIP file to a specified folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Path to the ZIP file."},
                    "output_folder": {"type": "string", "description": "Folder to extract the contents into."}
                },
                "required": ["file", "output_folder"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "csv_to_df",
            "description": "Converts a CSV file into a Pandas DataFrame.",
            "parameters": {
                "type": "object",
                "properties": {
                    "csvfile": {"type": "string", "description": "Path to the CSV file."}
                },
                "required": ["csvfile"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sort_json",
            "description": "Sorts a JSON array by age and name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_json": {"type": "string", "description": "JSON array string to be sorted."}
                },
                "required": ["input_json"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mv_name_getsha256sum",
            "description": "Modifies file contents, renaming 'IITM' to 'IIT Madras' and computes SHA256 checksum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "extract_folder": {"type": "string", "description": "Folder containing extracted files."}
                },
                "required": ["extract_folder"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executes a shell command and returns the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."}
                },
                "required": ["command"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_file",
            "description": "Compares two files and returns the count of differing lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file1": {"type": "string", "description": "First file to compare."},
                    "file2": {"type": "string", "description": "Second file to compare."}
                },
                "required": ["file1", "file2"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]


def execute_fns(calls):
    for x in calls:
        o = {}
        fn = x['function']['name']
        args = json.loads(x['function']['arguments'])
        if fn == 'query_LLM':
            result = query_LLM(query=args['query'])
        return result

def LLM_function_calling(question:str):
    response = requests.post(
        url = AIPROXY_URL,
        headers={ 'Content-Type': 'application/json', 'Authorization': f'Bearer {AIPROXY_TOKEN}'},
        json={
            "model": "gpt-4o-mini",
            "messages":[
                {"role": "system", "content": "Consider all the files that need to be downloaded are in the Present Working Directory."},
                {"role": "system", "content": "Only reply in tool calls do not reply as a message, if there is a qustion that is solvable by LLM, use query_LLM function, do not answer directly."},
                {"role": "user", "content": question}
            ],
            "tools": tool_list,
            "tool_choice": "auto"
        }
    )
    return response.json()['choices'][0]['message']['tool_calls']



@app.post('/api')
async def echolarge(question: str = Form(...), files: list[UploadFile] = File(...)):
    for file in files:
        fname = f'./tmp/{file.filename}'
        with open(fname, 'wb') as buffer:
            buffer.write(await file.read())
        firstResponse = LLM_function_calling(question)
        result = execute_fns(firstResponse)
    return {"answer": result}



@app.get('/')
async def homepage():
    return {"Message": "Welcome to vercel for project2 by student2300", "status": 200}
