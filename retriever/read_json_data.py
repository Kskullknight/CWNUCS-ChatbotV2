import json


class JsonDataLoader:
    def __init__(self, file_path='data/cwnu_all_notices_parallel.json'):
        self.file_path = file_path
        self.data = []
    
    def load_data(self):
        """JSON 파일에서 데이터를 읽어서 필요한 필드만 추출하여 반환"""
        with open(self.file_path, 'r', encoding='utf-8') as file:
            raw_data = json.load(file)
        
        self.data = []
        for item in raw_data:
            extracted_item = {
                'url': item.get('url', ''),
                'content': item.get('content', ''),
                'title': item.get('title', ''),
                'author': item.get('author', ''),
                'date': item.get('date', ''),
                'views': item.get('views', ''),
                'number': item.get('number', '')
            }
            self.data.append(extracted_item)
        
        return self.data
    
    def get_data(self):
        """저장된 데이터 반환"""
        if not self.data:
            self.load_data()
        return self.data
    
    def get_item(self, index):
        """특정 인덱스의 아이템 반환"""
        if not self.data:
            self.load_data()
        if 0 <= index < len(self.data):
            return self.data[index]
        return None
    
    def get_total_count(self):
        """전체 데이터 개수 반환"""
        if not self.data:
            self.load_data()
        return len(self.data)