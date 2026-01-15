from openai import OpenAI
from test_fc.prompt import prompt_for_llm_judgement
from rouge_score import rouge_scorer
from sentence_transformers import CrossEncoder
import torch
import json

# Configure PyTorch precision settings to avoid warnings
torch.set_float32_matmul_precision('high')
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

class Evaluation: 
    """
    Docstring for Evaluation
    """
    def __init__(self, data_path: str): 
        with open(data_path, "r", encoding="utf-8") as f:
            if data_path.endswith("jsonl"): 
                self.data = [json.loads(line) for line in f.readlines()]
            else: 
                self.data = json.load(f)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        nli_model_name = "dleemiller/ModernCE-large-nli"
        self.nli_model = CrossEncoder(nli_model_name).to(self.device)
    
    def cal_rougeL(self) -> float: 
        """
        Calculate ROUGE-L score between prediction and ground truth
        """
        total_f1 = 0.0      
        for sample in self.data:
            reference = sample['ground_truth']
            candidate = sample['prediction']
            if isinstance(reference, list):
                reference = " ".join(" ".join(ref) if isinstance(ref, list) else ref for ref in reference)
            if isinstance(candidate, list):
                candidate = " ".join(" ".join(cand) if isinstance(cand, list) else cand for cand in candidate)
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
            scores = scorer.score(reference.lower(), candidate.lower())
            f1_score = scores['rougeL'].fmeasure
            total_f1 += f1_score
        return total_f1 / len(self.data) if len(self.data) > 0 else 0.0
    
    def cal_nli(self, pred: str, gt: str) -> tuple: 
        """
        Calculate NLI score between prediction and ground truth
        Returns: (probabilities, label) tuple where probabilities sum to 1
        """
        import numpy as np
        
        # Predict NLI score for the pair - returns array of 3 logits [entailment, contradiction, neutral]
        logits = self.nli_model.predict([(pred, gt)])[0]
        
        # Convert logits to probabilities using softmax
        exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
        probabilities = exp_logits / exp_logits.sum()
        
        # Get the predicted class index
        predicted_class = probabilities.argmax()
        
        # Map index to label
        label_mapping = ['entailment', 'contradiction', 'neutral']
        label = label_mapping[predicted_class]
        
        # Return the probabilities array and the predicted label
        return probabilities, label
    
    def judge_llm(self, question: str, human_answer: str, llm_answer: str, model: str, api_key: str, base_url: str) -> str:
        prompt = prompt_for_llm_judgement.format(
            question=question,
            human_answer=human_answer,
            llm_answer=llm_answer
        )
        # Get client
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        # Call the LLM
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        return response.choices[0].message.content


eval = Evaluation()

