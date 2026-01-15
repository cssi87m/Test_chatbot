from prompt import (
    SYSTEM_PROMPT,
    SUMMARIZE_DOCUMENT_USER_PROMPT_TEMPLATE,
    SUMMARIZE_TERM_USER_PROMPT_TEMPLATE
)

import os 
from openai import OpenAI
from datetime import datetime
import json
import argparse
from dotenv import load_dotenv
load_dotenv()

def get_summary(terms: list) -> str: 
    """
    Method to get summary of list of terms using OpenAI API
    Args:
        terms (list): List of terms to summarize
    Returns:
        str: Summary of the terms
    """
    # Init OpenAI client
    api_key = os.getenv("API_KEY")

    client = OpenAI(
        api_key=api_key, 
        base_url=f"{os.getenv('HOST_NAME')}/v1",
    )
    
    # Test summarize the whole docs first 
    response = client.chat.completions.create(
        model="CATI-AI/CMC-Legal-LLM-32B-sft-v2",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": SUMMARIZE_DOCUMENT_USER_PROMPT_TEMPLATE.format(
                    content=terms[0]['content']
                )
            }
        ])
    return terms[0]['content'], response.choices[0].message.content

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--markdown", action="store_true", help="Save summary in markdown format")
    args = argparser.parse_args()
    terms = [
        {
            "content": """
            (PLVN) - Thông tư mới của Bộ Công an có hiệu lực thi hành từ ngày 6/1/2026 với nhiều nội dung mới, nổi bật nhằm hoàn thiện quy định tuyển sinh, đặc biệt ở trình độ sau đại học.
Thứ Năm 15/01/2026 14:20 (GMT+7)
Bộ Công an mới ban hành ​​Thông tư số 99/2025/TT-BCA sửa đổi, bổ sung một số điều của Thông tư số 50/2021/TT-BCA ngày 11/5/2021 của Bộ trưởng Bộ Công an quy định về tuyển sinh trong Công an nhân dân.

Mở rộng và làm rõ đối tượng dự tuyển đào tạo tiến sĩ

Tại Điều 1 Thông tư đã sửa đổi, bổ sung quy định về đối tượng dự tuyển trình độ tiến sĩ trong Công an nhân dân, cụ thể:

Cán bộ quản lý giáo dục, giảng viên, giáo viên, nghiên cứu viên của các trường Công an nhân dân;

Lãnh đạo cấp phòng và tương đương trở lên, hoặc cán bộ trong quy hoạch lãnh đạo cấp phòng và tương đương trở lên thuộc công an đơn vị, địa phương;

Cán bộ có chức danh cao cấp hoặc tương đương theo quy định của Bộ Công an.

Quy định cụ thể các điều kiện dự tuyển trình độ tiến sĩ

Bên cạnh quy định mở rộng đối tượng, Thông tư này còn quy định chi tiết các điều kiện để người dự tuyển được tham gia xét tuyển đào tạo trình độ tiến sĩ trong Công an nhân dân.

Thứ nhất, tính đến năm dự tuyển không quá 50 tuổi;

Thứ hai, có thời gian công tác thực tế từ 24 tháng trở lên (không tính thời gian học chương trình đào tạo các trình độ trong Công an nhân dân, thời gian tạm tuyển, thời gian tham gia nghĩa vụ Công an nhân dân);

Thứ ba, có bằng thạc sĩ hoặc có bằng tốt nghiệp đại học loại giỏi trở lên thuộc ngành phù hợp với ngành đào tạo trình độ tiến sĩ;

Thứ tư, loại cán bộ đạt mức “Hoàn thành tốt nhiệm vụ” trở lên trong năm liền trước với năm dự tuyển.

Quy định mới về đối tượng, điều kiện dự tuyển đào tạo trình độ thạc sĩ

Thông tư sửa đổi, bổ sung đối tượng dự tuyển đào tạo trình độ thạc sĩ, gồm:

Cán bộ quản lý giáo dục, giảng viên, giáo viên trường Công an nhân dân; 

Chỉ huy cấp đội và tương đương trở lên hoặc cán bộ quy hoạch lãnh đạo, chỉ huy từ cấp đội và tương đương trở lên thuộc Công an các đơn vị, địa phương; 

Cán bộ có chức danh từ chuyên viên, nghiên cứu viên trở lên;

Cán bộ tình báo đã được bổ nhiệm chức danh Tình báo viên sơ cấp trở lên; 

Cán bộ của Bộ Quốc phòng có ngạch chức danh từ trợ lý hoặc tương đương trở lên; 

Cán bộ có chức danh khác theo quy định tại Thông tư số 78/2021 của Bộ trưởng Bộ Công an quy định tiêu chuẩn chức danh của sĩ quan, hạ sĩ quan Công an nhân dân từ trung cấp hoặc tương đương trở lên.

Điều kiện dự tuyển đào tạo trình độ thạc sĩ quy định người dự tuyển ngoài bảo đảm các điều kiện theo quy định của pháp luật và của Bộ Giáo dục và Đào tạo phải đáp ứng các điều kiện sau:

Tính đến năm dự tuyển không quá 45 tuổi;

Có bằng tốt nghiệp đại học thuộc ngành phù hợp với ngành đào tạo trình độ thạc sĩ;

Có thời gian công tác thực tế từ 24 tháng trở lên (không tính thời gian học chương trình đào tạo các trình độ trong Công an nhân dân, thời gian tạm tuyển, thời gian tham gia nghĩa vụ Công an nhân dân). 

Trường hợp thuộc điểm a khoản 1 Điều này có thời gian công tác thực tế từ 12 tháng trở lên;

Xếp loại cán bộ đạt mức “Hoàn thành tốt nhiệm vụ” trở lên trong năm liền trước với năm dự tuyển.
            """
        }
    ]
    doc, summary = get_summary(terms)
    print("Document:", doc)
    print("-------------------")
    print("Summary:", summary)
    
    # Save summary to file
    with open(f"./test_summary/res_summary/summary_output_{datetime.now()}.json", "w", encoding="utf-8") as f:
        json.dump({
            "document": doc,
            "summary": summary
        }, f, ensure_ascii=False, indent=4)
    
    if args.markdown:
        with open(f"./test_summary/res_summary/summary_output_{datetime.now()}.md", "w", encoding="utf-8") as f:
            f.write(f"{summary}")