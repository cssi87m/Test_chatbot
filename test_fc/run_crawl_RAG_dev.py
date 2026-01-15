from test_fc.prompt import prompt

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from typing import List, Dict, Tuple
import requests
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from tqdm import tqdm
import shutil
import glob
from datetime import datetime

# ===CONFIG===
USE_FUNCTION_CALLING = "with_fc"  # "with_fc" or "without_fc"
SEARCH_API = "http://10.4.0.204:6971/v2/legal_search"
LIMIT = 20
GT_PATH = "Data/final/hoi_dap_phap_luat_1000_TW_v2.json"
LOAI_VB = "Hiến pháp,Bộ luật,Luật,Nghị định,Thông tư"
OUTPUT_PATH = f"Data/du_lieu_output/api_dev/retrieved_results_{USE_FUNCTION_CALLING}.json"

print(f"Đang sử dụng Function Calling: {USE_FUNCTION_CALLING}")

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
    
    return normalized

def search_cls(question: str, limit: int = 100) -> Tuple[List[Dict], str]:
    headers = {
        "Content-Type": "application/json",
    }

    # Get payload from function calling
    fc_payload = function_calling(question)
    
    # Validate and normalize the function calling result
    payload = validate_and_normalize_payload(fc_payload, question)
    
    # Add API-specific parameters
    payload["limit"] = limit
    payload["sort"] = "score"
    payload["order"] = "desc"
    payload["search_legal_term"] = True
    payload["statistics"] = False
    payload["highlight"] = False
    payload["return_for_chatbot"] = True
    
    # # Create payload for API request
    # payload = {
    #     "query": question,
    #     "limit": limit,
    #     "sort": "score",
    #     "order": "desc",
    #     "so_hieu": "",
    #     "ten_van_ban": "",
    #     "search_legal_term": True,
    #     "ngay_ban_hanh_start": "",
    #     "ngay_ban_hanh_end": "",
    #     "chu_de_phap_dien": "",
    #     "tinh_trang_hieu_luc": "Còn hiệu lực,Hết hiệu lực một phần",
    #     "loai_van_ban": "",
    #     "co_quan_ban_hanh": "",
    #     "co_quan_quan_ly": "",
    #     "should": "",
    #     "must": "",
    #     "must_not": "",
    #     "statistics": False,
    #     "highlight": False,
    #     "return_for_chatbot": True,
    # }
    
    # Log payload to file and print
    logging.info(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    tqdm.write(f"[PAYLOAD] {question[:50]}... => {json.dumps(payload, ensure_ascii=False)}")

    retry = 0

    while retry < 5:
        response = requests.get(SEARCH_API, params=payload, headers=headers)
        if not response.ok:
            raise Exception(f"Search failed: {response.text}")

        resp_json = response.json()
        # logging.info(f"API Response JSON: {json.dumps(resp_json, ensure_ascii=False, indent=2)}")
        data = resp_json.get("data", [])
        msg = resp_json.get("msg", "")  # Fix: should be empty string, not empty list
        
        # Debug: Log the first item structure to see what fields are actually returned
        # if data and len(data) > 0:
            # logging.info(f"Sample API response item keys: {list(data[0].keys())}")
            # logging.info(f"Sample API response item (first result): {json.dumps(data[0], ensure_ascii=False, indent=2)}")

        if msg != "Tìm kiếm thành công":
            retry += 1
            time.sleep(1)
            continue

        results = []
        for item in data:
            results.append(
                {
                    "index": item.get("index", ""),  # Now directly available
                    "id": item.get('id', item.get('ID', '')),  # Try lowercase first, then uppercase
                    "id_document": item.get("id_document", item.get("ID", "")),
                    "position": item.get("position", ""),  # Now directly available
                    "dia_danh": item.get("dia_danh", ""),
                    "title": item.get("title", ""),
                    "so_hieu": item.get("so_hieu", ""),
                    "trich_yeu": item.get("trich_yeu", ""),
                    "loai_van_ban": item.get("loai_van_ban", ""),
                    "tinh_trang_hieu_luc": item.get("tinh_trang_hieu_luc", ""),
                    "co_quan_ban_hanh": item.get("co_quan_ban_hanh", ""),
                    "don_vi": item.get("don_vi", []),
                    "linh_vuc": item.get("linh_vuc", ""),
                    "score": item.get("score", 0),
                }
            )
        
        logging.info(f"Tìm thấy {len(results)} kết quả cho câu hỏi: {question}")
        return results, msg
    
    return [], msg

def process_question(item, limit):
    id = item.get("id", "")
    question = item.get("cau_hoi", "")
    tra_loi = item.get("tra_loi", "")
    trich_dan = item.get("trich_dan", [])
    retry = 0
    backoff = 5  # thời gian chờ ban đầu (giây)
    msg = ''
    while retry < 8:  # tăng số lần thử lại lên 5 cho an toàn
        try:
            retrieved, msg = search_cls(question, limit)
            # Print out retrieved and msg for debugging
            logging.info(f"Câu hỏi {id}: {question} - Tìm được {len(retrieved)} kết quả. Msg: {msg}")
            logging.info(f"Kết quả truy vấn: {json.dumps(retrieved, ensure_ascii=False, indent=2)}")
            return {
                "id": id,
                "cau_hoi": question,
                "tra_loi": tra_loi,
                "trich_dan": trich_dan,
                "msg": msg,
                "retrieved": retrieved,
            }
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "Unauthorized" in err_str:
                logging.warning(
                    f"Token hết hạn hoặc không hợp lệ, đang lấy lại token cho câu hỏi {id}: {question}"
                )
                retry += 1
            elif (
                "429" in err_str
                or "Too Many Requests" in err_str
                or "503" in err_str
                or "502" in err_str   
                or "Service Unavailable" in err_str
                or "Connection refused" in err_str 
                or "Failed to establish a new connection" in err_str
            ):
                logging.warning(
                    f"[Retry {retry}] Gặp lỗi {err_str} ở câu hỏi: {question}. Đang giảm tốc, chờ {backoff} giây rồi thử lại..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # tăng dần thời gian chờ, tối đa 60s
                retry += 1
            else:
                logging.error(f"[LỖI] Lỗi ở câu hỏi {id}: {question}: {e}")
                return {
                    "id": id,
                    "cau_hoi": question,
                    "tra_loi": tra_loi,
                    "trich_dan": trich_dan,
                    "msg": msg,
                    "retrieved": [],
                }
    logging.info(f"[LỖI] Không truy vấn được ở câu hỏi {id}: {question}")
    return {
        "id": id,
        "cau_hoi": question,
        "tra_loi": tra_loi,
        "trich_dan": trich_dan,
        "msg": msg,
        "retrieved": [],
    }

def query_all_parallel_batch(
    gt_path,
    save_dir,
    batch_size=1000,
    limit=10,
    num_workers=8,
    max_questions=None,
    start_id=None,
    time_sleep=5
):
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    print(f"Đang truy vấn từ {gt_path}")

    if max_questions is not None:
        gt_data = gt_data[start_id : (start_id + max_questions)]
    else:
        gt_data = gt_data[start_id : ]

    print(f"Tổng số câu hỏi trong GT: {len(gt_data)}")

    total = len(gt_data)
    os.makedirs(save_dir, exist_ok=True)
    for i in range(0, total, batch_size):
        batch_data = gt_data[i : i + batch_size]
        batch_idx = i // batch_size + 1
        query_batch_parallel(batch_data, limit, num_workers, batch_idx, save_dir)
        print(f"Nghỉ giữa {batch_idx} batch {time_sleep} giây, đã xử lý {i + len(batch_data)}/{len(gt_data)} câu hỏi.")
        logging.info(f"Nghỉ giữa {batch_idx} batch {time_sleep} giây, đã xử lý {i + len(batch_data)}/{len(gt_data)} câu hỏi.")
        time.sleep(time_sleep)

def query_batch_parallel(batch_data, limit, num_workers, batch_idx, save_dir):
    results = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(process_question, item, limit) for item in batch_data
        ]
        for f in tqdm(
            as_completed(futures), total=len(futures), desc=f"Batch {batch_idx}"
        ):
            results.append(f.result())
    save_path = os.path.join(save_dir, f"retrieved_results_batch_{batch_idx}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

def merge_batch_results(save_dir):
    all_results = []
    for file in sorted(
        glob.glob(os.path.join(save_dir, "retrieved_results_batch_*.json"))
    ):
        with open(file, "r", encoding="utf-8") as f:
            all_results.extend(json.load(f))
    return all_results

def main_parallel():
    batch_size = 5
    num_workers = 4
    save_dir = "Data/batch_results/api_dev"

    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    print("Đang truy vấn câu hỏi")
    query_all_parallel_batch(
        gt_path=GT_PATH,
        save_dir=save_dir,
        batch_size=batch_size,
        limit=LIMIT,
        num_workers=num_workers,
        max_questions=100,
        start_id=0,
        time_sleep=10
    )

    all_results = merge_batch_results(save_dir)
    merged_path = OUTPUT_PATH
    if os.path.dirname(merged_path):
        os.makedirs(os.path.dirname(merged_path), exist_ok=True)
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # question = "Nêu các luật về xử lý vi phạm hành chính trong lĩnh vực giao thông đường bộ?"
    # args = function_calling(question)
    # print("Function calling arguments:", args)
    ngay_cap_nhat = "./thoi_diem_chay/rag/9_1_2026/dev_log"
    log_filename = os.path.join(
        ngay_cap_nhat, f"dev_legal_search_{datetime.now().strftime('%d_%m_%y_%H_%M')}.log"
    )
    os.makedirs(ngay_cap_nhat, exist_ok=True)
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )
    logging.info("==== START ====")
    logging.info(f"API: {SEARCH_API}")
    print(f"API: {SEARCH_API}")
    logging.info(f"Loai văn bản: {LOAI_VB}")
    print(f"Loai văn bản: {LOAI_VB}")
    start_time = time.time()

    main_parallel()
    end_time = time.time()
    logging.info(f"- Time: {round((end_time - start_time) / 60, 4)} m")
