from test_fc.prompt import prompt
import logging 
import os 
import json 
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
def function_calling(query: str) -> dict:
    """
    Perform function calling to extract essential terms
    """
    FC_PAYLOAD_TOOLCALL = "function_calling_toolcall.json"
    with open(FC_PAYLOAD_TOOLCALL, "r") as f:
        function_def = json.load(f)

    # Wrap the function definition in the correct format
    tools = [
        {
            "type": "function",
            "function": function_def
        }
    ]

    # Init OpenAI client
    api_key = os.getenv("API_KEY")

    client = OpenAI(
        api_key=api_key, 
        base_url=f"{os.getenv('HOST_NAME')}/v1",
    )

    response = client.chat.completions.create(
        model="CATI-AI/CMC-Legal-LLM-32B-sft-v2",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ],
        tools=tools,
        tool_choice={
            "type": "function",
            "function": {"name": "extract_intent_and_query"}
        }
    )

    # Log the raw response for debugging
    arguments_str = response.choices[0].message.tool_calls[0].function.arguments
    # logging.info(f"Raw arguments_str from LLM: '{arguments_str}'")
    
    # Handle empty or invalid JSON
    if not arguments_str or arguments_str.strip() == "":
        logging.error(f"Empty arguments returned for query: {query}")
        return {
            "query": query,
            "loai_van_ban": "",
            "chu_de_phap_dien": "",
            "tinh_trang_hieu_luc": []
        }
    
    # Flexible parsing - handle multiple formats
    original_str = arguments_str
    
    # Strip common junk prefixes/suffixes
    arguments_str = arguments_str.strip()
    
    # Format 0: Handle weird prefixes like "<>", "<name:...", "<function>", "<function-call>", etc.
    # Remove leading tags that are not valid JSON
    if arguments_str.startswith("<"):
        # Find the first occurrence of "{" which likely starts the actual JSON
        json_start = arguments_str.find("{")
        if json_start != -1:
            arguments_str = arguments_str[json_start:].strip()
    
    # Format 1: Handle "{Name}: ..., {Arguments}: {...}" or similar patterns
    if ("{Name}:" in arguments_str or "{name}:" in arguments_str) and ("{Arguments}:" in arguments_str or "{arguments}:" in arguments_str):
        # Extract everything after "{Arguments}:" or "{arguments}:"
        for pattern in ["{Arguments}:", "{arguments}:"]:
            if pattern in arguments_str:
                args_start = arguments_str.find(pattern) + len(pattern)
                arguments_str = arguments_str[args_start:].strip()
                break
    
    # Format 2: Handle "<name>: ..., <arguments>: {...}"
    elif ("<name>:" in arguments_str or "<Name>:" in arguments_str) and "<arguments>:" in arguments_str:
        args_start = arguments_str.find("<arguments>:") + len("<arguments>:")
        arguments_str = arguments_str[args_start:].strip()
    
    # Format 3: Handle XML-like tags like <arguments>...</arguments>
    elif "<arguments>" in arguments_str and "</arguments>" in arguments_str:
        start = arguments_str.find("<arguments>") + len("<arguments>")
        end = arguments_str.find("</arguments>")
        arguments_str = arguments_str[start:end].strip()
    
    # Format 4: Handle <function>...</function>
    elif "<function>" in arguments_str and "</function>" in arguments_str:
        start = arguments_str.find("<function>") + len("<function>")
        end = arguments_str.find("</function>")
        arguments_str = arguments_str[start:end].strip()
    
    # Format 5: Handle <extract_intent_and_query>...</extract_intent_and_query>
    elif "<extract_intent_and_query>" in arguments_str:
        if "</extract_intent_and_query>" in arguments_str:
            start = arguments_str.find("<extract_intent_and_query>") + len("<extract_intent_and_query>")
            end = arguments_str.find("</extract_intent_and_query>")
            arguments_str = arguments_str[start:end].strip()
        else:
            # Remove the opening tag and keep the rest
            arguments_str = arguments_str.replace("<extract_intent_and_query>", "").strip()
    
    # Format 6: Handle <name>xxx</name>\n<arguments>...</arguments>
    elif "<name>" in arguments_str and "</name>" in arguments_str:
        if "<arguments>" in arguments_str and "</arguments>" in arguments_str:
            start = arguments_str.find("<arguments>") + len("<arguments>")
            end = arguments_str.find("</arguments>")
            arguments_str = arguments_str[start:end].strip()
    
    # Format 7: If it starts with "{"name": and contains "arguments", extract just the arguments
    if arguments_str.startswith('{"name":') or arguments_str.startswith("{'name':"):
        try:
            temp_parse = json.loads(arguments_str)
            if isinstance(temp_parse, dict) and "arguments" in temp_parse:
                arguments_str = json.dumps(temp_parse["arguments"])
        except:
            pass
    
    # Format 8: If it's just plain text like "function-call", return default
    if arguments_str.strip() in ["function-call", "function_call", "<tool>", "</tool>", "<>", ""]:
        logging.error(f"Invalid response format for query '{query}': '{original_str[:200]}'")
        return {
            "query": query,
            "loai_van_ban": "",
            "chu_de_phap_dien": "",
            "tinh_trang_hieu_luc": []
        }
    
    try:
        parsed = json.loads(arguments_str)
        
        # If the JSON has an "arguments" key, use that as the actual arguments
        if isinstance(parsed, dict) and "arguments" in parsed:
            arguments = parsed["arguments"]
            # logging.info(f"Extracted nested arguments: {arguments}")
        else:
            arguments = parsed
            
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error for query '{query}': {e}. Tried: '{arguments_str[:200]}'")
        # Return default payload
        return {
            "query": query,
            "loai_van_ban": "",
            "chu_de_phap_dien": "",
            "tinh_trang_hieu_luc": []
        }
    return arguments

