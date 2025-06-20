"""
LinkedIn scraper service
Integrates with external API for LinkedIn job and company data
"""

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import requests
from schemas import LinkedInJobRequest, LinkedInJobResponse, LinkedInCompanyRequest, LinkedInCompanyResponse

logger = logging.getLogger(__name__)


class LinkedInScraperService:
    """
    Service class for LinkedIn data scraping operations
    Integrates with external LinkedIn scraping API
    """
    
    def __init__(self):
        self.api_key = os.getenv("LINKEDIN_SCRAPER_API_KEY", "demo_key")
        self.base_url = os.getenv("LINKEDIN_SCRAPER_BASE_URL", "https://api.linkedinscraper.com/v1")
        self.timeout = int(os.getenv("API_TIMEOUT", "45"))  # LinkedIn scraping can take longer
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to the LinkedIn scraper API
        Handles authentication and error cases
        """
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "JobApp-Backend/1.0"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="LinkedIn scraper service authentication failed"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="LinkedIn scraper service rate limit exceeded"
                )
            elif response.status_code == 404:
                return {"data": [], "total": 0}  # No results found
            elif response.status_code >= 400:
                logger.error(f"LinkedIn scraper API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="LinkedIn scraper service temporarily unavailable"
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LinkedIn scraper service timeout"
            )
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LinkedIn scraper service unavailable"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"LinkedIn scraper request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LinkedIn scraper service error"
            )
    
    def search_jobs(self, request: LinkedInJobRequest) -> List[LinkedInJobResponse]:
        """
        Search for jobs on LinkedIn using the external API
        Returns a list of job postings matching the criteria
        """
        try:
            params = {
                "keywords": request.keywords,
                "location": request.location,
                "experience_level": request.experience_level,
                "limit": request.limit,
                "sort": "date",
                "include_description": True
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            result = self._make_request("/jobs/search", params)
            
            jobs_data = result.get("data", [])
            jobs = []
            
            for job_data in jobs_data:
                job = LinkedInJobResponse(
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    location=job_data.get("location", ""),
                    description=job_data.get("description", ""),
                    url=job_data.get("url", ""),
                    posted_date=job_data.get("posted_date")
                )
                jobs.append(job)
            
            return jobs
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"LinkedIn job search error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn job search failed"
            )
    
    def get_company_info(self, request: LinkedInCompanyRequest) -> LinkedInCompanyResponse:
        """
        Get company information from LinkedIn
        Returns detailed company data including industry and size
        """
        try:
            params = {
                "company_name": request.company_name,
                "include_details": True
            }
            
            result = self._make_request("/companies/search", params)
            
            companies_data = result.get("data", [])
            if not companies_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found on LinkedIn"
                )
            
            # Take the first (most relevant) result
            company_data = companies_data[0]
            
            company = LinkedInCompanyResponse(
                name=company_data.get("name", ""),
                industry=company_data.get("industry", ""),
                size=company_data.get("size"),
                description=company_data.get("description", ""),
                website=company_data.get("website"),
                headquarters=company_data.get("headquarters")
            )
            
            return company
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"LinkedIn company search error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn company search failed"
            )
    
    def get_job_suggestions(self, user_skills: List[str], user_location: Optional[str] = None) -> List[LinkedInJobResponse]:
        """
        Get job suggestions based on user skills and location
        Returns personalized job recommendations
        """
        try:
            # Convert skills list to keywords string
            keywords = " OR ".join(user_skills[:5])  # Limit to top 5 skills
            
            request = LinkedInJobRequest(
                keywords=keywords,
                location=user_location,
                limit=20
            )
            
            return self.search_jobs(request)
            
        except Exception as e:
            logger.error(f"LinkedIn job suggestions error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn job suggestions failed"
            )
    
    def get_trending_jobs(self, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trending job titles and their frequencies
        Helps users understand market demand
        """
        try:
            params = {
                "location": location,
                "timeframe": "week",  # last week's data
                "limit": 50
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            result = self._make_request("/jobs/trending", params)
            
            return result.get("trending_jobs", [])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"LinkedIn trending jobs error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn trending jobs failed"
            )


# Create global service instance
linkedin_scraper_service = LinkedInScraperService()
