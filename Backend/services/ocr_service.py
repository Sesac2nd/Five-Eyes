import os
import json
import time
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import traceback

load_dotenv()
DEBUG_FLAG = os.getenv("IS_DEBUG", "")

# 프로젝트 루트 디렉터리 설정 (Backend의 상위 폴더)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BIN_IMAGES_DIR = os.path.join(DATA_DIR, "bin_images")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

def ensure_directories():
    """필요한 디렉터리가 존재하지 않으면 생성"""
    directories = [DATA_DIR, BIN_IMAGES_DIR, OUTPUT_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ 디렉터리 생성됨: {directory}")
        else:
            print(f"📁 디렉터리 확인됨: {directory}")

# PaddleOCR 관련 임포트 시도
try:
    import paddle
    from paddleocr import PaddleOCR
    import numpy as np
    from PIL import Image
    from sklearn.cluster import DBSCAN
    PADDLE_OCR_AVAILABLE = True
    print("✅ PaddleOCR 사용 가능")
except ImportError as e:
    print(f"⚠️ PaddleOCR 가져오기 실패: {e}")
    PADDLE_OCR_AVAILABLE = False

# Azure OCR 관련 임포트 시도
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.formrecognizer import DocumentAnalysisClient
    AZURE_OCR_AVAILABLE = True
    print("✅ Azure OCR 사용 가능")
except ImportError as e:
    print(f"⚠️ Azure OCR 가져오기 실패: {e}")
    AZURE_OCR_AVAILABLE = False


class OCRResult:
    """OCR 분석 결과 데이터 클래스"""
    def __init__(
        self,
        status: str = "processing",
        extracted_text: str = "",
        word_count: int = 0,
        confidence_score: float = 0.0,
        processing_time: float = 0.0,
        visualization_path: Optional[str] = None,
        error_message: Optional[str] = None,
        ocr_data: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.extracted_text = extracted_text
        self.word_count = word_count
        self.confidence_score = confidence_score
        self.processing_time = processing_time
        self.visualization_path = visualization_path
        self.error_message = error_message
        self.ocr_data = ocr_data


def binarize_image(img_path: str, threshold: int = 127):
    """이미지 이진화 함수"""
    if not PADDLE_OCR_AVAILABLE:
        return None
    
    # 이미지 열기 및 그레이스케일 변환
    img = Image.open(img_path).convert('L')  # 'L'은 그레이스케일 모드
    img_np = np.array(img)
    
    # 임계값 적용해 이진화 (threshold 초과: 255, 이하: 0)
    binarized_np = (img_np > threshold) * 255
    binarized_np = binarized_np.astype(np.uint8)
    
    # NumPy 배열을 PIL 이미지로 변환
    binarized_img = Image.fromarray(binarized_np)
    return binarized_img


def sort_text_with_bbox(ocr_result: Dict, debug: bool = False):
    """
    고문서 OCR 결과 정렬 (우→좌, 상→하)
    DBSCAN 클러스터링을 사용하여 더 정확한 열 구분
    """
    if not PADDLE_OCR_AVAILABLE:
        return []
    
    boxes = ocr_result['rec_boxes']
    texts = ocr_result['rec_texts']
    
    # 박스와 텍스트를 묶어서 처리
    text_boxes = []
    for i, (box, text) in enumerate(zip(boxes, texts)):
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        height = y2 - y1
        text_boxes.append({
            'text': text,
            'center_x': center_x,
            'center_y': center_y,
            'height': height,
            'box': box,
            'index': i
        })
    
    if debug:
        print("=== 원본 데이터 분석 ===")
        for i, item in enumerate(text_boxes):
            print(f"{i:2d}: X={item['center_x']:4.0f} Y={item['center_y']:4.0f} H={item['height']:4d} \"{item['text'][:20]}...\"")
    
    # 1단계: DBSCAN을 사용한 열 클러스터링
    columns = cluster_columns_dbscan(text_boxes, debug)
    
    # 2단계: 각 열을 오른쪽에서 왼쪽 순서로 정렬
    columns.sort(key=lambda col: -float(np.mean([item['center_x'] for item in col])))
    
    # 3단계: 각 열 내에서 Y 좌표 기준 정렬 (상→하)
    sorted_text = []
    for col_idx, column in enumerate(columns):
        # 열 내에서 Y 좌표 순으로 정렬
        column.sort(key=lambda item: item['center_y'])
        
        if debug:
            avg_x = np.mean([item['center_x'] for item in column])
            print(f"\n열 {col_idx + 1} (평균 X: {avg_x:.0f}):")
            for j, item in enumerate(column):
                print(f"  {j+1:2d}: Y={item['center_y']:4.0f} \"{item['text'][:30]}...\"")
        
        sorted_text.extend([item['text'] for item in column])
    
    return sorted_text


def cluster_columns_dbscan(text_boxes, debug: bool = False):
    """DBSCAN 클러스터링을 사용한 열 구분"""
    if not PADDLE_OCR_AVAILABLE:
        return []
    
    # X 좌표만 사용하여 클러스터링
    X = np.array([[item['center_x']] for item in text_boxes])
    
    # DBSCAN 매개변수 조정
    eps = 120  # 픽셀 단위
    min_samples = 1
    
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = clustering.labels_
    
    # 클러스터별로 그룹화
    columns = {}
    for i, label in enumerate(labels):
        if label == -1:  # 노이즈로 분류된 경우 가장 가까운 클러스터에 할당
            label = find_nearest_cluster(text_boxes[i], columns)
        
        if label not in columns:
            columns[label] = []
        columns[label].append(text_boxes[i])
    
    if debug:
        print(f"\n=== DBSCAN 클러스터링 결과 (eps={eps}) ===")
        for label, items in columns.items():
            avg_x = np.mean([item['center_x'] for item in items])
            print(f"클러스터 {label}: {len(items)}개 항목, 평균 X={avg_x:.0f}")
    
    return list(columns.values())


def find_nearest_cluster(item, clusters):
    """노이즈로 분류된 항목을 가장 가까운 클러스터에 할당"""
    if not PADDLE_OCR_AVAILABLE or not clusters:
        return 0
    
    min_distance = float('inf')
    nearest_label = 0
    
    for label, cluster_items in clusters.items():
        cluster_center_x = np.mean([ci['center_x'] for ci in cluster_items])
        distance = abs(item['center_x'] - cluster_center_x)
        if distance < min_distance:
            min_distance = distance
            nearest_label = label
    
    return nearest_label


def initialize_paddle_ocr():
    """PaddleOCR 인스턴스 초기화"""
    if not PADDLE_OCR_AVAILABLE:
        return None
    
    # Paddle 설정
    paddle.set_flags({
        "FLAGS_fraction_of_cpu_memory_to_use": 0.5, 
        "FLAGS_eager_delete_tensor_gb": 0.0,
        "FLAGS_fast_eager_deletion_mode": True,
        "FLAGS_use_mkldnn": False,
    })
    
    try:
        # Try OCR with High-performance(hpi)
        ocr = PaddleOCR(
            lang='chinese_cht',
            text_det_limit_side_len=1500,
            text_det_limit_type='max',
            cpu_threads=1,
            use_doc_orientation_classify=True,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
            ocr_version='PP-OCRv5',
            enable_hpi=True,
        )
        return ocr
    except RuntimeError:
        # If failed, go with hpi disabled
        ocr = PaddleOCR(
            lang='chinese_cht',
            text_det_limit_side_len=1500,
            text_det_limit_type='max',
            cpu_threads=1,
            use_doc_orientation_classify=True,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            enable_mkldnn=False,
            ocr_version='PP-OCRv5',
            enable_hpi=False,
            text_det_box_thresh=0.7,
            precision="fp32",
        )
        return ocr


def run_paddle_ocr_analysis(filename: str, ocr_object) -> Optional[Dict[str, Any]]:
    """PaddleOCR 분석 실행"""
    if not PADDLE_OCR_AVAILABLE or not ocr_object:
        return None
    
    try:
        # 이미지 이진화
        bin_img = binarize_image(filename, threshold=127)
        if bin_img is None:
            return None
        
        name, ext = os.path.basename(filename).split(".", 1)
        bin_name = name + "_bin." + ext
        bin_path = os.path.join(BIN_IMAGES_DIR, bin_name)
        bin_img.save(bin_path)

        avg_confidence = None

        if os.path.exists(bin_path):
            result = ocr_object.predict(input=bin_path)
            for res in result:
                res.print()
                res.save_to_img(OUTPUT_DIR)
                res.save_to_json(OUTPUT_DIR)
        else:
            print("Binarized Image File Not Found.")
            return None
        
        json_path = os.path.join(OUTPUT_DIR, name + "_bin_res.json")
        res_json = None
        rec_scores = None

        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                res_json = json.load(f)
                rec_scores = res_json["rec_scores"]

        if rec_scores:
            scores = [float(s) for s in rec_scores if s is not None]
            if scores:
                avg_confidence = sum(scores) / len(scores)

        img_path = os.path.join(OUTPUT_DIR, f"{name}_bin_ocr_res_img.jpg")
        vis_img_path = img_path if os.path.exists(img_path) else None

        json_name = bin_name.split(".")[0] + "_res.json"
        json_path = os.path.join(OUTPUT_DIR, json_name)
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            sorted_texts = sort_text_with_bbox(ocr_data, debug=False)
            
            # 결과 출력
            print("\n=== 최종 정렬된 텍스트 ===")
            for i, text in enumerate(sorted_texts, 1):
                print(f"{i:2d}. {text}")
            
            print("\n=== 연결된 전체 텍스트 ===")
            full_text = "".join(sorted_texts)
            print(full_text)
            return {
                "full_text": full_text,
                "visualization_path": vis_img_path,  # 존재하면 경로, 없으면 None
                "ocr_data": ocr_data,
                "avg_confidence": avg_confidence
            }
        else:
            print("Json File Not Found.")
            return None
            
    except Exception as e:
        print(f"❌ PaddleOCR 분석 중 오류: {e}")
        return None


def initialize_azure_ocr():
    """Azure OCR 클라이언트 초기화"""
    if not AZURE_OCR_AVAILABLE:
        return None
    
    endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    
    if not endpoint or not key:
        print("⚠️ Azure Document Intelligence 환경변수가 설정되지 않음")
        return None
    
    try:
        client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        print("✅ Azure Document Analysis 클라이언트 초기화 성공")
        return client
    except Exception as e:
        print(f"❌ Azure 클라이언트 초기화 실패: {e}")
        return None


def run_azure_ocr_analysis(file_path: str, client) -> Dict[str, Any]:
    """Azure OCR 분석 실행"""
    if not AZURE_OCR_AVAILABLE or not client:
        return {}
    
    try:
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        print(f"📄 Azure OCR 분석 시작...")
        print("⏳ Azure API 호출 중... (30초 - 2분 소요)")
        
        # Azure Document Analysis API 호출
        poller = client.begin_analyze_document("prebuilt-read", document=image_data)
        result = poller.result()
        
        print(f"✅ Azure 분석 완료: {len(result.pages)} 페이지")
        
        # 결과를 표준 형식으로 변환
        ocr_result = {
            "analyzeResult": {
                "pages": [],
                "version": "3.2",
                "apiVersion": "2023-07-31",
                "modelId": "prebuilt-read"
            }
        }
        
        total_words = 0
        total_confidence = 0
        
        for page_idx, page in enumerate(result.pages):
            page_data = {
                "pageNumber": page_idx + 1,
                "words": []
            }
            
            for word in page.words:
                word_data = {
                    "content": word.content,
                    "confidence": word.confidence,
                    "polygon": [
                        coord for point in word.polygon
                        for coord in [point.x, point.y]
                    ]
                }
                page_data["words"].append(word_data)
                total_words += 1
                total_confidence += word.confidence
            
            ocr_result["analyzeResult"]["pages"].append(page_data)
        
        # 통계 정보
        avg_confidence = total_confidence / total_words if total_words > 0 else 0
        print(f"✅ Azure 분석 완료: {total_words} 단어, 평균 신뢰도 {avg_confidence:.3f}")
        
        return ocr_result
        
    except Exception as e:
        print(f"❌ Azure OCR 분석 실패: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {}


def analyze_document(
    file_path: str,
    engine: str = "paddle",
    extract_text_only: bool = False,
    visualization: bool = True
) -> OCRResult:
    """
    문서 OCR 분석 메인 함수
    """
    start_time = time.time()
    
    # 디렉터리 확인 및 생성
    ensure_directories()
    print(f"analuze_doc : {engine}")
    try:
        if engine.lower() == "paddle":
            return analyze_with_paddle(file_path, extract_text_only, visualization, start_time)
        elif engine.lower() == "azure":
            return analyze_with_azure(file_path, extract_text_only, visualization, start_time)
        else:
            processing_time = time.time() - start_time
            return OCRResult(
                status="failed",
                error_message=f"지원하지 않는 엔진: {engine}. 'paddle' 또는 'azure'를 사용하세요.",
                processing_time=processing_time
            )
    
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ OCR 분석 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
        return OCRResult(
            status="failed",
            error_message=str(e),
            processing_time=processing_time
        )


def analyze_with_paddle(
    file_path: str,
    extract_text_only: bool = False,
    visualization: bool = True,
    start_time: Optional[float] = None
) -> OCRResult:
    """PaddleOCR를 사용한 문서 분석"""
    if start_time is None:
        start_time = time.time()
    
    if not PADDLE_OCR_AVAILABLE:
        processing_time = time.time() - start_time
        return OCRResult(
            status="failed",
            error_message="PaddleOCR를 사용할 수 없습니다. 설치를 확인해주세요.",
            processing_time=processing_time
        )
    
    try:
        print(f"🔍 PaddleOCR로 분석 시작: {file_path}")
        
        # PaddleOCR 인스턴스 초기화
        ocr_instance = initialize_paddle_ocr()
        if not ocr_instance:
            processing_time = time.time() - start_time
            return OCRResult(
                status="failed",
                error_message="PaddleOCR 초기화에 실패했습니다.",
                processing_time=processing_time
            )
        
        # PaddleOCR 실행
        paddle_resp = run_paddle_ocr_analysis(file_path, ocr_instance)
        
        if not paddle_resp:
            processing_time = time.time() - start_time
            return OCRResult(
                status="failed",
                error_message="PaddleOCR에서 텍스트를 추출할 수 없습니다.",
                processing_time=processing_time
            )
        
        extracted_text = paddle_resp.get("full_text", "")
        vis_path = paddle_resp.get("visualization_path")
        ocr_data = paddle_resp.get("ocr_data")

        # 단어 수 계산
        word_count = len(extracted_text.replace(" ", ""))  # 한국어/중국어의 경우 공백 제거 후 문자 수
        
        # 신뢰도 점수
        avg_confidence = paddle_resp.get("avg_confidence")
        confidence_score = float(avg_confidence) if avg_confidence is not None else 0.0

        visualization_path = vis_path if visualization else None
        processing_time = time.time() - start_time
        
        print(f"✅ PaddleOCR 분석 완료: {word_count}자, {processing_time:.2f}초")
        
        return OCRResult(
            status="completed",
            extracted_text=extracted_text,
            word_count=word_count,
            confidence_score=confidence_score,
            processing_time=processing_time,
            visualization_path=visualization_path,
            ocr_data = ocr_data
            # ocr_data={"engine": "paddle", "raw_text": extracted_text} if not extract_text_only else None
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ PaddleOCR 분석 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
        return OCRResult(
            status="failed",
            error_message=f"PaddleOCR 분석 실패: {str(e)}",
            processing_time=processing_time
        )


def analyze_with_azure(
    file_path: str,
    extract_text_only: bool = False,
    visualization: bool = True,
    start_time: Optional[float] = None
) -> OCRResult:
    """Azure Document Intelligence를 사용한 문서 분석"""
    if start_time is None:
        start_time = time.time()
    
    if not AZURE_OCR_AVAILABLE:
        processing_time = time.time() - start_time
        return OCRResult(
            status="failed",
            error_message="AzureOCR를 사용할 수 없습니다. 설치를 확인해주세요.",
            processing_time=processing_time
        )
    
    try:
        print(f"🔍 Azure OCR로 분석 시작: {file_path}")
        
        # Azure OCR 클라이언트 초기화
        client = initialize_azure_ocr()
        if not client:
            processing_time = time.time() - start_time
            return OCRResult(
                status="failed",
                error_message="Azure OCR 클라이언트 초기화에 실패했습니다.",
                processing_time=processing_time
            )
        
        # Azure OCR 분석 실행
        ocr_data = run_azure_ocr_analysis(file_path, client)
        
        if not ocr_data:
            processing_time = time.time() - start_time
            return OCRResult(
                status="failed",
                error_message="Azure OCR에서 분석 결과를 받을 수 없습니다.",
                processing_time=processing_time
            )
        
        # 텍스트 추출 및 통계 계산
        extracted_text = ""
        total_confidence = 0.0
        word_count = 0
        
        for page in ocr_data["analyzeResult"]["pages"]:
            for word in page["words"]:
                extracted_text += word["content"]
                total_confidence += word["confidence"]
                word_count += 1
        
        confidence_score = total_confidence / word_count if word_count > 0 else 0.0
        processing_time = time.time() - start_time
        
        # 시각화는 Azure에서 제공하지 않으므로 None
        visualization_path = None
        if visualization:
            print("⚠️ Azure OCR 시각화는 현재 구현되지 않았습니다.")
        
        print(f"✅ Azure OCR 분석 완료: {word_count}단어, 신뢰도 {confidence_score:.3f}, {processing_time:.2f}초")
        
        return OCRResult(
            status="completed",
            extracted_text=extracted_text,
            word_count=word_count,
            confidence_score=confidence_score,
            processing_time=processing_time,
            visualization_path=visualization_path,
            ocr_data=ocr_data if not extract_text_only else None
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Azure OCR 분석 오류: {traceback.format_exc() if DEBUG_FLAG else e}")
        return OCRResult(
            status="failed",
            error_message=f"Azure OCR 분석 실패: {str(e)}",
            processing_time=processing_time
        )


def get_available_engines() -> Dict[str, bool]:
    """사용 가능한 OCR 엔진 목록 반환"""
    return {
        "paddle": PADDLE_OCR_AVAILABLE,
        "azure": AZURE_OCR_AVAILABLE
    }


def validate_image_file(file_path: str) -> bool:
    """이미지 파일 유효성 검사"""
    if not os.path.exists(file_path):
        return False
    
    # 파일 확장자 확인
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    _, ext = os.path.splitext(file_path.lower())
    
    return ext in valid_extensions