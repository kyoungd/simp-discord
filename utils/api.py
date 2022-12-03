from aiohttp import ClientSession, ClientResponse
import asyncio

from utils.config import init_config

class API:
    def __init__(self, base_url, username, password, tmp_filepath='tmp.json') -> None:
        self.session: ClientSession
        self.initiated = False
        self.headers = {}
        self.username = username
        self.base_url = base_url
        self.token = None
        self.performing_login = False
        self.password = password
        self.tmp_filepath = tmp_filepath
    
    async def before_request(self):
        if not self.initiated:
            if self.headers:
                self.session = ClientSession(headers = self.headers)
            else:
                self.session = ClientSession()
            self.initiated = True
        if not self.token and  not self.performing_login:
            self.performing_login = True
            await self.login()
            self.performing_login = False
    async def get(self, url, *args, **kwargs) -> ClientResponse:
        await self.before_request()
        async with self.session.get(url, *args, **kwargs) as request:
            return await request.json(), await request.text()

    async def post(self, url, *args, **kwargs) -> ClientResponse:
        await self.before_request()
        async with self.session.post(url, *args, **kwargs) as request:
           return await request.json()
    
    async def login(self):
        data = {
        	"identifier": self.username,
        	"password": self.password
        }
        resp = await self.post(f"{self.base_url}/auth/local", json=data)
        self.token = resp['jwt']
        return resp
    
    async def get_classes(self):
        await self.before_request()
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        resp, txt = await self.get(f"{self.base_url}/get-daily-discord-room", headers=headers)
        if resp.get("error") and (resp['error']['status'] == 401 or resp['error']['status'] == 403):
            self.login()
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            resp,txt = await self.get(f"{self.base_url}/get-daily-discord-room", headers=headers)
        return init_config(txt, self.tmp_filepath)
