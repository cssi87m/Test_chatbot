import json
import os
from openai import OpenAI
import time

api_key = ""

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key = api_key,
)

keys = ["intent", "query", "use_rag", "need_subquery", "reference_text", "retrieve_level", "tinh_trang_hieu_luc", "loai_van_ban", "so_hieu", "ten_van_ban", "use_memory", 
                     "query_external_search", "ngay_ban_hanh_start", "ngay_ban_hanh_end", "ngay_co_hieu_luc_start", "ngay_co_hieu_luc_end"]

#keys = ["query", "retrieve_level", "term_position", "so_hieu",
#                                 "ten_van_ban", "loai_van_ban", "tinh_trang_hieu_luc",
#                                 "thoi_gian_ban_hanh", "ngay_ban_hanh_start", "ngay_ban_hanh_end"]

#keys = ["comparison_type", "object_1", "object_2"]

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
    return response.choices[0].message.content.strip()



results = {}
total_count = 0

diff_map = {} 

for key in keys:
    results[key] = 0

for filename1 in os.listdir("gpt"):
    file_path1 = os.path.join("gpt", filename1)
    with open(file_path1, "r", encoding = "utf-8") as f1:
        data1 = json.load(f1)
        messages1 = data1.get("request_params")["messages"]

        for filename2 in os.listdir("cmc_model"):
            file_path2 = os.path.join("cmc_model", filename2)
            with open(file_path2, "r", encoding = "utf-8") as f2:
                data2 = json.load(f2)
                messages2 = data2.get("request_params")["messages"]
                if messages1 == messages2:
                    #time.sleep(3)
                    total_count += 1
                    question = messages1[-1]["content"]
                    for key in keys:
                        #if key == "query":
                        #    if compare_queries(data1["query_params"].get(key), data2["query_params"].get(key)):
                        #        print(data1["query_params"].get(key), data2["query_params"].get(key))
                        #        results[key] += 1
                        #if data1["query_params"].get(key) == data2["query_params"].get(key):
                        #    results[key] += 1

                        if question not in diff_map:
                            diff_map[question] = {
                                "messages": messages1,
                                "fields": {}
                            }

                        for key in keys:
                            if key in ["loai_van_ban", "so_hieu", "ten_van_ban"]:
                                val1 = data1["query_params"].get(key)
                                val2 = data2["query_params"].get(key)

                                if val1 != val2:
                                    diff_map[question]["fields"][key] = {
                                        "gpt4.1": val1,
                                        "cmc-fc": val2
                                    }


                    """
                    comp1 = data1["query_params"].get("comparison_objects", {})
                    comp2 = data2["query_params"].get("comparison_objects", {})
                    print(comp2)
                    if comp1:
                        total_count += 1
                        if comp2:
                            for key in keys:
                                val1 = comp1.get(key)
                                val2 = comp2.get(key)
                                
                                if isinstance(val1, dict) and isinstance(val2, dict):
                                    res = 1
                                    # Duyệt các key trong dict, chỉ so sánh query
                                    for sub_key in val1:
                                        if sub_key == "query" and sub_key in val2:
                                            if not compare_queries(val1[sub_key], val2[sub_key]):
                                                res = 0
                                        elif val1[sub_key] != val2[sub_key]:
                                            res = 0
                                    if res == 1:
                                        results[key] += 1
                                else:
                                    if val1 == val2:
                                        results[key] += 1
                    
                    subquery1 = data1["query_params"].get("sub_queries", {})
                    subquery2 = data2["query_params"].get("sub_queries", {})
                    if subquery1:
                        total_count += 1
                        if subquery2:
                            for key in keys:
                                val1 = subquery1.get(key)
                                val2 = subquery2.get(key)
                                
                                if isinstance(val1, dict) and isinstance(val2, dict):
                                    res = 1
                                    # Duyệt các key trong dict, chỉ so sánh query
                                    for sub_key in val1:
                                        if sub_key == "query" and sub_key in val2:
                                            if not compare_queries(val1[sub_key], val2[sub_key]):
                                                res = 0
                                        elif val1[sub_key] != val2[sub_key]:
                                            res = 0
                                    if res == 1:
                                        results[key] += 1
                                else:
                                    if val1 == val2:
                                        results[key] += 1
                    """
                                
                            
# for key in keys:
#     results[key] /= total_count
# with open("extract_intent_and_query.json", "w", encoding = "utf-8") as f:
#     json.dump(results, f, ensure_ascii=False, indent=2)
diff_list = [x for x in list(diff_map.values()) if x['fields'] != {}]
with open("diff.json", "w", encoding = "utf-8") as f:
    json.dump(diff_list, f, ensure_ascii=False, indent=2)
#print(results)