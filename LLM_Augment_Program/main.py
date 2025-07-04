import logging
from df_preparing_service import DFPreparingService
from df_processing_service import DFProcessingService
import pandas as pd

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)

if __name__ == "__main__":
    path_to_excel = "../daochai_parsed.xlsx"
    preparing_service = DFPreparingService(path_to_excel)
    original_df = preparing_service.get_loaded_df()
    rare_descriptor_rows = preparing_service.get_rare_descriptor_rows()

    ollama_url = "http://localhost:8080/api/generate"
    model_name = "gemma3:1b"
    range_count = 50
    processing_service = DFProcessingService(ollama_url, model_name, range_count)
    processed_df = processing_service.processing(rare_descriptor_rows)
    processed_df_ids = processed_df["id"].unique()
    original_df = original_df[~original_df["id"].isin(processed_df_ids)]
    original_df = pd.concat([original_df, processed_df], ignore_index=True)
    original_df.to_excel("processed_df.xlsx", index=False)