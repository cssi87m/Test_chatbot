import json
import os
from openai import OpenAI
import time
import logging 
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI")

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key = api_key,
)

keys = ["intent", "query", "use_rag", "need_subquery", "reference_text", "retrieve_level", "tinh_trang_hieu_luc", "loai_van_ban", "so_hieu", "ten_van_ban", "use_memory", 
                     "query_external_search", "ngay_ban_hanh_start", "ngay_ban_hanh_end", "ngay_co_hieu_luc_start", "ngay_co_hieu_luc_end"]

DELAY = 3

#keys = ["query", "retrieve_level", "term_position", "so_hieu",
#                                 "ten_van_ban", "loai_van_ban", "tinh_trang_hieu_luc",
#                                 "thoi_gian_ban_hanh", "ngay_ban_hanh_start", "ngay_ban_hanh_end"]

#keys = ["comparison_type", "object_1", "object_2"]

# Setup logging 
logging.basicConfig(
    level=logging.INFO,
    filename = "/home/team_nlp/quangminh/test_fc/test_fc/temp/eval_fc.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
def compare_queries(query1, query2):
    prompt = f"""
                Bạn là một trợ lý AI. So sánh hai truy vấn sau và đánh giá mức độ giống nhau về ý nghĩa nội dung, đưa ra câu trả lời xem hai query có tương đương nhau không:
                Query 1: "{query1}"
                Query 2: "{query2}"

                Chỉ trả về True/False, không giải thích gì thêm.
        """
    response = client.chat.completions.create(
        model="gemini-2.5-flash-lite",
        messages=[
            {"role": "system", "content": "Bạn là một chuyên gia xử lý ngôn ngữ tự nhiên."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    # Add delay to avoid rate limiting
    time.sleep(DELAY)
    return response.choices[0].message.content.strip()
    # return "true"

def normalize_data(data: list[str]) -> str:
    """
    Normalize list of strings by stripping whitespace, converting to lowercase, and join all.
    """
    if not data or data is None:
        return ""
    return " ".join(sorted([item.strip() for item in data]))

def compare_data(question: str, data1: dict, data2: dict):
    result = {} 
    
    for key in keys:
        result[key] = 0
    
    for key in keys: 
        if key == "query":
            # Use a different function to compare query
            if compare_queries(data1.get(key), data2.get(key)):
                result[key] += 1
                
        # Use accuracy for other fields 
        if data1.get(key) == data2.get(key) and key != "query":
            result[key] += 1
        
        if key in ["loai_van_ban", "so_hieu", "ten_van_ban"]:
            val1 = data1.get(key)
            val2 = data2.get(key)
            
            val1 = normalize_data(val1) if isinstance(val1, list) else val1
            val2 = normalize_data(val2) if isinstance(val2, list) else val2

            if val1 != val2:
                print(f"Difference found in question: {question}")
                print(f"Field: {key}, GPT-4.1: {val1}, CMC-FC: {val2}")
        
    # # Get comparison objects
    # comp1 = data1["query_params"].get("comparison_objects", {})
    # comp2 = data2["query_params"].get("comparison_objects", {})
    # if comp1 and comp2:
    #     for key in keys:
    #         val1 = comp1.get(key)
    #         val2 = comp2.get(key)
            
    #         if isinstance(val1, dict) and isinstance(val2, dict):
    #             res = 1
    #             # Duyệt các key trong dict, chỉ so sánh query
    #             for sub_key in val1:
    #                 if sub_key == "query" and sub_key in val2:
    #                     if not compare_queries(val1[sub_key], val2[sub_key]):
    #                         res = 0
    #                 elif val1[sub_key] != val2[sub_key]:
    #                     res = 0
    #             if res == 1:
    #                 result[key] += 1
    #         else:
    #             if val1 == val2:
    #                 result[key] += 1
    
    # # Get subqueries
    # subquery1 = data1["query_params"].get("sub_queries", {})
    # subquery2 = data2["query_params"].get("sub_queries", {})
    # if subquery1 and subquery2:
    #     for key in keys:
    #         val1 = subquery1.get(key)
    #         val2 = subquery2.get(key)
            
    #         if isinstance(val1, dict) and isinstance(val2, dict):
    #             res = 1
    #             # Duyệt các key trong dict, chỉ so sánh query
    #             for sub_key in val1:
    #                 if sub_key == "query" and sub_key in val2:
    #                     if not compare_queries(val1[sub_key], val2[sub_key]):
    #                         res = 0
    #                 elif val1[sub_key] != val2[sub_key]:
    #                     res = 0
    #             if res == 1:
    #                 result[key] += 1
    #         else:
    #             if val1 == val2:
    #                 result[key] += 1
    return question, result


                
# diff_list = [x for x in list(diff_map.values()) if x['fields'] != {}]
# with open("./test_fc/temp/diff.json", "w", encoding = "utf-8") as f:
#     json.dump(diff_list, f, ensure_ascii=False, indent=2)                        
                            
# for key in keys:
#     results[key] /= total_count
# with open("./test_fc/temp/extract_intent_and_query.json", "w", encoding = "utf-8") as f:
#     json.dump(results, f, ensure_ascii=False, indent=2)

# print(results)

if __name__ == "__main__":
    data_path = "test_fc/data_test_fc/results.jsonl"
    with open(data_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f.readlines()]
    results = {}
    for key in keys:
        results[key] = 0
    for line in lines:
        question = line.get("query", "")
        ground_truth = line.get("gpt_payload", {})
        prediction = line.get("fc_payload", {})
        
        question, result = compare_data(question, ground_truth, prediction)
        print(f"Question: {question}")
        print("Comparison Results:")
        print(result)
        logging.info(f"Question: {question}")
        logging.info(f"Comparison Results: {result}")
        
        for key in keys: 
            results[key] += result.get(key, 0) 
        
    
    # Print summary 
    total_count = len(lines)
    print("Summary Results:")
    for key in keys:
        results[key] /= total_count
        print(f"Accuracy {key}: {results[key]:.4f}")