from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.post('/echo')
async def echo(file: Annotated[(bytes, File())]):
    return {"file_size": len(file), "file name": "a.txt"}

@app.post('/api')
async def echolarge(question: str = Form(...), files: list[UploadFile] = File(...)):
    contents = [await file.read() for file in files]
    res = []
    for x in zip(files, contents):
        o = {}
        o['filename'] = x[0].filename
        o['file_size'] = x[0].size
        o['content'] = x[1]
        res.append(o)
    out = None
    for y in res:
        if y['filename'] in question:
            out = y['file_size']
    return {"res": res, "out": out}



@app.get('/')
async def homepage():
    return {"Message": "Welcome to darkos.local:8000 !", "status": 200}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000 )