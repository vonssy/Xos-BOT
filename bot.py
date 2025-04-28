from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from datetime import datetime
from colorama import *
import asyncio, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class XOS:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://x.ink",
            "Referer": "https://x.ink/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://api.x.ink/v1"
        self.ref_code = "1V7NKQ" # U can change it with yours.
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}XOS - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
        
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address

            return address
        except Exception as e:
            return None
    
    def generate_payload(self, account: str, address: str, message: str):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            payload = {
                "walletAddress":address,
                "signMessage":message,
                "signature":signature,
                "referrer":self.ref_code
            }
            
            return payload
        except Exception as e:
            return self.log(str(e))
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account

    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

    async def get_message(self, address: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/get-sign-message2?walletAddress={address}"
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=self.headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result['message']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def verify_signature(self, account: str, address: str, message: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/verify-signature2"
        data = json.dumps(self.generate_payload(account, address, message))
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result['token']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    async def user_data(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/me"
        headers = {
            **self.headers,
            "authorization": f"Bearer {token}"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result['data']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def claim_checkin(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/check-in"
        headers = {
            **self.headers,
            "authorization": f"Bearer {token}",
            "Content-Length": "2",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json={}) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def perform_draw(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/draw"
        headers = {
            **self.headers,
            "authorization": f"Bearer {token}",
            "Content-Length": "2",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json={}) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def process_get_nonce(self, address: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        message = None
        while message is None:
            message = await self.get_message(address, proxy)
            if not message:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} GET Nonce Failed {Style.RESET_ALL}"
                )
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
                continue
            
            return message
            
    async def process_get_token(self, account: str, address: str, use_proxy: bool):
        message = await self.process_get_nonce(address, use_proxy)
        if message:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            token = None
            while token is None:
                token = await self.verify_signature(account, address, message, proxy)
                if not token:
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                        f"{Fore.RED + Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    )
                    proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                    await asyncio.sleep(5)
                    continue

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
                )
                return token

    async def process_accounts(self, account: str, address, use_proxy: bool):
        token = await self.process_get_token(account, address, use_proxy)
        if token:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            balance = "N/A"
            current_draw = 0
            user = await self.user_data(token, proxy)
            if user:
                balance = user.get("points", 0)
                current_draw = user.get("currentDraws", 0)

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {balance} PTS {Style.RESET_ALL}"
            )

            claim = await self.claim_checkin(token, proxy)
            if claim.get("success", False):
                days = claim['check_in_count']
                reward = claim['pointsEarned']
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} Day {days} {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}Is Claimed{Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT}Reward{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {reward} PTS{Style.RESET_ALL}"
                )
            else:
                if claim.get("error") == "Already checked in today":
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                    )
                elif claim.get("error") == "Please follow Twitter or join Discord first":
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT} Not Eligible, {Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT}Connect Your X or Discord Account First{Style.RESET_ALL}"
                    )
                else:
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.RED + Style.BRIGHT} Unknown Error {Style.RESET_ALL}"
                    )

            if current_draw > 0:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Draw    :{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {current_draw} {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}Available{Style.RESET_ALL}"
                )

                count = 0
                while current_draw > 0:
                    count += 1

                    draw = await self.perform_draw(token, proxy)
                    if draw.get("message") == "Draw successful":
                        reward = draw['pointsEarned']
                        self.log(
                            f"{Fore.MAGENTA + Style.BRIGHT}    >{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {count} {Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT}Success{Style.RESET_ALL}"
                            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}Reward{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {reward} PTS {Style.RESET_ALL}"
                        )
                    else:
                        self.log(
                            f"{Fore.MAGENTA + Style.BRIGHT}    >{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {count} {Style.RESET_ALL}"
                            f"{Fore.RED + Style.BRIGHT}Failed{Style.RESET_ALL}"
                        )
                        break
            else:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Draw    :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} No Available {Style.RESET_ALL}"
                )

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            use_proxy_choice = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)

                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )
                        account = await self.process_accounts(account, address, use_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                delay = 12 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = XOS()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] XOS - BOT{Style.RESET_ALL}                                       "                              
        )