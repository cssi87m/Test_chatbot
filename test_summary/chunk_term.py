def _finalize_chunk(chunk):
    """Hoàn thiện chunk trước khi thêm vào danh sách."""
    return {
        'content': chunk['content'],
        'articles': chunk['articles'],
        'doc_ids': list(chunk['doc_ids']),
        'start_position': chunk['start_position'],
        'end_position': chunk['end_position'],
        'length': len(chunk['content']),
        'article_count': len(chunk['articles'])
    }

def _create_empty_chunk():
    """Tạo chunk rỗng."""
    return {
        'content': '',
        'articles': [],
        'doc_ids': set(),
        'start_position': '',
        'end_position': ''
    }

def chunk_legal_documents(articles, max_length=1000, separator="\n\n"):
    """
    Gộp các điều khoản pháp luật thành chunks với độ dài tối đa.
   
    Args:
        articles (list[dict]): Danh sách các điều khoản
        max_length (int): Độ dài tối đa của mỗi chunk
        separator (str): Ký tự phân cách giữa các điều khoản
   
    Returns:
        list[dict]: Danh sách các chunks
    """
    if not articles:
        return []
   
    chunks = []
    current_chunk = {
        'content': '',
        'articles': [],
        'doc_ids': set(),
        'start_position': '',
        'end_position': ''
    }
   
    separator_len = len(separator)
   
    for article in articles:
        # Sử dụng content nếu có, không thì dùng title
        article_text = article.get('content', '').strip() or article.get('title', '').strip()
       
        if not article_text:
            continue
           
        # Nếu điều khoản đơn lẻ đã vượt quá max_length
        if len(article_text) > max_length:
            # Lưu chunk hiện tại nếu có nội dung
            if current_chunk['content']:
                chunks.append(_finalize_chunk(current_chunk))
                current_chunk = _create_empty_chunk()
           
            # Tạo chunk riêng cho điều khoản dài
            chunks.append({
                'content': article_text,
                'articles': [article],
                'doc_ids': [article.get('doc_ids')],
                'start_position': article.get('position', ''),
                'end_position': article.get('position', ''),
                'length': len(article_text)
            })
            continue
       
        # Tính độ dài nếu thêm điều khoản này
        additional_length = len(article_text)
        if current_chunk['content']:
            additional_length += separator_len
           
        new_total_length = len(current_chunk['content']) + additional_length
       
        # Nếu vượt quá max_length, lưu chunk hiện tại và bắt đầu chunk mới
        if new_total_length > max_length and current_chunk['content']:
            chunks.append(_finalize_chunk(current_chunk))
            current_chunk = _create_empty_chunk()
       
        # Thêm điều khoản vào chunk hiện tại
        if current_chunk['content']:
            current_chunk['content'] += separator + article_text
        else:
            current_chunk['content'] = article_text
            current_chunk['start_position'] = article.get('position', '')
           
        current_chunk['articles'].append(article)
        current_chunk['doc_ids'].add(article.get('doc_ids'))
        current_chunk['end_position'] = article.get('position', '')
   
    # Lưu chunk cuối cùng nếu có nội dung
    if current_chunk['content']:
        chunks.append(_finalize_chunk(current_chunk))
   
    return chunks

