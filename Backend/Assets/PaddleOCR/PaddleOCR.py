import paddle
from paddleocr import PaddleOCR

import os
import json
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

def binarize_image(img_path, threshold=127):
    # 이미지 열기 및 그레이스케일 변환
    img = Image.open(img_path).convert('L')  # 'L'은 그레이스케일 모드
    img_np = np.array(img)
    
    # 임계값 적용해 이진화 (threshold 초과: 255, 이하: 0)
    binarized_np = (img_np > threshold) * 255
    binarized_np = binarized_np.astype(np.uint8)
    
    # NumPy 배열을 PIL 이미지로 변환
    binarized_img = Image.fromarray(binarized_np)
    return binarized_img

def sort_text_with_bbox(ocr_result, debug=False):
    """
    고문서 OCR 결과 정렬 (우→좌, 상→하)
    DBSCAN 클러스터링을 사용하여 더 정확한 열 구분
    """
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
    columns.sort(key=lambda col: -np.mean([item['center_x'] for item in col]))
    
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

def cluster_columns_dbscan(text_boxes, debug=False):
    """
    DBSCAN 클러스터링을 사용한 열 구분
    """
    # X 좌표만 사용하여 클러스터링
    X = np.array([[item['center_x']] for item in text_boxes])
    
    # DBSCAN 매개변수 조정
    # eps: 클러스터링 거리 임계값
    # min_samples: 최소 샘플 수
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
    """
    노이즈로 분류된 항목을 가장 가까운 클러스터에 할당
    """
    if not clusters:
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

def analyze_text_layout(ocr_result):
    """
    텍스트 레이아웃 분석 및 시각화
    """
    boxes = ocr_result['rec_boxes']
    texts = ocr_result['rec_texts']
    
    # 중심 좌표 계산
    centers = [(box[0] + box[2]) / 2 for box in boxes]
    y_centers = [(box[1] + box[3]) / 2 for box in boxes]
    
    # 시각화
    plt.figure(figsize=(12, 8))
    plt.scatter(centers, y_centers, alpha=0.7)
    
    # 각 점에 인덱스 표시
    for i, (x, y) in enumerate(zip(centers, y_centers)):
        plt.annotate(f'{i}', (x, y), xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('X 좌표 (Center)')
    plt.ylabel('Y 좌표 (Center)')
    plt.title('고문서 텍스트 블록 분포')
    plt.gca().invert_yaxis()  # Y축 뒤집기 (이미지 좌표계)
    plt.grid(True, alpha=0.3)
    plt.show()
    
    return centers, y_centers

def run_PaddleOCR(filename, ocr_object):
    bin_img = binarize_image(filename, threshold=127)
    name, ext = os.path.basename(filename).split(".")
    
    bin_name = name + "_bin." + ext
    bin_path = f"./bin_images/{bin_name}"
    bin_img.save(bin_path)

    if os.path.exists(bin_path):
        result = ocr_object.predict(input=bin_path)
        print(dir(result))
        for res in result:
            res.print()
            res.save_to_img("output")
            res.save_to_json("output")
    else:
        print("Binarized Image File Not Found.")
        return
    json_name = bin_name.split(".")[0] + "_res.json"
    json_path = os.path.join("./output", json_name)
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        sorted_texts = sort_text_with_bbox(ocr_data, debug=False)
        # def convert_ocr_results(ocr_result):
        #     import opencc
        #     converter = opencc.OpenCC('jp2t')
        #     converted_texts = [converter.convert(text) for text in ocr_result]
        #     return converted_texts
        
        # 결과 출력
        print("\n=== 최종 정렬된 텍스트 ===")
        for i, text in enumerate(sorted_texts, 1):
            print(f"{i:2d}. {text}")
        
        # for i in range(len(sorted_texts)):
        #     con1 = "".join(convert_ocr_results(sorted_texts[i]))
        #     # con2 = "".join(convert_ocr_results(conv2, con1))
        #     print(f"{i:2d} : {con1}")

        # for i in range(len(sorted_texts)):
        #     print(f"changed {i} : {"".join(convert_ocr_results(sorted_texts[i]))}")
        # # 연결된 전체 텍스트
        print("\n=== 연결된 전체 텍스트 ===")
        full_text = "".join(sorted_texts)
        print(full_text)
        return full_text
    else:
        print("Json File Not Found.")
        return

paddle.set_flags({
    # CPU 메모리 사용률을 50%로 제한합니다. (0.0 ~ 1.0 사이 값)
    "FLAGS_fraction_of_cpu_memory_to_use": 0.5, 
    # 텐서 메모리 즉시 회수를 활성화하여 메모리 누수를 방지합니다.
    "FLAGS_eager_delete_tensor_gb": 0.0,
    "FLAGS_fast_eager_deletion_mode": True,
    "FLAGS_use_mkldnn": False,
})

try:
    # Try OCR with High-performance(hpi)
    ocr = PaddleOCR(
        lang='chinese_cht',
        text_det_limit_side_len = 1500,
        text_det_limit_type='max',
        cpu_threads = 1,
        use_doc_orientation_classify=True,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
        ocr_version='PP-OCRv5',
        enable_hpi=True,
        )
except RuntimeError as E:
    # if failed, go with hpi disabled
    # settings should be changed
    ocr = PaddleOCR(
        lang='chinese_cht',
        text_det_limit_side_len = 1500,
        text_det_limit_type='max',
        cpu_threads = 1,
        use_doc_orientation_classify=True,
        use_doc_unwarping=False,
        use_textline_orientation=True,
        enable_mkldnn=False,
        ocr_version='PP-OCRv5',
        enable_hpi=False,
        text_det_box_thresh=0.7,
        precision="fp32",
        )

# example
run_PaddleOCR("/Users/user/Projects/Five-Eyes/Backend/PaddleOCR/cropped_images/태조실록_001권_총서_001a면_cropped.jpg", ocr)