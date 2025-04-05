import random
import string
from typing import Optional
from fastapi import HTTPException

class DatabaseManager:
    def __init__(self, urls, session):
        self.urls = urls
        self.session = session
     
    def generate_short_url(self):
        short_url = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return short_url
    
    def add_url(self, long_url, short_url: Optional[str] = None):
        if not short_url:
            short_url = None
        if short_url is None:
            short_url = self.generate_short_url()
            while self.session.query(self.urls).filter_by(short_url=short_url).first():
                short_url = self.generate_short_url()
            self.session.add(self.urls(long_url=long_url, short_url=short_url))
            self.session.commit()
            return short_url
        else:
            if self.session.query(self.urls).filter_by(short_url=short_url).first():
                raise HTTPException(status_code=400, detail="Short URL already exists, please choose another one")
            else:
                self.session.add(self.urls(long_url=long_url, short_url=short_url))
                self.session.commit()
                return short_url
        
    def get_url(self, short_url):
        result = self.session.query(self.urls).filter_by(short_url=short_url).first()
        if result:
            return result.long_url
        else:
            raise HTTPException(status_code=400, detail="Short URL not found")       
        
    def delete_url(self, short_url):
        result = self.session.query(self.urls).filter_by(short_url=short_url).first()
        if not result:
            raise HTTPException(status_code=400, detail="Short URL not found")
        else:
            self.session.delete(result)
            self.session.commit()
            print(f"short url '{short_url}' deleted from the database")   