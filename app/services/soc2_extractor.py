# app/services/soc2_extractor.py

import json
import re
from pathlib import Path
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_perplexity import ChatPerplexity
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pdf_parser import extract_text
from soc2_scoring import calculate_soc2_score

# ----------------------
# Flexible JSON extractor
# ----------------------
def extract_json_from_text(text: str) -> dict:
    """
    1. Try to parse entire text as JSON.
    2. Else look for ```json ... ``` block.
    3. Else extract first standalone { ... } block.
    """
    t = text.strip()
    # 1) Direct JSON parse
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass

    # 2) Fenced ```json ... ```
    fence = re.compile(r'```json\s*(\{[\s\S]*?\})\s*```', re.MULTILINE)
    m = fence.search(text)
    if m:
        return json.loads(m.group(1))

    # 3) First standalone {...}
    brace = re.compile(r'\{[\s\S]*\}')
    m = brace.search(text)
    if m:
        return json.loads(m.group(0))

    raise ValueError("No JSON found in the input text.")

class SOC2Extractor:
    def __init__(self, api_key: str):
        
        # prompt_file = Path(__file__).parent.parent / "prompts" / "full_json_template.json"
        
        # Get absolute path to the project root (2 levels up from this file)
        base_dir = Path(__file__).resolve().parent.parent
        prompt_path = base_dir.parent / "prompts" / "full_json_template.json"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Template file not found: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            full_prompt = json.load(f)

        instruction = full_prompt.pop("instruction")
        schema_str = json.dumps(full_prompt, indent=2)
        escaped_schema = schema_str.replace("{", "{{").replace("}", "}}")

        template = (
            instruction
            + "\n\nHere is the JSON schema you must follow exactly (do NOT re-output this schema):\n"
            + escaped_schema
            + "\n\n{report_text}"
        )

        self.prompt = ChatPromptTemplate.from_template(template)
        self.llm = ChatPerplexity(model="sonar", api_key=api_key, temperature=0)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)

    def extract(self, pdf_path: str) -> Dict[str, Any]:
        raw = extract_text(pdf_path)
        chunks = self.splitter.split_text(raw)
        joined = "\n\n".join(chunks)

        chain = self.prompt | self.llm
        resp = chain.invoke({"report_text": joined})
        content = resp.content.strip()

        # match = re.search(r"(\{.*?\})\s*$", content, re.DOTALL)
        # if not match:
        #     raise ValueError("No JSON found in LLM response")
        
        # data = json.loads(match.group(1))
        
        # CHANGED: Use flexible JSON extractor instead of simple regex
        data = extract_json_from_text(content)
        
        score = calculate_soc2_score(data)
        return {"extracted": data, "score": score}







    # def extract(self, pdf_path: str) -> Dict[str, Any]:
    #     raw_text = extract_text(pdf_path)
    #     chunks = self.splitter.split_text(raw_text)

    #     structured_outputs: list[Dict[str, Any]] = []

    #     for chunk in chunks:
    #         try:
    #             chain = self.prompt | self.llm
    #             response = chain.invoke({"report_text": chunk})
    #             content = response.content.strip()

    #             match = re.search(r"(\{.*?\})\s*$", content, re.DOTALL)
    #             if not match:
    #                 continue  # Skip if no JSON found

    #             data = json.loads(match.group(1))
    #             structured_outputs.append(data)

    #         except Exception as e:
    #             print(f"Chunk error: {e}")
    #             continue

    #     if not structured_outputs:
    #         raise ValueError("No valid structured output extracted from any chunk.")

    #     merged_data = self.merge_extracted_data(structured_outputs)
    #     score = calculate_soc2_score(merged_data)

    #     return {"extracted": merged_data, "score": score}

    # def merge_extracted_data(self, outputs: list[dict]) -> dict:
    #     merged = {}

    #     for field in outputs[0].keys():
    #         values = [o.get(field) for o in outputs if field in o]

    #         if not values:
    #             continue
    #         if isinstance(values[0], list):
    #             merged[field] = [item for sublist in values for item in sublist]
    #         elif isinstance(values[0], str):
    #             merged[field] = " ".join(values)
    #         else:
    #             merged[field] = values[0]

    #     return merged
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#     import asyncio

# class SOC2Extractor:
#     # ... __init__ stays the same ...

#     async def extract(self, pdf_path: str) -> Dict[str, Any]:
#         raw_text = extract_text(pdf_path)
#         chunks = self.splitter.split_text(raw_text)

#         tasks = [self.process_chunk_async(chunk) for chunk in chunks]
#         results = await asyncio.gather(*tasks, return_exceptions=True)

#         structured_outputs = [r for r in results if isinstance(r, dict)]

#         if not structured_outputs:
#             raise ValueError("No valid structured output extracted from any chunk.")

#         merged_data = self.merge_extracted_data(structured_outputs)
#         score = calculate_soc2_score(merged_data)

#         return {"extracted": merged_data, "score": score}

#     async def process_chunk_async(self, chunk: str) -> dict:
#         try:
#             chain = self.prompt | self.llm
#             response = await chain.ainvoke({"report_text": chunk})  # 🧠 async version
#             content = response.content.strip()
#             match = re.search(r"(\{.*?\})\s*$", content, re.DOTALL)
#             if not match:
#                 return None
#             return json.loads(match.group(1))
#         except Exception as e:
#             print(f"Chunk error: {e}")
#             return None



#? ye just for knowledge, not used in the final code
# self.splitter = RecursiveCharacterTextSplitter(
#     chunk_size=3000,  # larger chunk
#     chunk_overlap=500
# )
