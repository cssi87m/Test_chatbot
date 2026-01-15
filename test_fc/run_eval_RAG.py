import json
from tqdm import tqdm
import re
import unicodedata
import logging
from typing import Dict, List, Any
from fuzzywuzzy import fuzz
from datetime import datetime
import os

# ===CONFIG===
USE_FUNCTION_CALLING = "with_fc"  # "with_fc" or "without_fc"
GT_PATH = f"Data/du_lieu_output/api_dev/retrieved_results_{USE_FUNCTION_CALLING}.json"
REPORT_PATH = r"Data/results/rag/dev_report.json"
# ERORR_PATH_DOC = r"Data/error_question/rag/skipped_items_doc.json"
# ERORR_PATH_TERM = r"Data/error_question/rag/skipped_items_term.json"
# NO_MATCH_PATH_DOC = r"Data/error_question/rag/no_match_item_doc.json"
# NO_MATCH_PATH_TERM = r"Data/error_question/rag/no_match_item_term.json"

def normalize_text(text: str) -> str:
    """Chuẩn hóa văn bản: thường hóa, xóa dấu, bỏ khoảng trắng dư."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text

def evaluate_doc_level(results_data, note: str) -> Dict[str, Any]:
    data = results_data.copy()

    total_mrr = 0.0
    total_hit_5 = 0
    total_hit_10 = 0
    total_hit_20 = 0
    total_found = 0
    precision_list = []
    recall_list = []
    skipped_items = []
    no_match_item = []

    for entry in tqdm(data, desc="Đang xử lý đánh giá văn bản"):
        gt_docs = entry.get("trich_dan", [])
        retrieved = entry.get("retrieved", [])

        if not retrieved or not gt_docs:
            skipped_items.append(entry)
            continue

        # Lấy danh sách văn bản đúng từ GT
        gt_doc_terms = set()
        for trich_dan in gt_docs:
            if not isinstance(trich_dan, dict):
                continue

            loai = normalize_text(trich_dan.get("loai_vb", ""))
            so_hieu = normalize_text(trich_dan.get("so_hieu", ""))
            trich_yeu = normalize_text(trich_dan.get("trich_yeu", ""))

            # Tạo key cho văn bản
            if loai and so_hieu:
                gt_doc_terms.add((loai, so_hieu, True))
            else:
                gt_doc_terms.add((loai, trich_yeu))

        if not gt_doc_terms:  
            continue

        # So sánh
        ranks = []
        checked = set()
        for rank, doc in enumerate(retrieved):
            loai_doc = normalize_text(doc.get("loai_van_ban", ""))
            so_hieu_doc = normalize_text(doc.get("so_hieu", ""))
            trich_yeu_doc = normalize_text(f"{loai_doc} {doc.get('title', '')}")

            # Kiểm tra từng văn bản trong GT
            for gt_doc_key in gt_doc_terms:
                doc_matched = False
                if len(gt_doc_key) == 3:  # so sánh theo (loai, so_hieu)
                    if (loai_doc, so_hieu_doc, True) == gt_doc_key:
                        doc_matched = True
                elif gt_doc_key[0] == loai_doc:  # so sánh trích yếu
                    score = fuzz.token_set_ratio(gt_doc_key, trich_yeu_doc)
                    if score >= 90:
                        doc_matched = True

                # Nếu văn bản match
                if doc_matched and gt_doc_key not in checked:
                    ranks.append(rank)
                    checked.add(gt_doc_key)
                    break
        if not ranks:
            no_match_item.append(entry)
        else:
            total_mrr += 1.0 / (ranks[0] + 1)
            total_found += 1

        total_hit_5 += 1 if any(x < 5 for x in ranks) else 0
        total_hit_10 += 1 if any(x < 10 for x in ranks) else 0
        total_hit_20 += 1 if any(x < 20 for x in ranks) else 0
        precision = len(ranks) / len(retrieved)
        recall = len(ranks) / len(gt_doc_terms)
        precision_list.append(precision)
        recall_list.append(recall)

    mrr = total_mrr / len(data) if len(data) else 0
    hr5 = total_hit_5 / len(data) if len(data) else 0
    hr10 = total_hit_10 / len(data) if len(data) else 0
    hr20 = total_hit_20 / len(data) if len(data) else 0
    found_ratio = total_found / len(data) if len(data) else 0


    # if os.path.dirname(ERORR_PATH_DOC):
    #     os.makedirs(os.path.dirname(ERORR_PATH_DOC), exist_ok=True)
    # with open(ERORR_PATH_DOC, "w", encoding="utf-8") as f:
    #     json.dump(skipped_items, f, ensure_ascii=False, indent=4)

    # if os.path.dirname(NO_MATCH_PATH_DOC):
    #     os.makedirs(os.path.dirname(NO_MATCH_PATH_DOC), exist_ok=True)
    # with open(NO_MATCH_PATH_DOC, "w", encoding="utf-8") as f:
    #     json.dump(no_match_item, f, ensure_ascii=False, indent=4)

    return {
        "Note": note,
        "Tổng câu hỏi": len(data),
        "Tổng câu có kết quả truy vấn": len(
            [item for item in data if item.get("retrieved", [])]
        ),
        "Found": total_found,
        "Found_ratio": round(found_ratio, 4),
        "MRR": round(mrr, 4),
        "HR@5": round(hr5, 4),
        "HR@10": round(hr10, 4),
        "HR@20": round(hr20, 4),
        "Precision": round(sum(precision_list) / len(data), 4),
        "Recall": round(sum(recall_list) / len(data), 4),
    }

def evaluate_term_level(results_data, note: str) -> Dict[str, Any]:
    data = results_data.copy()

    total_mrr = 0.0
    total_hit_5 = 0
    total_hit_10 = 0
    total_hit_20 = 0
    total_found = 0
    precision_list = []
    recall_list = []
    skipped_items = []
    no_match_item = []
    count = 0
    match_temp = []

    for entry in tqdm(data, desc="Đang xử lý đánh giá điều"):
        gt_docs = entry.get("trich_dan", [])
        retrieved = entry.get("retrieved", [])   

        # Lấy danh sách văn bản và điều đúng từ GT
        gt_doc_terms = set()  # {doc_key: set(terms)}
        for trich_dan in gt_docs:
            if not isinstance(trich_dan, dict):
                continue

            loai = normalize_text(trich_dan.get("loai_vb", ""))
            so_hieu = normalize_text(trich_dan.get("so_hieu", ""))
            trich_yeu = normalize_text(trich_dan.get("trich_yeu", ""))
            dieu = trich_dan.get("dieu", "").strip()

            if not dieu:  # Bỏ qua nếu không có thông tin điều
                continue

            # Tạo key cho văn bản
            if loai and so_hieu:
                gt_doc_terms.add(((loai, so_hieu), dieu, True))
            else:
                gt_doc_terms.add(((loai, trich_yeu), dieu, False))

        if not gt_doc_terms:
            continue
        
        if not retrieved or not gt_docs:
            skipped_items.append(entry)
            count += 1
            continue 

        # So sánh: chỉ xét điều khi văn bản đã match
        ranks = []
        checked = set()
        for rank, doc in enumerate(retrieved):
            loai_doc = normalize_text(doc.get("loai_van_ban", ""))
            so_hieu_doc = normalize_text(doc.get("so_hieu", ""))
            trich_yeu_doc = normalize_text(f"{loai_doc} {doc.get('title', '')}")
            dieu_doc = doc.get("id", "").split("_")[1] if isinstance(doc.get("id", ""), str) else doc.get("id", "")

            # Kiểm tra từng văn bản trong GT
            for gt_doc_key, gt_terms, b in gt_doc_terms:
                doc_matched = False
                if b:  # so sánh theo (loai, so_hieu)
                    if (loai_doc, so_hieu_doc) == gt_doc_key:
                        doc_matched = True
                elif gt_doc_key[0] == loai_doc:  # so sánh trích yếu
                    score = fuzz.token_set_ratio(gt_doc_key[1], trich_yeu_doc)
                    if score >= 90:
                        doc_matched = True

                # Nếu văn bản match
                if (
                    doc_matched
                    and dieu_doc == gt_terms
                    and (gt_doc_key, gt_terms, b) not in checked
                ):
                    ranks.append(rank)
                    checked.add((gt_doc_key, gt_terms, b))
                    break

        if not ranks:
            no_match_item.append(entry)
        else:
            match_temp.append(entry.get("id", ""))
            total_mrr += 1.0 / (ranks[0] + 1)
            total_found += 1

        total_hit_5 += 1 if any(x < 5 for x in ranks) else 0
        total_hit_10 += 1 if any(x < 10 for x in ranks) else 0
        total_hit_20 += 1 if any(x < 20 for x in ranks) else 0
        precision = len(ranks) / len(retrieved)
        recall = len(ranks) / len(gt_doc_terms)
        precision_list.append(precision)
        recall_list.append(recall)
        count += 1

    mrr = total_mrr / count
    hr5 = total_hit_5 / count
    hr10 = total_hit_10 / count
    hr20 = total_hit_20 / count
    found_ratio = total_found / count

    
    # with open("match_dev_api.json", "w", encoding="utf-8") as f:
    #     json.dump(match_temp, f, ensure_ascii=False, indent=4)

    # if os.path.dirname(ERORR_PATH_TERM):
    #     os.makedirs(os.path.dirname(ERORR_PATH_TERM), exist_ok=True)    
    # with open(ERORR_PATH_TERM, "w", encoding="utf-8") as f:
    #     json.dump(skipped_items, f, ensure_ascii=False, indent=4)

    # if os.path.dirname(NO_MATCH_PATH_TERM):
    #     os.makedirs(os.path.dirname(NO_MATCH_PATH_TERM), exist_ok=True)
    # with open(NO_MATCH_PATH_TERM, "w", encoding="utf-8") as f:
    #     json.dump(no_match_item, f, ensure_ascii=False, indent=4)

    return {
        "Note": note,
        "Tổng câu hỏi": len(data),
        "Tổng câu có kết quả truy vấn": len(
            [item for item in data if item.get("retrieved", [])]
        ),
        "count": count,
        "Found": total_found,
        "Found_ratio": round(found_ratio, 4),
        "MRR": round(mrr, 4),
        "HR@5": round(hr5, 4),
        "HR@10": round(hr10, 4),
        "HR@20": round(hr20, 4),
        "Precision": round(sum(precision_list) / count, 4),
        "Recall": round(sum(recall_list) / count, 4),
    }


def evaluate_existing_results(results_data, note: str = ""):
    """
    Đánh giá kết quả có sẵn ở cả hai mức độ: Document-Level và Term-Level
    """
    print(f"Đang đánh giá {len(results_data)} câu hỏi")

    # Đánh giá Document-Level
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key_doc = f"Evaluation Document-Level, time:{current_time}, questions = {len(results_data)}"
    doc_report = {key_doc: evaluate_doc_level(results_data, note)}

    # Đánh giá Term-Level
    key_term = f"Evaluation Term-Level, time:{current_time}, questions = {len(results_data)}"
    term_report = {key_term: evaluate_term_level(results_data, note)}

    # Gộp cả hai báo cáo
    report = {**doc_report, **term_report}

    if os.path.dirname(REPORT_PATH):
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
 
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}
    existing_data.update(report)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print("Đánh giá hoàn thành!")

if __name__ == "__main__":
    print(f"Dữ liệu đánh giá: {GT_PATH}")
    data = json.load(open(GT_PATH, 'r', encoding='utf-8'))
    if USE_FUNCTION_CALLING == "with_fc":
        note = "[Test] có fc"
    else:
        note = "[Test] không fc"
    evaluate_existing_results(data, note=note)