gt = """
3. Nghị định số 107/2024/NĐ-CP ngày 20 tháng 8 năm 2024 của Chính phủ bãi bỏ một số văn bản quy phạm pháp luật của Chính phủ
a) Hiệu lực thi hành:Nghị định này có hiệu lực thi hành từ ngày 20 tháng 8 năm 2024.
b) Sự cần thiết, mục đích ban hành:
- Sự cần thiết ban hành:
Thời gian qua, một số bộ, cơ quan ngang bộ đã thực hiện rà soát và phát hiện một số văn bản quy phạm pháp luật không còn được áp dụng trên thực tế nhưng chưa có căn cứ pháp lý để xác định hết hiệu lực theo quy định tại các Luật Ban hành văn bản quy phạm pháp luật (năm 1996, năm 2008, năm 2015 và các Luật sửa đổi, bổ sung một số điều của Luật Ban hành văn bản quy phạm pháp luật). Về nguyên tắc, các văn bản này vẫn được xác định là “còn hiệu lực”. Do đó, để bảo đảm tính công khai, minh bạch của hệ thống pháp luật, đồng thời bảo đảm tuân thủ đúng quy định về hiệu lực của văn bản theo Luật Ban hành văn bản quy phạm pháp luật năm 2015 (được sửa đổi, bổ sung năm 2020), Nghị định số 34/2016/NĐ-CP ngày 14 tháng 5 năm 2016 của Chính phủ quy định chi tiết một số điều và biện pháp thi hành Luật Ban hành văn bản quy phạm pháp luật (được sửa đổi, bổ sung bởi các Nghị định số 154/2020/NĐ-CP, Nghị định số 59/2024/NĐ-CP), việc ban hành văn bản để bãi bỏ các văn bản nêu trên là cần thiết.
Thực hiện Nghị quyết số 23/NQ-CP ngày 08/4/2018 của Chính phủ về phiên họp Chính phủ thường kỳ tháng 3 năm 2018, trên cơ sở đề xuất của các bộ, cơ quan, Bộ Tư pháp đã tổng hợp và thấy rằng có 10 văn bản quy phạm pháp luật của Chính phủ[2]cần được bãi bỏ toàn bộ.
- Mục đích ban hành:
Xử lý hiệu lực của các văn bản quy phạm pháp luật đã không còn được áp dụng trên thực tế nhưng chưa có căn cứ xác định hết hiệu lực theo quy định của Luật Ban hành văn bản quy phạm pháp luật, nhằm đảm bảo tính công khai, minh bạch của hệ thống pháp luật.
c) Nội dung chủ yếu:Nghị định gồm 02 Điều bãi bỏ một số văn bản quy phạm pháp luật của Chính phủ, cụ thể như sau:
- Điều 1: Quy định việc bãi bỏ toàn bộ văn bản quy phạm pháp luật (10 văn bản). Các văn bản bãi bỏ toàn bộ được sắp xếp theo phạm vi điều chỉnh (trong đó các văn bản điều chỉnh về cùng một vấn đề được sắp xếp gần nhau) và theo thứ tự thời gian ban hành (từ văn bản ban hành trước đến văn bản ban hành sau).
- Điều 2: Quy định về điều khoản thi hành (Hiệu lực thi hành và trách nhiệm thi hành Nghị định).
Nghị định chỉ bãi bỏ toàn bộ một số văn bản của Chính phủ không còn được áp dụng trên thực tế; Nghị định không quy định chính sách mới hay sửa đổi, bổ sung chính sách hiện có trong các nghị định, do vậy không làm phát sinh nguồn nhân lực và tài chính trong triển khai, thi hành Nghị định sau khi được Chính phủ ban hành.
Nghị định không có nội dung liên quan đến vấn đề bình đẳng giới và không quy định về thủ tục hành chính hoặc làm phát sinh thủ tục hành chính theo quy định tại Nghị định số 63/2010/NĐ-CP ngày 08/6/2010 của Chính phủ về kiểm soát thủ tục hành chính (được sửa đổi, bổ sung bởi Nghị định số 48/2013/NĐ-CP ngày 14/5/2013 của Chính phủ và Nghị định số 92/2017/NĐ-CP ngày 07/8/2017 của Chính phủ sửa đổi, bổ sung một số điều của các nghị định liên quan đến kiểm soát thủ tục hành chính).
"""

pred = """
************************************************************
Nghị định này do Chính phủ ban hành nhằm bãi bỏ toàn bộ hiệu lực của 10 nghị định do Chính phủ ban hành trước đây, bao gồm các quy định về quân hiệu, cấp hiệu, lễ phục của Bộ đội Biên phòng; chế độ đền bù, trợ cấp trong phòng, chống ma túy; khen thưởng trong phòng, chống ma túy; tổ chức và hoạt động của tổ chức bảo hiểm tương hỗ; hướng dẫn thi hành Luật Thanh niên; kiểm toán độc lập; phát hành trái phiếu Chính phủ và chính quyền địa phương; tuyển dụng công chức, viên chức và thực hiện chế độ hợp đồng trong cơ quan hành chính nhà nước, đơn vị sự nghiệp công lập.

Nghị định có hiệu lực thi hành từ ngày 20 tháng 8 năm 2024. Các Bộ trưởng, Thủ trưởng cơ quan ngang bộ, Chủ tịch UBND các tỉnh, thành phố trực thuộc trung ương và các cơ quan, đơn vị liên quan chịu trách nhiệm tổ chức thực hiện nghị định này.

Nghị định được gửi đến các cơ quan Trung ương, địa phương và các tổ chức có liên quan để biết và thực hiện.
"""

print(eval.cal_nli(pred = pred, gt = gt))  # Example usage of cal_nli