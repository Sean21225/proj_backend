"""
Resume optimization service
Integrates with external API for resume tailoring and optimization
"""

import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
import requests
from schemas import ResumeOptimizationRequest, ResumeOptimizationResponse

logger = logging.getLogger(__name__)


class ResumeOptimizerService:
    """
    Service class for resume optimization operations
    Integrates with external resume optimization API
    """
    
    def __init__(self):
        self.api_key = os.getenv("RESUME_OPTIMIZER_API_KEY", "demo_key")
        self.base_url = os.getenv("RESUME_OPTIMIZER_BASE_URL", "https://api.resumeoptimizer.com/v1")
        self.timeout = int(os.getenv("API_TIMEOUT", "30"))
        
    def _make_request(self, endpoint: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Make HTTP request to the resume optimizer API
        Handles authentication and error cases
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "JobApp-Backend/1.0"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Resume optimization service authentication failed"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Resume optimization service rate limit exceeded"
                )
            elif response.status_code >= 400:
                logger.error(f"Resume optimizer API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Resume optimization service temporarily unavailable"
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Resume optimization service timeout"
            )
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Resume optimization service unavailable"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Resume optimizer request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Resume optimization service error"
            )
    
    def optimize_resume(self, request: ResumeOptimizationRequest) -> ResumeOptimizationResponse:
        """
        Optimize resume content using external API
        Returns optimized content with suggestions
        """
        try:
            # Prepare request payload
            payload = {
                "resume_content": request.resume_content,
                "job_description": request.job_description,
                "optimization_type": request.optimization_type,
                "format": "text",
                "include_suggestions": True,
                "include_score": True
            }
            
            # Make API request
            result = self._make_request("/optimize", payload)
            
            # Parse response
            optimized_content = result.get("optimized_content", request.resume_content)
            suggestions = result.get("suggestions", [])
            score = result.get("score")
            
            return ResumeOptimizationResponse(
                optimized_content=optimized_content,
                suggestions=suggestions,
                score=score
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Resume optimization error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Resume optimization failed"
            )
    
    def analyze_resume(self, resume_content: str) -> Dict[str, Any]:
        """
        Analyze resume and provide insights
        Returns detailed analysis including strengths and weaknesses
        """
        try:
            payload = {
                "resume_content": resume_content,
                "analysis_type": "comprehensive",
                "include_keywords": True,
                "include_sections": True
            }
            
            result = self._make_request("/analyze", payload)
            
            return {
                "overall_score": result.get("overall_score", 0),
                "keyword_score": result.get("keyword_score", 0),
                "structure_score": result.get("structure_score", 0),
                "content_score": result.get("content_score", 0),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "missing_keywords": result.get("missing_keywords", []),
                "recommended_sections": result.get("recommended_sections", []),
                "word_count": result.get("word_count", 0),
                "reading_level": result.get("reading_level", "Unknown")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Resume analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Resume analysis failed"
            )
    
    def get_keywords_for_job(self, job_title: str, job_description: Optional[str] = None) -> List[str]:
        """
        Get recommended keywords for a specific job
        Helps users optimize their resume for specific positions
        """
        try:
            payload = {
                "job_title": job_title,
                "job_description": job_description,
                "keyword_type": "all",  # technical, soft, industry
                "limit": 20
            }
            
            result = self._make_request("/keywords", payload)
            
            return result.get("keywords", [])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Keyword extraction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Keyword extraction failed"
            )


# Create global service instance
resume_optimizer_service = ResumeOptimizerService()
