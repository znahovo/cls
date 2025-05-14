import requests
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from typing import Optional, List

class FreeClashNodeScraper:
    def __init__(self, debug: bool = False):
        self.base_url = "https://www.freeclashnode.com"
        self.daily_url = ""
        self.debug = debug
        self.headers = {
            "Accept": "*/*",
            'Accept-Encoding': 'gzip, deflate',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Connection": "keep-alive",
        }
        self.output_dir = Path("configs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_proxies(self) -> None:
        """Fetch and save the latest Clash proxy configurations."""
        try:
            soup = self._request_home_page()
            if not soup:
                self.logger.error("Failed to fetch home page")
                return

            # Find the latest article
            latest_article = soup.find("div", id="blog-list").find("div", class_="row item py-3")
            if not latest_article:
                self.logger.error("Could not find latest article on home page")
                return

            self.daily_url = latest_article.find("a")["href"]
            self.logger.info(f"Found daily URL: {self.daily_url}")

            soup = self._request_daily_proxy_page()
            if not soup:
                self.logger.error("Failed to fetch daily proxy page")
                return

            # Find all YAML config links
            proxies = soup.find_all("p", string=lambda text: text and text.strip().endswith(".yaml"))
            self.logger.info(f"找到 {len(proxies)} 个 YAML 配置")

            v2Proxies = soup.find_all("p", string=lambda text: text and text.strip().endswith(".txt"))
            self.logger.info(f"找到 {len(v2Proxies)} 个 V2Ray 配置")
            
            
            # Clear old configs
            for old_file in self.output_dir.glob("*.yaml"):
                old_file.unlink()
            for old_file in self.output_dir.glob("*.txt"):
                old_file.unlink()
                
            for idx,p in enumerate(proxies):
                self.logger.info(f"clash {idx+1}. {p}")

            for idx,p in enumerate(v2Proxies):
                self.logger.info(f"v2ray {idx+1}. {p}")
        
            # Download new configs
            self._downloadProxies(proxies, "")
            self._downloadProxies(v2Proxies, "v")

        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}", exc_info=True)

    def _downloadProxies(self,proxies: List[str],prefixName=""):
        for idx, proxy in enumerate(proxies):
            try:
                url = proxy.text.strip()
                self.logger.info(f"从 {url} 下载")
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                file_path = self.output_dir / f"{prefixName}{idx+1}.yaml"
                with file_path.open("wb") as f:
                    f.write(response.content)
                self.logger.info(f"下载成功 {file_path}")
            except Exception as e:
                self.logger.error(f"下载失败 {idx+1}: {str(e)}")
    
    def _request_daily_proxy_page(self) -> Optional[BeautifulSoup]:
        """Request the daily proxy page."""
        if self.debug:
            return self._load_test_data("daily_proxy.html")
        
        try:
            response = requests.get(f"{self.base_url}{self.daily_url}", headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            self.logger.error(f"Failed to fetch daily proxy page: {str(e)}")
            return None

    def _request_home_page(self) -> Optional[BeautifulSoup]:
        """Request the home page."""
        if self.debug:
            return self._load_test_data("home_page.html")
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            self.logger.error(f"Failed to fetch home page: {str(e)}")
            return None

    def _load_test_data(self, filename: str) -> BeautifulSoup:
        """Load test data from file for debugging."""
        with open(filename, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")

if __name__ == "__main__":
    scraper = FreeClashNodeScraper(debug=False)
    scraper.get_proxies()