def validate_and_normalize_payload(fc_payload: dict, question: str) -> dict:
    """
    Validate and normalize function calling payload with safe defaults.
    Ensures all required fields exist and have correct types.
    Preserves all original fields from fc_payload.
    """
    err = False
    # Track if we're using defaults due to missing/invalid fields
    used_defaults = []
    
    # Start with a copy of the original payload to preserve all fields
    normalized = fc_payload.copy()
    
    # Ensure query field exists
    if "query" not in normalized or not normalized["query"]:
        normalized["query"] = question
    
    # Ensure safe defaults for fields that might be missing
    default_fields = {
        "loai_van_ban": "",
        "co_quan_ban_hanh": "",
        "tinh_trang_hieu_luc": "Còn hiệu lực,Hết hiệu lực một phần",
        "ten_van_ban": "",
        "ngay_ban_hanh_start": "",
        "ngay_ban_hanh_end": "",
        "ngay_co_hieu_luc_start": "",
        "ngay_co_hieu_luc_end": "",
        "should": "",
        "must": "",
        "must_not": "",
    }
    
    # Add missing fields with defaults
    for field, default_value in default_fields.items():
        if field not in normalized:
            normalized[field] = default_value
    
    # Safely normalize loai_van_ban (can be string or list)
    loai_van_ban = normalized.get("loai_van_ban", [])
    if isinstance(loai_van_ban, list):
        normalized["loai_van_ban"] = ",".join(loai_van_ban) if loai_van_ban else ""
    elif not isinstance(loai_van_ban, str):
        normalized["loai_van_ban"] = ""
    
    # Safely normalize tinh_trang_hieu_luc (can be string or list)
    tinh_trang = normalized.get("tinh_trang_hieu_luc", [])
    if tinh_trang and tinh_trang != []:
        if isinstance(tinh_trang, list):
            normalized["tinh_trang_hieu_luc"] = ",".join(tinh_trang)
        elif not isinstance(tinh_trang, str):
            normalized["tinh_trang_hieu_luc"] = "Còn hiệu lực,Hết hiệu lực một phần"
            used_defaults.append("tinh_trang_hieu_luc")
    else:
        normalized["tinh_trang_hieu_luc"] = "Còn hiệu lực,Hết hiệu lực một phần"
        if "tinh_trang_hieu_luc" not in fc_payload:
            used_defaults.append("tinh_trang_hieu_luc")
    
    # Ensure string fields are actually strings
    for field in ["ten_van_ban", "co_quan_ban_hanh", "ngay_ban_hanh_start", 
                  "ngay_ban_hanh_end", "ngay_co_hieu_luc_start", "ngay_co_hieu_luc_end",
                  "should", "must", "must_not"]:
        if field in normalized and normalized[field] is not None:
            normalized[field] = str(normalized[field])
    
    # Log if we had to use defaults
    if used_defaults:
        logging.warning(f"Function calling missing fields (using defaults): {', '.join(used_defaults)} for query: {question[:100]}")
        err = True
    
    return normalized, err

def main(): 
    # Get queries
    gpt_dir = "test_fc/data_test_fc/gpt"
    output_path = "test_fc/data_test_fc/results.jsonl"
    for log in os.listdir(gpt_dir):
        log_path = os.path.join(gpt_dir, log)
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        user_query = data["request_params"]["messages"][0]["content"]

        gpt_payload = data["query_params"]
        del gpt_payload["_metadata"]

        # Get payload from function calling
        fc_payload = function_calling(user_query)
        fc_payload, err = validate_and_normalize_payload(fc_payload, user_query)
        
        # Save results
        with open(output_path, "a", encoding="utf-8") as f_out:
            result = {
                "query": user_query,
                "gpt_payload": gpt_payload,
                "fc_payload": fc_payload,
                "fc_error": err
            }
            f_out.write(json.dumps(result, ensure_ascii=False) + "\n") 

if __name__ == "__main__": 
    main()