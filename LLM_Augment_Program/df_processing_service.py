import logging
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class DFProcessingService:
    def __init__(self, ollama_url: str, model_name: str, range_count: int):
        # Настройки Ollama
        self.ollama_url = ollama_url
        self.ollama_model = model_name
        self.range_count = range_count
        self.session = self.__create_retry_session()

    def processing(self, for_augment_df: pd.DataFrame) -> pd.DataFrame:
        augment_df = for_augment_df.copy()
        augment_df['augmented'] = False
        for i in range(self.range_count):
            i_for_log = i + 1
            logger.debug(f'Обрабатываем range: {i_for_log}')
            augment_df_for_processing = augment_df[augment_df['augmented'] == False]
            augment_new_rows_list: [pd.DataFrame] = self.__processing_range(augment_df_for_processing)
            augment_df['augmented'] = True
            for augment_new_row in augment_new_rows_list:
                augment_df = pd.concat( [augment_df, augment_new_row], ignore_index=True)
        return augment_df

    def __processing_range(self, augment_df_for_processing: pd.DataFrame) -> [pd.DataFrame]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(self.__processing_row, idx, row, augment_df_for_processing.columns)
                for idx, row in augment_df_for_processing.iterrows()
            ]
            dfs = [f.result() for f in tqdm(as_completed(futures), total=len(futures))]
        return dfs

    def __processing_row(self, index: int, augment_row: pd.Series, columns: pd.Index):
        current_pd = pd.DataFrame(columns=columns)
        current_pd.loc[len(current_pd)] = augment_row.copy()
        current_pd['augmented_text'] = current_pd['description'].apply(lambda x: self.__request_to_gpt(x))
        current_pd['original'] = False
        return current_pd

    def __request_to_gpt(self, text: str) -> str:

        # Создание промпта
        prompt = f"""
                У меня есть описание чая с комментариями. Не добавляй новых комментариев. Перефразируй текст, не теряя смысла.
                Сделай текст более выразительным и литературным. 
                Выводи только финальный текст на русском языке без форматирования. Вот исходный текст:
                "{text[:5363]}"
                """

        """Запрос к Ollama API"""
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = self.session.post(self.ollama_url, json=payload, timeout=600)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            return "Ошибка обработки данных их GPT"

    def __create_retry_session(self, total_retries=3, backoff_factor=1.0) -> requests.Session:
        retry = Retry(
            total=total_retries,
            read=total_retries,
            connect=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=frozenset(['POST']),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

