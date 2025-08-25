import requests
import pydantic
from typing import List, Dict, Optional, Union
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

class AutodlDeployment(pydantic.BaseModel):
    id: int
    uid: int
    uuid: str
    name: str
    deployment_type: str
    status: str
    region_sign: str
    dc_list: List[str]
    gpu_name_set: List[str]
    created_at: str


class AutodlContainerEvent(pydantic.BaseModel):
    deployment_container_uuid: str
    status: str
    created_at: str

class AutodlContainer(pydantic.BaseModel):
    id: int
    machine_id: str
    deployment_uuid: str
    status: str
    gpu_name: str
    gpu_num: int
    cpu_num: int
    memory_size: int
    image_uuid: str
    price: int
    uuid: str
    version: str
    data_center: str
    info: dict
    started_at: Optional[str]
    stopped_at: Optional[str]
    created_at: str
    updated_at: str

class AutodlGpuStockElastic(pydantic.BaseModel):
    gpu_type: str
    total_gpu_num: int
    idle_gpu_num: int
    chip_corp: Optional[str] = None
    cpu_arch: Optional[str] = None

class AutodlDdpOverview(pydantic.BaseModel):
    gpu_type: str
    total: int
    balance: int
    dc_list: str
    pass

class AutodlNetworkError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        pass


