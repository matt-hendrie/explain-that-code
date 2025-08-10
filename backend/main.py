from typing import Union, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from fastapi import FastAPI, Request
from pydantic import BaseModel
import re
from os import getenv
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

class CodeExplanationRequest(BaseModel):
    language: str
    code_snippet: str
    user_explanation: str

class CodeExplanationResponse(BaseModel):
    language: str
    code_snippet: str
    user_explanation: str
    ai_feedback: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


def split_think_content(text: str) -> Dict[str, str]:
    """Split content into think section and response section"""
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, text, re.DOTALL)
    think_content = think_match.group(1).strip() if think_match else ""
    response_content = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

    return {
        "think": think_content,
        "response": response_content
    }


@app.get("/generate/{language}")
def generate_code_question(language: str, request: Request):
    template = """Write a self-contained code snippet (20 ± 5` logical lines, bug-free) in {language}.
It should: 

    Demonstrate a mid–level concept such as a specific algorithmic technique, well-known pattern, or useful std-library feature that isn’t immediately obvious to beginners.  
    Be idiomatic for {language} and compile/run without modification.  
     

Finish the snippet with the sole comment // TODO: explain this code (or language-appropriate equivalent).
Do not supply any further explanation."""

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(

        api_key=getenv("OPENAPI_KEY"),
        base_url=getenv("OPENAPI_ENDPOINT"),
        model=getenv("MODEL"),

    )
    chain = prompt | llm
    result = chain.invoke({"language": language})

    split_content = split_think_content(result.content)

    # Backend modification - detect content type or create separate endpoint
    if request.headers.get("accept") == "text/html":
        print("hello")
        return f"""
        <div class="code-display">
            <div class="language-badge">{language}</div>
            <div class="code-block">
                <pre><code>{split_content["response"]}</code></pre>
            </div>
        </div>
        """
    else:
        return {
            "language": language,
            "think_content": split_content["think"],
            "code_snippet": split_content["response"]
        }


@app.post("/explain-code")
def explain_code(request: CodeExplanationRequest):
    """Endpoint to evaluate user's explanation of code snippet"""

    template = """You receive two inputs: 

     

    {request.code_snippet}
    – A short, correct, idiomatic code snippet (≈ 20 logical lines) that illustrates one
    clearly-defined concept in LANGUAGE X
    – Contains no comments beyond: “// TODO: explain this code” (or language-appropriate) 
     

    {request.user_explanation}
    – A free-form text in which a learner tries to explain what the code does and
    which specific concept it is demonstrating. 
     

Task
Return a valid JSON object with exactly four boolean fields: 

• syntax_correct – true if the user describes the flow of execution in a way that would still make the code run as intended
• concept_correct – true if the user explicitly identifies the single concept the snippet was created to show (e.g., “memoised recursion”, “iterator invalidation avoidance”, “double-checked locking”, etc.)
• details_complete – true if the explanation covers all critical moving parts of the snippet (key variables, control-flow decisions, library calls) without omission
• clarity_adequate – true if the explanation is clear and could be understood by another student with the same background 

Overall accuracy 

accuracy = syntax_correct && concept_correct && details_complete && clarity_adequate 

Rules 

    Favor leniency on wording/terminology mismatches as long as the underlying idea is correct.  
    Do not penalise for spelling or grammatical errors.  
    Do not provide any additional text—return only the JSON.
     """

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(

        api_key=getenv("OPENAPI_KEY"),
        base_url=getenv("OPENAPI_ENDPOINT"),
        model=getenv("MODEL"),

    )
    chain = prompt | llm

    result = chain.invoke({
        "language": request.language,
        "code_snippet": request.code_snippet,
        "user_explanation": request.user_explanation
    })

    return CodeExplanationResponse(
        language=request.language,
        code_snippet=request.code_snippet,
        user_explanation=request.user_explanation,
        ai_feedback=result.content
    )