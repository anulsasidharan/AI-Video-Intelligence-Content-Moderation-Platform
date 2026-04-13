"""AI tool layer — frame extraction, audio transcription, OCR, object detection, similarity search."""

from app.ai.tools.audio_transcriber import (
    AudioTranscriptionError,
    TranscriptResult,
    TranscriptSegment,
    transcribe_audio,
)
from app.ai.tools.frame_extractor import (
    FrameExtractionError,
    FrameExtractionResult,
    extract_frames,
)
from app.ai.tools.object_detector import ObjectDetectionResult, detect_objects
from app.ai.tools.ocr_tool import OCRResult, run_ocr
from app.ai.tools.similarity_search import (
    SimilarityMatch,
    SimilaritySearchError,
    SimilaritySearchResult,
    query_similar,
    upsert_vectors,
)

__all__ = [
    # frame extractor
    "extract_frames",
    "FrameExtractionResult",
    "FrameExtractionError",
    # audio transcriber
    "transcribe_audio",
    "TranscriptResult",
    "TranscriptSegment",
    "AudioTranscriptionError",
    # ocr
    "run_ocr",
    "OCRResult",
    # object detector
    "detect_objects",
    "ObjectDetectionResult",
    # similarity search
    "query_similar",
    "upsert_vectors",
    "SimilaritySearchResult",
    "SimilarityMatch",
    "SimilaritySearchError",
]
