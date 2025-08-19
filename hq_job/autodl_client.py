import requests
import pydantic
from typing import List, Dict
import loguru


logger = loguru.logger

class AutodlImage(pydantic.BaseModel):
    id: int
    image_name: str
    image_uuid: str
    pass

class AutodlGpuStock(pydantic.BaseModel):
    idle_gpu_num: int
    total_gpu_num: int

class AutodlBlacklist(pydantic.BaseModel):
    created_at: str
    updated_at: str
    data_center: str
    expired_time: str
    machine_id: str
    msg: str
    pass

class AutodlNetworkError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        pass

class AutodlClient(object):
    def __init__(self, token):
        self.token = token
        self.host = "https://api.autodl.com"
        self.default_region = "westDC3"

    def _request(self, url, req, method=None):
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        url = f"{self.host}{url}"
        if method is None:
            if len(req) == 0:
                method = "get"
            else:
                method = "post"
                pass
            pass

        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, json=req, headers=headers)
            pass

        if response.status_code != 200:
            raise AutodlNetworkError(
                message=f"http code not 200: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        logger.info(f"Response data: {data}")
        code = data.get("code")
        if code != "Success":
            raise AutodlNetworkError(
                message=f"return code not Success: {code} - {data.get('message')}"
            )
        
        return data.get("data")
        
        
    def image_list(self, ) -> List[AutodlImage]:
        url = "/api/v1/dev/image/private/list"
        offset = 0
        page_size = 10
        page_index = 1
        images = []
        while True:
            req = {
                "offset": offset,
                "page_size": page_size,
                "page_index": page_index
            }

            logger.info(f"image list Request: {req}") 
            data = self._request(url, req)
            
            for image in data["list"]:
                images.append(AutodlImage(**image))
                pass
            
            max_page = data["max_page"]
            if page_index >= max_page:
                break
            
            page_index += 1
            pass

        return images
        pass

    def gpu_stock_list(self, region=None) -> Dict[str, AutodlGpuStock]:
        url = "/api/v1/dev/machine/region/gpu_stock"

        if region is None:
            region = self.default_region
            pass

        req = {
            "region_sign": region
        }
        
        data = self._request(url, req)
        
        stocks = dict()

        for gpu_stock in data:
            gpu_type = list(gpu_stock.keys())[0]
            idle_gpu_num = gpu_stock[gpu_type]["idle_gpu_num"]
            total_gpu_num = gpu_stock[gpu_type]["total_gpu_num"]
            stock = AutodlGpuStock(
                idle_gpu_num=idle_gpu_num,
                total_gpu_num=total_gpu_num
            )
            stocks[gpu_type] = stock
            pass
        
        return stocks
    
    def blacklist_list(self, ) -> List[AutodlBlacklist]:
        url = "/api/v1/dev/deployment/blacklist"
        data = self._request(url, {})
        blacklist = []
        if data is None:
            return blacklist
        for item in data:
            blacklist.append(AutodlBlacklist(**item))
            pass
        return blacklist
        pass