class AutoDLConstants:
    """AutoDL constants"""
    
    # region sign
    REGIONS = {
        "西北企业区(推荐)": "westDC2",
        "西北B区": "westDC3", 
        "北京A区": "beijingDC1",
        "北京B区": "beijingDC2",
        "L20专区(原北京C区)": "beijingDC4",
        "V100专区(原华南A区)": "beijingDC3",
        "内蒙A区": "neimengDC1",
        "佛山区": "foshanDC1",
        "重庆A区": "chongqingDC1",
        "3090专区": "yangzhouDC1",
        "内蒙B区": "neimengDC3"
    }
    
    # base image uuid
    BASE_IMAGES = {
        "PyTorch 1.9.0 (CUDA 11.1)": "base-image-12be412037",
        "PyTorch 1.10.0 (CUDA 11.3)": "base-image-u9r24vthlk",
        "PyTorch 1.11.0 (CUDA 11.3)": "base-image-l374uiucui",
        "PyTorch 2.0.0 (CUDA 11.8)": "base-image-l2t43iu6uk",
        "TensorFlow 2.5.0 (CUDA 11.2)": "base-image-0gxqmciyth",
        "TensorFlow 2.9.0 (CUDA 11.2)": "base-image-uxeklgirir",
        "TensorFlow 1.15.5 (CUDA 11.4)": "base-image-4bpg0tt88l",
        "Miniconda (CUDA 11.6)": "base-image-mbr2n4urrc",
        "Miniconda (CUDA 10.2)": "base-image-qkkhitpik5",
        "Miniconda (CUDA 11.1)": "base-image-h041hn36yt",
        "Miniconda (CUDA 11.3)": "base-image-7bn8iqhkb5",
        "Miniconda (CUDA 9.0)": "base-image-k0vep6kyq8",
        "TensorRT 8.5.1 (CUDA 11.8)": "base-image-l2843iu23k"
    }
    
    # CUDA version mapping
    CUDA_VERSIONS = {
        "11.8": 118,
        "12.0": 120,
        "12.1": 121,
        "12.2": 122
    }
    
    # GPU types
    GPU_TYPES = [
        "RTX 4090", "RTX 4080", "RTX 3090", "RTX 3080", "RTX 3070",
        "V100", "A100", "H100", "L20", "L40"
    ]


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
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict:
        """Send HTTP request"""
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        url = f"{self.host}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
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
            return data
            
        except requests.exceptions.RequestException as e:
            raise AutodlNetworkError(f"API request failed: {e}")
        
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
            
            max_page = data["max_page"]
            if page_index >= max_page:
                break
            
            page_index += 1

        return images

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

        return blacklist

    # Elastic deployment related functions
    def create_deployment(self, name: str, image_uuid: str, deployment_type: str = "ReplicaSet",
                         replica_num: int = 1, parallelism_num: Optional[int] = None,
                         gpu_name_set: Optional[List[str]] = None, gpu_num: int = 1,
                         cuda_v_from: int = 113, cuda_v_to: int = 128,
                         cpu_num_from: int = 1, cpu_num_to: int = 100,
                         memory_size_from: int = 1, memory_size_to: int = 256,
                         dc_list: Optional[List[str]] = None, cmd: str = "sleep 100",
                         price_from: int = 10, price_to: int = 9000,
                         reuse_container: bool = True, env_vars: Optional[Dict[str, str]] = None) -> str:
        """Create elastic deployment"""
        if dc_list is None:
            dc_list = ["westDC2", "westDC3"]
        
        if gpu_name_set is None:
            gpu_name_set = ["RTX 4090"]
        
        data = {
            "name": name,
            "deployment_type": deployment_type,
            "replica_num": replica_num,
            "reuse_container": reuse_container,
            "container_template": {
                "dc_list": dc_list,
                "gpu_name_set": gpu_name_set,
                "gpu_num": gpu_num,
                "cuda_v_from": cuda_v_from,
                "cuda_v_to": cuda_v_to,
                "cpu_num_from": cpu_num_from,
                "cpu_num_to": cpu_num_to,
                "memory_size_from": memory_size_from,
                "memory_size_to": memory_size_to,
                "cmd": cmd,
                "price_from": price_from,
                "price_to": price_to,
                "image_uuid": image_uuid,
            }
        }
        
        if deployment_type == "Job" and parallelism_num is not None:
            data["parallelism_num"] = parallelism_num
        elif deployment_type == "Container":
            data["container_template"]["cuda_v"] = cuda_v_from
            data["container_template"].pop("cuda_v_from", None)
            data["container_template"].pop("cuda_v_to", None)
        
        if env_vars:
            data["container_template"]["env_vars"] = env_vars
            
        response = self._make_request("POST", "/api/v1/dev/deployment", data=data)
        
        deployment_uuid = response.get("data", {}).get("deployment_uuid")
        if not deployment_uuid:
            raise AutodlNetworkError("Deployment created successfully but no UUID returned")
        
        return deployment_uuid

    def create_replicaset_deployment(self, name: str, image_uuid: str, replica_num: int = 2,
                                   gpu_name_set: Optional[List[str]] = None, gpu_num: int = 1,
                                   cuda_v_from: int = 113, cuda_v_to: int = 128,
                                   cpu_num_from: int = 1, cpu_num_to: int = 100,
                                   memory_size_from: int = 1, memory_size_to: int = 256,
                                   dc_list: Optional[List[str]] = None, cmd: str = "sleep 100",
                                   price_from: int = 10, price_to: int = 9000,
                                   reuse_container: bool = True, env_vars: Optional[Dict[str, str]] = None) -> str:
        """Create ReplicaSet type deployment"""
        return self.create_deployment(
            name=name,
            image_uuid=image_uuid,
            deployment_type="ReplicaSet",
            replica_num=replica_num,
            gpu_name_set=gpu_name_set,
            gpu_num=gpu_num,
            cuda_v_from=cuda_v_from,
            cuda_v_to=cuda_v_to,
            cpu_num_from=cpu_num_from,
            cpu_num_to=cpu_num_to,
            memory_size_from=memory_size_from,
            memory_size_to=memory_size_to,
            dc_list=dc_list,
            cmd=cmd,
            price_from=price_from,
            price_to=price_to,
            reuse_container=reuse_container,
            env_vars=env_vars
        )

    def create_job_deployment(self, name: str, image_uuid: str, replica_num: int = 4,
                            parallelism_num: int = 1, gpu_name_set: Optional[List[str]] = None,
                            gpu_num: int = 1, cuda_v_from: int = 113, cuda_v_to: int = 128,
                            cpu_num_from: int = 1, cpu_num_to: int = 100,
                            memory_size_from: int = 1, memory_size_to: int = 256,
                            dc_list: Optional[List[str]] = None, cmd: str = "sleep 10",
                            price_from: int = 10, price_to: int = 9000,
                            reuse_container: bool = True, env_vars: Optional[Dict[str, str]] = None) -> str:
        """Create Job type deployment"""
        return self.create_deployment(
            name=name,
            image_uuid=image_uuid,
            deployment_type="Job",
            replica_num=replica_num,
            parallelism_num=parallelism_num,
            gpu_name_set=gpu_name_set,
            gpu_num=gpu_num,
            cuda_v_from=cuda_v_from,
            cuda_v_to=cuda_v_to,
            cpu_num_from=cpu_num_from,
            cpu_num_to=cpu_num_to,
            memory_size_from=memory_size_from,
            memory_size_to=memory_size_to,
            dc_list=dc_list,
            cmd=cmd,
            price_from=price_from,
            price_to=price_to,
            reuse_container=reuse_container,
            env_vars=env_vars
        )

    def create_container_deployment(self, name: str, image_uuid: str,
                                  gpu_name_set: Optional[List[str]] = None, gpu_num: int = 1,
                                  cuda_v: int = 113, cpu_num_from: int = 1, cpu_num_to: int = 100,
                                  memory_size_from: int = 1, memory_size_to: int = 256,
                                  dc_list: Optional[List[str]] = None, cmd: str = "sleep 100",
                                  price_from: int = 10, price_to: int = 9000,
                                  reuse_container: bool = True, env_vars: Optional[Dict[str, str]] = None) -> str:
        """Create Container type deployment"""
        return self.create_deployment(
            name=name,
            image_uuid=image_uuid,
            deployment_type="Container",
            replica_num=1,
            gpu_name_set=gpu_name_set,
            gpu_num=gpu_num,
            cuda_v_from=cuda_v,
            cuda_v_to=cuda_v,
            cpu_num_from=cpu_num_from,
            cpu_num_to=cpu_num_to,
            memory_size_from=memory_size_from,
            memory_size_to=memory_size_to,
            dc_list=dc_list,
            cmd=cmd,
            price_from=price_from,
            price_to=price_to,
            reuse_container=reuse_container,
            env_vars=env_vars
        )

    def get_deployments(self) -> List[AutodlDeployment]:
        """Get deployment list"""
        response = self._make_request("GET", "/api/v1/dev/deployment/list")
        print(response)
        deployments = []
        for item in response.get("data", {}).get("list", []):
            deployments.append(AutodlDeployment(**item))
        return deployments

    def query_container_events(self, deployment_uuid: str,
            deployment_container_uuid: str = "",
            page_index: int = 0,
            page_size: int = 10) -> List[AutodlContainerEvent]:
        """Query container events"""
        body = {
            "deployment_uuid": deployment_uuid,
            "deployment_container_uuid": deployment_container_uuid,
            "page_index": page_index,
            "page_size": page_size,
        }
        response = self._make_request("POST", "/api/v1/dev/deployment/container/event/list", data=body)
        events = []
        for item in response.get("data", {}).get("list", []):
            events.append(AutodlContainerEvent(**item))
        return events

    def query_containers(self, deployment_uuid: str,
            deployment_container_uuid: str = "", 
            page_index: int = 1, 
            page_size: int = 100,
            date_from: str = "",
            date_to: str = "",
            gpu_name: str = "",
            cpu_num_from: int = 0,
            cpu_num_to: int = 0,
            memory_size_from: int = 0,
            memory_size_to: int = 0,
            price_from: int = 0,
            price_to: int = 0,
            released: bool = False,
            status: List[str] = ["running"]) -> List[AutodlContainer]:
        """Query containers"""
        body = {
            "deployment_uuid": deployment_uuid,
            "container_uuid": deployment_container_uuid,
            "date_from": date_from,
            "date_to": date_to,
            "gpu_name": gpu_name,
            "cpu_num_from": cpu_num_from,
            "cpu_num_to": cpu_num_to,
            "memory_size_from": memory_size_from,
            "memory_size_to": memory_size_to,
            "price_from": price_from,
            "price_to": price_to,
            "released": released,
            "status": status,
            "page_index": page_index,
            "page_size": page_size
        }
        response = self._make_request("POST", "/api/v1/dev/deployment/container/list", data=body)
        print(response['data']['list'])
        containers = []
        for item in response.get("data", {}).get("list", []):
            containers.append(AutodlContainer(**item))
            pass
        return containers

    def stop_container(self, deployment_container_uuid: str,
            decrease_one_replica_num: bool = False,
            no_cache: bool = False,
            cmd_before_shutdown: str = "sleep 5") -> bool:
        """Stop specific container"""
        data = {
            "deployment_container_uuid": deployment_container_uuid,
            "decrease_one_replica_num": decrease_one_replica_num,
            "no_cache": no_cache,
            "cmd_before_shutdown": cmd_before_shutdown
        }
        self._make_request("POST", "/api/v1/dev/deployment/container/stop", data=data)
        return True

    def set_replicas(self, deployment_uuid: str, replicas: int) -> bool:
        """Set replica count"""
        body = {
            "deployment_uuid": deployment_uuid,
            "replica_num": replicas
        }
        self._make_request("PUT", "/api/v1/dev/deployment/replica_num", data=body)
        return True

    def stop_deployment(self, deployment_uuid: str) -> bool:
        """Stop deployment"""
        data = {
            "deployment_uuid": deployment_uuid, 
            "operate": "stop"
        }
        self._make_request("PUT", "/api/v1/dev/deployment/operate", data=data)
        return True

    def delete_deployment(self, deployment_uuid: str) -> bool:
        """Delete deployment"""
        body = {
            "deployment_uuid": deployment_uuid,
        }
        self._make_request("DELETE", "/api/v1/dev/deployment", data=body)
        return True

    def set_scheduling_blacklist(self, deployment_uuid: str, 
            expire_in_minutes: int, comment: str) -> bool:
        """Set scheduling blacklist"""
        body = {
            "deployment_uuid": deployment_uuid,
            "expire_in_minutes": expire_in_minutes,
            "comment": comment
        }
        self._make_request("POST", "/api/v1/dev/deployment/scheduling/blacklist", data=body)
        return True

    def get_scheduling_blacklist(self, deployment_uuid: str) -> List[AutodlBlacklist]:
        """Get active scheduling blacklist"""
        data = self._make_request("GET", "/api/v1/dev/deployment/scheduling/blacklist").get("data", [])
        blacklist = []
        if data is None:
            return blacklist
        for item in data:
            blacklist.append(AutodlBlacklist(**item))
            pass
        return blacklist

    def get_gpu_stock_elastic(self, region_sign: str, 
            cuda_v_from: int = 117, cuda_v_to: int = 128) -> List[AutodlGpuStockElastic]:
        """Get elastic deployment GPU stock"""
        body = {
            "region_sign": region_sign,
            "cuda_v_to": cuda_v_to,
            "cuda_v_from": cuda_v_from,
        }
        response = self._make_request("POST", "/api/v1/dev/machine/region/gpu_stock", data=body)
        data = response.get("data", [])
        stocks = []
        for item in data:
            if isinstance(item, dict):
                for gpu_type, info in item.items():
                    info_flat = info.copy()
                    info_flat["gpu_type"] = gpu_type
                    stocks.append(AutodlGpuStockElastic(**info_flat))
        return stocks

    def get_ddp_overview(self, deployment_uuid: str) -> List[AutodlDdpOverview]:
        """Get DDP overview data"""
        params = {"deployment_uuid": deployment_uuid}
        response = self._make_request("GET", "/api/v1/dev/deployment/ddp/overview", params=params)
        ddp_list = []
        for item in response.get("data", []):
            ddp_list.append(AutodlDdpOverview(**item))
        return ddp_list