# Example usage
if __name__ == "__main__":
    # Test method chunk_legal_documents
    articles = [
        {
            "index": 1,
            "id": "dieu_1",
            "id_document": 151164,
            "content": "Phạm vi điều chỉnh Nghị định này ban hành Biểu thuế xuất khẩu ưu đãi, Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam để thực hiện Hiệp định Thương mại tự do giữa Cộng hòa xã hội chủ nghĩa Việt Nam và Liên hiệp Vương quốc Anh và Bắc Ai-len (sau đây gọi tắt là Hiệp định UKVFTA) giai đoạn 2021 - 2022 và điều kiện được hưởng thuế suất thuế xuất khẩu ưu đãi, thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA.",
            "raw_content": "Điều 1. Phạm vi điều chỉnh\nNghị định này ban hành Biểu thuế xuất khẩu ưu đãi, Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam để thực hiện Hiệp định Thương mại tự do giữa Cộng hòa xã hội chủ nghĩa Việt Nam và Liên hiệp Vương quốc Anh và Bắc Ai-len (sau đây gọi tắt là Hiệp định UKVFTA) giai đoạn 2021 - 2022 và điều kiện được hưởng thuế suất thuế xuất khẩu ưu đãi, thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA.",
            "position": "Điều 1"
        },
        {
            "index": 2,
            "id": "dieu_2",
            "id_document": 151164,
            "content": "Đối tượng áp dụng\nNgười nộp thuế theo quy định của Luật Thuế xuất khẩu, thuế nhập khẩu. Cơ quan hải quan, công chức hải quan. Tổ chức, cá nhân có quyền và nghĩa vụ liên quan đến hàng hóa xuất khẩu, nhập khẩu.",
            "raw_content": "Điều 2. Đối tượng áp dụng\n1. Người nộp thuế theo quy định của Luật Thuế xuất khẩu, thuế nhập khẩu.\n2. Cơ quan hải quan, công chức hải quan.\n3. Tổ chức, cá nhân có quyền và nghĩa vụ liên quan đến hàng hóa xuất khẩu, nhập khẩu.",
            "position": "Điều 2"
        },
        {
            "index": 6,
            "id": "dieu_3",
            "id_document": 151164,
            "content": "Biểu thuế xuất khẩu ưu đãi, Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam giai đoạn 2021 - 2022\nBan hành kèm theo Nghị định này: Phụ lục I - Biểu thuế xuất khẩu ưu đãi của Việt Nam để thực hiện Hiệp định UKVFTA: gồm mã hàng, mô tả hàng hóa, thuế suất thuế xuất khẩu ưu đãi theo các giai đoạn khi xuất khẩu sang Liên hiệp Vương quốc Anh và Bắc Ai-len đối với từng mã hàng; Phụ lục II - Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam để thực hiện Hiệp định UKVFTA: gồm mã hàng, mô tả hàng hóa, mức thuế suất thuế nhập khẩu ưu đãi đặc biệt theo các giai đoạn được nhập khẩu vào Việt Nam từ các vùng lãnh thổ theo quy định tại điểm b khoản 3 Điều 5 Nghị định này đối với từng mã hàng.  Cột “Mã hàng” và cột “Mô tả hàng hóa” tại các Phụ lục ban hành kèm theo Nghị định này được xây dựng trên cơ sở Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam và chi tiết theo cấp mã 8 số hoặc 10 số. Trường hợp Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam được sửa đổi, bổ sung, người khai hải quan kê khai mô tả, mã hàng hóa theo Danh mục hàng hóa xuất khẩu, nhập khẩu sửa đổi, bổ sung và áp dụng thuế suất của mã hàng hoá được sửa đổi, bổ sung quy định tại các Phụ lục ban hành kèm theo Nghị định này. Phân loại hàng hóa thực hiện theo quy định của pháp luật Việt Nam. Cột “Thuế suất (%)” tại Phụ lục I và Phụ lục II: Thuế suất áp dụng cho các giai đoạn khác nhau, bao gồm: Cột “2021”: Thuế suất áp dụng từ ngày 01 tháng 01 năm 2021 đến hết ngày 31 tháng 12 năm 2021; Cột “2022”: Thuế suất áp dụng từ ngày 01 tháng 01 năm 2022 đến hết ngày 31 tháng 12 năm 2022.",
            "raw_content": "Điều 3. Biểu thuế xuất khẩu ưu đãi, Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam giai đoạn 2021 - 2022\n1. Ban hành kèm theo Nghị định này:\na) Phụ lục I - Biểu thuế xuất khẩu ưu đãi của Việt Nam để thực hiện Hiệp định UKVFTA: gồm mã hàng, mô tả hàng hóa, thuế suất thuế xuất khẩu ưu đãi theo các giai đoạn khi xuất khẩu sang Liên hiệp Vương quốc Anh và Bắc Ai-len đối với từng mã hàng;\nb) Phụ lục II - Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam để thực hiện Hiệp định UKVFTA: gồm mã hàng, mô tả hàng hóa, mức thuế suất thuế nhập khẩu ưu đãi đặc biệt theo các giai đoạn được nhập khẩu vào Việt Nam từ các vùng lãnh thổ theo quy định tại điểm b khoản 3 Điều 5 Nghị định này đối với từng mã hàng.\n\n2. Cột “Mã hàng” và cột “Mô tả hàng hóa” tại các Phụ lục ban hành kèm theo Nghị định này được xây dựng trên cơ sở Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam và chi tiết theo cấp mã 8 số hoặc 10 số.\nTrường hợp Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam được sửa đổi, bổ sung, người khai hải quan kê khai mô tả, mã hàng hóa theo Danh mục hàng hóa xuất khẩu, nhập khẩu sửa đổi, bổ sung và áp dụng thuế suất của mã hàng hoá được sửa đổi, bổ sung quy định tại các Phụ lục ban hành kèm theo Nghị định này.\nPhân loại hàng hóa thực hiện theo quy định của pháp luật Việt Nam.\n3. Cột “Thuế suất (%)” tại Phụ lục I và Phụ lục II: Thuế suất áp dụng cho các giai đoạn khác nhau, bao gồm:\na) Cột “2021”: Thuế suất áp dụng từ ngày 01 tháng 01 năm 2021 đến hết ngày 31 tháng 12 năm 2021;\nb) Cột “2022”: Thuế suất áp dụng từ ngày 01 tháng 01 năm 2022 đến hết ngày 31 tháng 12 năm 2022.",
            "position": "Điều 3"
        },
        {
            "index": 14,
            "id": "dieu_4",
            "id_document": 151164,
            "content": "Biểu thuế xuất khẩu ưu đãi của Việt Nam\nCác mặt hàng không thuộc Biểu thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này nhưng thuộc Biểu thuế xuất khẩu theo Danh mục nhóm hàng chịu thuế quy định tại Nghị định số 57/2020/NĐ-CP ngày 25 tháng 5 năm 2020 của Chính phủ sửa đổi, bổ sung một số điều của Nghị định số 122/2016/NĐ-CP ngày 01 tháng 9 năm 2016 của Chính phủ về Biểu thuế xuất khẩu, Biểu thuế nhập khẩu ưu đãi, Danh mục hàng hóa và mức thuế tuyệt đối, thuế hỗn hợp, thuế nhập khẩu ngoài hạn ngạch thuế quan và Nghị định số 125/2017/NĐ-CP ngày 16 tháng 11 năm 2017 sửa đổi, bổ sung một số điều của Nghị định số 122/2016/NĐ-CP (sau đây gọi tắt là Nghị định số 57/2020/NĐ-CP của Chính phủ) và các văn bản sửa đổi, bổ sung (nếu có) được áp dụng mức thuế suất 0% khi xuất khẩu sang Liên hiệp Vương quốc Anh và Bắc Ai-len. Điều kiện áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA Hàng hóa xuất khẩu từ Việt Nam được áp dụng thuế suất thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này và tại khoản 1 Điều này phải đáp ứng đủ các điều kiện sau: Được nhập khẩu vào Liên hiệp Vương quốc Anh và Bắc Ai-len. Có chứng từ vận tải (bản sao) thể hiện đích đến là Liên hiệp Vương quốc Anh và Bắc Ai-len. Có tờ khai hải quan nhập khẩu của lô hàng xuất khẩu có xuất xứ Việt Nam nhập khẩu vào Liên hiệp Vương quốc Anh và Bắc Ai-len (bản sao và bản dịch tiếng Anh hoặc tiếng Việt trong trường hợp ngôn ngữ sử dụng trên tờ khai không phải là tiếng Anh).  Thủ tục áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA Tại thời điểm làm thủ tục hải quan, người khai hải quan thực hiện khai tờ khai xuất khẩu, áp dụng thuế suất thuế xuất khẩu, tính thuế và nộp thuế theo Biểu thuế xuất khẩu theo Danh mục mặt hàng chịu thuế tại Nghị định số 57/2020/NĐ-CP của Chính phủ và các văn bản sửa đổi, bổ sung (nếu có); Trong thời hạn 01 năm kể từ ngày đăng ký tờ khai xuất khẩu, người khai hải quan nộp đầy đủ chứng từ chứng minh hàng hóa đáp ứng quy định tại điểm b và điểm c khoản 2 Điều này (01 bản sao) và thực hiện khai bổ sung để áp dụng mức thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA. Quá thời hạn 01 năm nêu trên, hàng hóa xuất khẩu không được áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA; Cơ quan hải quan thực hiện kiểm tra hồ sơ, kiểm tra mức thuế suất thuế xuất khẩu ưu đãi theo Biểu thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này, nếu hàng hóa xuất khẩu đáp ứng đủ các điều kiện quy định tại khoản 2 Điều này thì áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA và thực hiện xử lý tiền thuế nộp thừa cho người khai hải quan theo quy định của pháp luật về quản lý thuế.",
            "raw_content": "Điều 4. Biểu thuế xuất khẩu ưu đãi của Việt Nam\n1. Các mặt hàng không thuộc Biểu thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này nhưng thuộc Biểu thuế xuất khẩu theo Danh mục nhóm hàng chịu thuế quy định tại Nghị định số 57/2020/NĐ-CP ngày 25 tháng 5 năm 2020 của Chính phủ sửa đổi, bổ sung một số điều của Nghị định số 122/2016/NĐ-CP ngày 01 tháng 9 năm 2016 của Chính phủ về Biểu thuế xuất khẩu, Biểu thuế nhập khẩu ưu đãi, Danh mục hàng hóa và mức thuế tuyệt đối, thuế hỗn hợp, thuế nhập khẩu ngoài hạn ngạch thuế quan và Nghị định số 125/2017/NĐ-CP ngày 16 tháng 11 năm 2017 sửa đổi, bổ sung một số điều của Nghị định số 122/2016/NĐ-CP (sau đây gọi tắt là Nghị định số 57/2020/NĐ-CP của Chính phủ) và các văn bản sửa đổi, bổ sung (nếu có) được áp dụng mức thuế suất 0% khi xuất khẩu sang Liên hiệp Vương quốc Anh và Bắc Ai-len.\n2. Điều kiện áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA\nHàng hóa xuất khẩu từ Việt Nam được áp dụng thuế suất thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này và tại khoản 1 Điều này phải đáp ứng đủ các điều kiện sau:\na) Được nhập khẩu vào Liên hiệp Vương quốc Anh và Bắc Ai-len.\nb) Có chứng từ vận tải (bản sao) thể hiện đích đến là Liên hiệp Vương quốc Anh và Bắc Ai-len.\nc) Có tờ khai hải quan nhập khẩu của lô hàng xuất khẩu có xuất xứ Việt Nam nhập khẩu vào Liên hiệp Vương quốc Anh và Bắc Ai-len (bản sao và bản dịch tiếng Anh hoặc tiếng Việt trong trường hợp ngôn ngữ sử dụng trên tờ khai không phải là tiếng Anh).\n\n3. Thủ tục áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA\na) Tại thời điểm làm thủ tục hải quan, người khai hải quan thực hiện khai tờ khai xuất khẩu, áp dụng thuế suất thuế xuất khẩu, tính thuế và nộp thuế theo Biểu thuế xuất khẩu theo Danh mục mặt hàng chịu thuế tại Nghị định số 57/2020/NĐ-CP của Chính phủ và các văn bản sửa đổi, bổ sung (nếu có);\nb) Trong thời hạn 01 năm kể từ ngày đăng ký tờ khai xuất khẩu, người khai hải quan nộp đầy đủ chứng từ chứng minh hàng hóa đáp ứng quy định tại điểm b và điểm c khoản 2 Điều này (01 bản sao) và thực hiện khai bổ sung để áp dụng mức thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA. Quá thời hạn 01 năm nêu trên, hàng hóa xuất khẩu không được áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA;\nc) Cơ quan hải quan thực hiện kiểm tra hồ sơ, kiểm tra mức thuế suất thuế xuất khẩu ưu đãi theo Biểu thuế xuất khẩu ưu đãi quy định tại Phụ lục I ban hành kèm theo Nghị định này, nếu hàng hóa xuất khẩu đáp ứng đủ các điều kiện quy định tại khoản 2 Điều này thì áp dụng thuế suất thuế xuất khẩu ưu đãi theo Hiệp định UKVFTA và thực hiện xử lý tiền thuế nộp thừa cho người khai hải quan theo quy định của pháp luật về quản lý thuế.",
            "position": "Điều 4"
        },
        {
            "index": 24,
            "id": "dieu_5",
            "id_document": 151164,
            "content": "Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam\nKý hiệu “*”: Hàng hóa nhập khẩu không được hưởng thuế nhập khẩu ưu đãi đặc biệt của Hiệp định UKVFTA. Đối với hàng hóa nhập khẩu áp dụng hạn ngạch thuế quan gồm một số mặt hàng thuộc các nhóm hàng 04.07; 17.01; 24.01; 25.01, thuế nhập khẩu ưu đãi đặc biệt trong hạn ngạch là mức thuế suất quy định tại Phụ lục II ban hành kèm theo Nghị định này; danh mục và lượng hạn ngạch thuế quan nhập khẩu hàng năm theo quy định của Bộ Công Thương và mức thuế suất thuế nhập khẩu ngoài hạn ngạch áp dụng theo quy định tại Nghị định số 57/2020/NĐ-CP của Chính phủ và các văn bản sửa đổi, bổ sung (nếu có) tại thời điểm nhập khẩu. Điều kiện áp dụng thuế suất thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA Hàng hóa nhập khẩu được áp dụng mức thuế suất thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA phải đáp ứng đủ các điều kiện sau: Thuộc Biểu thuế nhập khẩu ưu đãi đặc biệt quy định tại Phụ lục II ban hành kèm theo Nghị định này. Được nhập khẩu vào Việt Nam từ: - Liên hiệp Vương quốc Anh và Bắc Ai-len; - Cộng hoà xã hội chủ nghĩa Việt Nam (Hàng hoá nhập khẩu từ khu phi thuế quan vào thị trường trong nước). Đáp ứng các quy định về xuất xứ hàng hóa và có chứng từ chứng nhận xuất xứ hàng hoá theo quy định của Hiệp định UKVFTA.",
            "raw_content": "Điều 5. Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam\n1. Ký hiệu “*”: Hàng hóa nhập khẩu không được hưởng thuế nhập khẩu ưu đãi đặc biệt của Hiệp định UKVFTA.\n2. Đối với hàng hóa nhập khẩu áp dụng hạn ngạch thuế quan gồm một số mặt hàng thuộc các nhóm hàng 04.07; 17.01; 24.01; 25.01, thuế nhập khẩu ưu đãi đặc biệt trong hạn ngạch là mức thuế suất quy định tại Phụ lục II ban hành kèm theo Nghị định này; danh mục và lượng hạn ngạch thuế quan nhập khẩu hàng năm theo quy định của Bộ Công Thương và mức thuế suất thuế nhập khẩu ngoài hạn ngạch áp dụng theo quy định tại Nghị định số 57/2020/NĐ-CP của Chính phủ và các văn bản sửa đổi, bổ sung (nếu có) tại thời điểm nhập khẩu.\n3. Điều kiện áp dụng thuế suất thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA\nHàng hóa nhập khẩu được áp dụng mức thuế suất thuế nhập khẩu ưu đãi đặc biệt theo Hiệp định UKVFTA phải đáp ứng đủ các điều kiện sau:\na) Thuộc Biểu thuế nhập khẩu ưu đãi đặc biệt quy định tại Phụ lục II ban hành kèm theo Nghị định này.\nb) Được nhập khẩu vào Việt Nam từ:\n- Liên hiệp Vương quốc Anh và Bắc Ai-len;\n- Cộng hoà xã hội chủ nghĩa Việt Nam (Hàng hoá nhập khẩu từ khu phi thuế quan vào thị trường trong nước).\nc) Đáp ứng các quy định về xuất xứ hàng hóa và có chứng từ chứng nhận xuất xứ hàng hoá theo quy định của Hiệp định UKVFTA.",
            "position": "Điều 5"
        },
        {
            "index": 31,
            "id": "dieu_6",
            "id_document": 151164,
            "content": "Hiệu lực thi hành\nNghị định này có hiệu lực kể từ ngày ký ban hành. Đối với các tờ khai hải quan của các mặt hàng xuất khẩu, nhập khẩu đăng ký từ ngày 01 tháng 01 năm 2021 đến trước ngày Nghị định này có hiệu lực thi hành, nếu đáp ứng đủ các quy định để được hưởng thuế suất thuế xuất khẩu ưu đãi, thuế nhập khẩu ưu đãi đặc biệt của Việt Nam tại Nghị định này và đã nộp thuế theo mức thuế cao hơn thì được cơ quan hải quan xử lý tiền thuế nộp thừa theo quy định của pháp luật về quản lý thuế.",
            "raw_content": "Điều 6. Hiệu lực thi hành\n1. Nghị định này có hiệu lực kể từ ngày ký ban hành.\n2. Đối với các tờ khai hải quan của các mặt hàng xuất khẩu, nhập khẩu đăng ký từ ngày 01 tháng 01 năm 2021 đến trước ngày Nghị định này có hiệu lực thi hành, nếu đáp ứng đủ các quy định để được hưởng thuế suất thuế xuất khẩu ưu đãi, thuế nhập khẩu ưu đãi đặc biệt của Việt Nam tại Nghị định này và đã nộp thuế theo mức thuế cao hơn thì được cơ quan hải quan xử lý tiền thuế nộp thừa theo quy định của pháp luật về quản lý thuế.",
            "position": "Điều 6"
        },
        {
            "index": 34,
            "id": "dieu_7",
            "id_document": 151164,
            "content": "Trách nhiệm thi hành Các Bộ trưởng, Thủ trưởng cơ quan ngang bộ, Thủ trưởng cơ quan thuộc Chính phủ, Chủ tịch Ủy ban nhân dân các tỉnh, thành phố trực thuộc trung ương và các tổ chức, cá nhân có liên quan chịu trách nhiệm thi hành Nghị định này.",
            "raw_content": "Điều 7. Trách nhiệm thi hành\nCác Bộ trưởng, Thủ trưởng cơ quan ngang bộ, Thủ trưởng cơ quan thuộc Chính phủ, Chủ tịch Ủy ban nhân dân các tỉnh, thành phố trực thuộc trung ương và các tổ chức, cá nhân có liên quan chịu trách nhiệm thi hành Nghị định này.",
            "position": "Điều 7"
        }
    ]

    chunks = chunk_legal_documents(articles, max_length=500)
    for chunk in chunks:
        print(chunk)
        print("-----")