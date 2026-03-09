from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AudioMetadata(BaseModel):
    
    # identity
    id: str                        
    title: str                     
    file_name: str                 
    file_path: str                 
    
    # source info
    video_url: str                 
    playlist_url: Optional[str]    
    channel_name: Optional[str]    
    channel_url: Optional[str]     
    
    # video metadata
    duration_seconds: Optional[float]    
    upload_date: Optional[datetime]      
    description: Optional[str]           
    thumbnail_url: Optional[str]         
    language: Optional[str]              
    tags: Optional[List[str]]            
    
    # pipeline tracking
    downloaded_at: datetime              
    transcribed: bool = False            
    qa_extracted: bool = False           
    embedded: bool = False