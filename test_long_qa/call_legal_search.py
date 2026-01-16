import requests

def call_legal_search(query, api_key, limit=100):
    url = "http://10.4.0.204:6971/v2/legal_search"
    headers = {
        "Content-Type": "application/json",
    }
 
    payload = {
        "query": query,
        "limit": limit,
        "sort": "score",
        "order": "desc",
        "so_hieu": "",
        "ten_van_ban": "",
        "search_legal_term": True,
        "ngay_ban_hanh_start": "",
        "ngay_ban_hanh_end": "",
        "chu_de_phap_dien": "",
        "tinh_trang_hieu_luc": "Còn hiệu lực,Hết hiệu lực một phần",
        "co_quan_ban_hanh": "",
        "co_quan_quan_ly": "",
        "should": "",
        "must": "",
        "must_not": "",
        "statistics": False,
        "highlight": False,
        "return_for_chatbot": True,
        "dense_threshold": 0.675,
        "rerank_threshold": 0.5,
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()
        return ""