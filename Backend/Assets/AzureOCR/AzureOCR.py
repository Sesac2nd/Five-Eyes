"""
Azure Document Intelligence OCR Backend Service
- FastAPI-based REST API for historical document OCR analysis
- Real-time Azure API integration
- Chinese character/ancient document visualization
- Vertical line-based color rendering
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from typing import List, Dict, Optional
import platform
import warnings
from pathlib import Path
from datetime import datetime
import tempfile
import base64
from io import BytesIO
import shutil

# Environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv installation required: pip install python-dotenv")

# Azure SDK imports - 안정적인 버전으로 변경
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.formrecognizer import DocumentAnalysisClient
    print("✅ Azure SDK 사용 가능")
    AZURE_SDK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Azure SDK 설치 필요: {e}")
    print("설치 명령어: pip install azure-ai-formrecognizer azure-core")
    AZURE_SDK_AVAILABLE = False

warnings.filterwarnings('ignore')

# Configure matplotlib for server environment
plt.rcParams['figure.figsize'] = [24, 16]
plt.ioff()  # Turn off interactive mode

class EnhancedAzureOCRAnalyzer:
    """Enhanced Azure Document Intelligence OCR Analyzer"""
    
    def __init__(self):
        print("🚀 Initializing Azure OCR Analyzer...")
        
        # Azure Document Analysis 클라이언트 초기화
        self.document_client = None
        self.endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        self.key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        print(f"🔍 Azure Endpoint: {self.endpoint}")
        print(f"🔍 Azure Key 존재: {'Yes' if self.key else 'No'}")
        
        if AZURE_SDK_AVAILABLE and self.endpoint and self.key:
            try:
                self.document_client = DocumentAnalysisClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.key)
                )
                print("✅ Azure Document Analysis 클라이언트 초기화 성공")
            except Exception as e:
                print(f"❌ Azure 클라이언트 초기화 실패: {e}")
        else:
            print("⚠️ Azure 설정이 완료되지 않음")

        # Darker colors for better distinction
        self.colors = [
            '#FF0000',  # Red
            '#0000FF',  # Blue  
            '#00AA00',  # Green
            '#FF8C00',  # Orange
            '#8A2BE2',  # Purple
            '#A52A2A',  # Brown
            '#FF1493',  # Pink
            '#2F4F4F',  # Gray
            '#8B8000',  # Olive
            '#00CED1'   # Cyan
        ]
        
        # RGB color map for PIL
        self.color_map = {
            '#FF0000': (255, 0, 0),
            '#0000FF': (0, 0, 255), 
            '#00AA00': (0, 170, 0),
            '#FF8C00': (255, 140, 0),
            '#8A2BE2': (138, 43, 226),
            '#A52A2A': (165, 42, 42),
            '#FF1493': (255, 20, 147),
            '#2F4F4F': (47, 79, 79),
            '#8B8000': (139, 128, 0),
            '#00CED1': (0, 206, 209)
        }
        
        # Font setup
        self.han_font = self._setup_cjk_font()
        self._configure_matplotlib()
        
        # Create temp directory for file processing
        self.temp_dir = tempfile.mkdtemp()
        
        print(f"✅ Initialization completed")
    
    def _setup_cjk_font(self):
        """Setup Chinese character fonts"""
        system = platform.system()
        
        if system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/simsun.ttc",  # Chinese character optimized
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/batang.ttc"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return fm.FontProperties(fname=font_path)
                    except:
                        continue
        
        return fm.FontProperties()
    
    def _configure_matplotlib(self):
        """Configure matplotlib settings"""
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 14
    
    def analyze_image_realtime(self, image_data: bytes) -> Optional[Dict]:
        """Real-time Azure API image analysis"""
        if not self.document_client:
            print("❌ Azure client not configured.")
            return None
        
        try:
            print(f"📄 Real-time analysis with Azure...")
            print("⏳ Calling Azure API... (30 seconds - 2 minutes required)")
            
            # Azure Document Analysis API 호출
            poller = self.document_client.begin_analyze_document(
                "prebuilt-read",
                document=image_data
            )
            
            # 결과 대기
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
            
            # 현재 문제가 있는 코드 부분 수정
            for page_idx, page in enumerate(result.pages):
                page_data = {
                    "pageNumber": page_idx + 1,
                    "words": []
                }
                
                # 수정: page.words를 직접 사용 (line.words가 아닌)
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
            
            # Analysis statistics
            avg_confidence = total_confidence / total_words if total_words > 0 else 0
            print(f"✅ Azure real-time analysis completed: {total_words} words, average confidence {avg_confidence:.3f}")
            
            return ocr_result
            
        except Exception as e:
            print(f"❌ Azure OCR 분석 실패: {str(e)}")
            print(f"🔍 오류 타입: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            raise e
    
    def group_words_by_vertical_lines(self, words_data: List[Dict], threshold: float = 50) -> List[List[Dict]]:
        """Group by vertical lines (reflecting Chinese document characteristics)"""
        if not words_data:
            return []
        
        # Sort by X coordinate
        sorted_words = sorted(words_data, key=lambda w: w['polygon'][0])
        vertical_lines = []
        current_line = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            current_line_avg_x = sum(w['polygon'][0] for w in current_line) / len(current_line)
            current_word_x = word['polygon'][0]
            
            if abs(current_word_x - current_line_avg_x) <= threshold:
                current_line.append(word)
            else:
                # Sort by Y coordinate (vertical reading)
                current_line.sort(key=lambda w: w['polygon'][1])
                vertical_lines.append(current_line)
                current_line = [word]
        
        if current_line:
            current_line.sort(key=lambda w: w['polygon'][1])
            vertical_lines.append(current_line)
        
        return vertical_lines
    
    def create_visualization(self, image_data: bytes, ocr_data: Dict) -> Optional[str]:
        """Create OCR result visualization"""
        print(f"🎨 Creating visualization...")
        
        # Extract word data
        words_data = []
        for page in ocr_data["analyzeResult"]["pages"]:
            words_data.extend(page["words"])
        
        if not words_data:
            print("❌ OCR data is empty.")
            return None
        
        # Group by vertical lines
        vertical_lines = self.group_words_by_vertical_lines(words_data)
        
        # Load original image
        try:
            original_image = Image.open(BytesIO(image_data))
            width, height = original_image.size
        except Exception as e:
            print(f"❌ Image loading failed: {e}")
            return None
        
        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(24, 16))
        
        # Left: Dark colored boxes image
        boxed_image = self._create_colored_boxes(image_data, vertical_lines)
        axes[0].imshow(boxed_image)
        axes[0].axis('off')
        
        # Right: Uniform size Chinese text + vertical outlines
        text_image = self._create_text_rendering_with_outlines(image_data, vertical_lines, width, height)
        axes[1].imshow(text_image)
        axes[1].axis('off')
        
        # Minimize margins
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.02)
        
        # Save to temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        viz_path = os.path.join(self.temp_dir, f"viz_{timestamp}.png")
        
        plt.savefig(viz_path, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.close()  # Close the figure to free memory
        
        print(f"💾 Visualization saved: {viz_path}")
        
        # Print simple statistics only
        print(f"📊 Analysis results: {len(words_data)} words, {len(vertical_lines)} vertical lines")
        
        return viz_path
    
    def _create_colored_boxes(self, image_data: bytes, vertical_lines: List[List[Dict]]) -> np.ndarray:
        """Create dark colored boxes image"""
        try:
            pil_image = Image.open(BytesIO(image_data)).convert('RGB')
            draw = ImageDraw.Draw(pil_image)
            
            for line_idx, line_words in enumerate(vertical_lines):
                color_hex = self.colors[line_idx % len(self.colors)]
                color_rgb = self.color_map[color_hex]
                
                for word in line_words:
                    polygon = word['polygon']
                    if len(polygon) >= 4:
                        points = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
                        # Thicker borders for darker appearance
                        draw.polygon(points, outline=color_rgb, width=5)
            
            return np.array(pil_image)
            
        except Exception as e:
            print(f"❌ Colored boxes creation failed: {e}")
            return np.ones((300, 300, 3), dtype=np.uint8) * 255
    
    def _create_text_rendering_with_outlines(self, image_data: bytes, vertical_lines: List[List[Dict]], width: int, height: int) -> np.ndarray:
        """Uniform size Chinese characters + vertical outline rendering"""
        try:
            # Create white background image
            pil_image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(pil_image)
            
            # Set uniform font size (fixed value)
            UNIFORM_FONT_SIZE = 96  # Same size for all characters
            
            # Pre-load font
            try:
                if platform.system() == "Windows":
                    font_path = "C:/Windows/Fonts/simsun.ttc"
                    if os.path.exists(font_path):
                        uniform_font = ImageFont.truetype(font_path, UNIFORM_FONT_SIZE)
                    else:
                        uniform_font = ImageFont.load_default()
                else:
                    uniform_font = ImageFont.load_default()
            except:
                uniform_font = ImageFont.load_default()
            
            # Draw outlines for each vertical line + uniform size text
            for line_idx, line_words in enumerate(vertical_lines):
                if not line_words:
                    continue
                    
                color_hex = self.colors[line_idx % len(self.colors)]
                color_rgb = self.color_map[color_hex]
                
                # Calculate vertical line area
                x_coords = []
                y_coords = []
                for word in line_words:
                    polygon = word['polygon']
                    if len(polygon) >= 4:
                        points = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
                        x_coords.extend([p[0] for p in points])
                        y_coords.extend([p[1] for p in points])
                
                if x_coords and y_coords:
                    min_x = min(x_coords) - 5
                    max_x = max(x_coords) + 5
                    min_y = min(y_coords) - 5
                    max_y = max(y_coords) + 5
                    
                    # Draw vertical line outlines only (no fill)
                    draw.rectangle(
                        [(min_x, min_y), (max_x, max_y)], 
                        outline=color_rgb, 
                        width=2
                    )
                
                # Render uniform size Chinese text
                for word in line_words:
                    polygon = word['polygon']
                    if len(polygon) >= 4:
                        points = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
                        center_x = sum(p[0] for p in points) / len(points)
                        center_y = sum(p[1] for p in points) / len(points)
                        
                        # Draw dark Chinese text (uniform size)
                        draw.text(
                            (center_x, center_y), 
                            word['content'],
                            font=uniform_font,
                            fill='black',
                            anchor='mm'
                        )
            
            return np.array(pil_image)
            
        except Exception as e:
            print(f"❌ Text rendering failed: {e}")
            return np.ones((height, width, 3), dtype=np.uint8) * 255
    
    def analyze_complete(self, image_data: bytes) -> Dict:
        """Complete real-time analysis and visualization"""
        print(f"🚀 Starting Azure complete analysis...")
        
        # 1. Real-time analysis with Azure API
        ocr_data = self.analyze_image_realtime(image_data)
        
        if not ocr_data:
            raise Exception("Real-time analysis failed")
        
        # 2. Create visualization
        viz_path = self.create_visualization(image_data, ocr_data)
        
        if not viz_path:
            raise Exception("Visualization failed")
        
        print("✅ Analysis and visualization completed!")
        
        return {
            "ocr_data": ocr_data,
            "visualization_path": viz_path,
            "status": "success"
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

# Initialize FastAPI app
app = FastAPI(title="Azure OCR Historical Document Analyzer", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer instance
analyzer = None

@app.on_event("startup")
async def startup_event():
    global analyzer
    analyzer = EnhancedAzureOCRAnalyzer()
    if not analyzer.document_client:
        print("⚠️ Azure client not configured. Check environment variables.")

@app.on_event("shutdown")
async def shutdown_event():
    global analyzer
    if analyzer:
        analyzer.cleanup()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Azure OCR Historical Document Analyzer",
        "status": "running",
        "azure_configured": analyzer.document_client is not None if analyzer else False
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "azure_sdk_available": AZURE_SDK_AVAILABLE,
        "azure_client_configured": analyzer.document_client is not None if analyzer else False
    }

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """Analyze historical document with OCR"""
    
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    if not analyzer.document_client:
        raise HTTPException(status_code=500, detail="Azure client not configured")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are supported")
    
    try:
        # Read uploaded file
        image_data = await file.read()
        
        # Perform complete analysis
        result = analyzer.analyze_complete(image_data)
        
        # Convert visualization to base64 for response
        with open(result["visualization_path"], "rb") as viz_file:
            viz_base64 = base64.b64encode(viz_file.read()).decode()
        
        # Extract basic OCR statistics
        words_data = []
        for page in result["ocr_data"]["analyzeResult"]["pages"]:
            words_data.extend(page["words"])
        
        return {
            "status": "success",
            "message": "Analysis completed successfully",
            "statistics": {
                "total_words": len(words_data),
                "total_pages": len(result["ocr_data"]["analyzeResult"]["pages"]),
                "average_confidence": sum(w["confidence"] for w in words_data) / len(words_data) if words_data else 0
            },
            "ocr_data": result["ocr_data"],
            "visualization_base64": viz_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/visualization/{filename}")
async def get_visualization(filename: str):
    """Get visualization file"""
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized")
    
    file_path = os.path.join(analyzer.temp_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Visualization file not found")
    
    return FileResponse(file_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Azure OCR Backend Service...")
    print("📋 Environment check:")
    print(f"   - Azure SDK Available: {AZURE_SDK_AVAILABLE}")
    print(f"   - Environment Variables: {bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'))}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False  # Set to False for production
    )