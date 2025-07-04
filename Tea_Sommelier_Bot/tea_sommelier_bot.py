import logging
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import re
import ast
from typing import List, Dict

logger = logging.getLogger(__name__)

class TeaSommelierBot:
    def __init__(self, excel_path:str, ollama_url: str, model_name: str):
        """
        Инициализация чайного бота
        """
        # Загрузка данных
        self.data = pd.read_excel(excel_path)

        # Преобразование available_tea в булевый тип
        self.data['available_tea'] = self.data['available_tea'].astype(bool)
        self.data['descriptors'] = self.data['descriptors'].apply(ast.literal_eval)
        self.data['feature'] = self.data['feature'].apply(ast.literal_eval)
        self.data['tea_category'] = self.data['tea_category'].apply(ast.literal_eval)
        self.data['comments'] = self.data['comments'].apply(ast.literal_eval)
        self.data['bert_descriptors'] = self.data['bert_descriptors'].apply(ast.literal_eval)

        # Инициализация модели для эмбеддингов
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Подготовка данных
        self.prepare_data()

        # Настройки Ollama
        self.ollama_url = ollama_url
        self.ollama_model = model_name

    def prepare_data(self):
        """Подготовка данных для поиска"""
        # Очистка и предобработка текстовых полей
        self.data['combined_text'] = self.data.apply(self.combine_text_fields, axis=1)

        # Создание эмбеддингов для каждого чая
        self.data['embedding'] = self.data['combined_text'].apply(
            lambda x: self.embedding_model.encode(str(x))
        )

    def combine_text_fields(self, row: pd.Series) -> str:
        """Объединение текстовых полей в один строку для поиска"""
        allText = []

        allText.append(row['title'])
        allText.append(row['description'])

        for descriptor in row['descriptors']:
            allText.append(descriptor)

        for bert_descriptor in row['bert_descriptors']:
            allText.append(bert_descriptor)

        for comment in row['comments']:
            allText.append(comment)

        for key, value in row['feature'].items():
            allText.append(key)
            allText.append(value)

        for tea_category in row['tea_category']:
            allText.append(tea_category)

        return ' '.join(allText)

    def extract_filters(self, query: str) -> Dict:
        """Извлечение фильтров из пользовательского запроса"""
        filters = {
            'category': [],
            'price_max': None,
            'descriptors': [],
            'price_min': None,
            'shipment': None,
            'province': None
        }

        # Поиск категории чая
        tea_categories = self.data['tea_category'].dropna()
        for category_row in tea_categories:
            for category in category_row:
                if category.lower() in query.lower():
                    filters['category'].append(category)

        # Поиск максимальной цены
        price_matches = re.findall(r'до (\d+)', query.lower())
        if price_matches:
            filters['price_max'] = float(price_matches[0])

        # Поиск минимальной цены
        price_matches = re.findall(r'от (\d+)', query.lower())
        if price_matches:
            filters['price_min'] = float(price_matches[0])

        # Поиск дескрипторов (ноток вкуса/аромата)
        descriptors = self.data['descriptors'].dropna()
        for desc_row in descriptors:
            for desc in desc_row:
                if desc.lower() in query.lower():
                    filters['descriptors'].append(desc)

        bert_descriptors = self.data['bert_descriptors'].dropna()
        for desc_row in bert_descriptors:
            for desc in desc_row:
                if desc.lower() in query.lower():
                    filters['descriptors'].append(desc)

        # Поиск по партии чая
        shipments = self.data['feature'].dropna()
        for shipment in shipments:
            if isinstance(shipment, dict):
                shipment_value = shipment.get('Партия:')
                if shipment_value is not None:
                    if shipment_value.lower() in query.lower():
                        filters['shipment'] = shipment_value

        # Поиск по провинции чая
        provinces = self.data['feature'].dropna()
        for province in provinces:
            if isinstance(province, dict):
                province_value = province.get('Провинция:')
                if province_value is not None:
                    if province_value.lower() in query.lower():
                        filters['province'] = province_value

        return filters

    def apply_filters(self, filters: Dict) -> pd.DataFrame:
        """Применение фильтров к данным"""
        filtered_data = self.data.copy()

        # Фильтр по доступности - сначала всегда доступные чаи
        filtered_data = filtered_data.sort_values('available_tea', ascending=False)

        # Фильтр по категории
        if filters['category']:
            filtered_data = filtered_data[filtered_data['tea_category'].apply(lambda x: any(cat.lower() in [item.lower() for item in x] for cat in filters['category']))]

        # Фильтр по цене
        if filters['price_max']:
            filtered_data = filtered_data[
                pd.to_numeric(filtered_data['price'], errors='coerce') <= filters['price_max']
            ]

        if filters['price_min']:
            filtered_data = filtered_data[
                pd.to_numeric(filtered_data['price'], errors='coerce') >= filters['price_min']
            ]

            # Фильтр по дескрипторам
        if filters['descriptors']:
            for desc in filters['descriptors']:
                filtered_data = filtered_data[
                    filtered_data['descriptors'].apply(lambda x: desc.lower() in [item.lower() for item in x]) |
                    filtered_data['bert_descriptors'].apply(lambda x: desc.lower() in [item.lower() for item in x]) |
                    filtered_data['description'].str.contains(desc, case=False, na=False) |
                    filtered_data['comments'].apply(lambda x: any(desc.lower() in str(c).lower() for c in x))
                ]

        # Фильтр по партии
        if filters['shipment']:
            filtered_data = filtered_data[
                filtered_data['feature'].apply(
                    lambda x: isinstance(x, dict) and 'Партия:' in x and filters['shipment'].lower() in x['Партия:'].lower()
                )
            ]

        # Фильтр по провинции
        if filters['province']:
            filtered_data = filtered_data[
                filtered_data['feature'].apply(
                    lambda x: isinstance(x, dict) and 'Провинция:' in x and filters['province'].lower() in x['Провинция:'].lower()
                )
            ]

        return filtered_data

    def semantic_search(self, query: str, filtered_data: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """Семантический поиск среди отфильтрованных чаев"""
        if filtered_data.empty:
            return filtered_data

        # Эмбеддинг запроса
        query_embedding = self.embedding_model.encode(query)

        # Вычисление косинусного сходства
        embeddings = np.stack(filtered_data['embedding'].values)
        similarities = np.dot(embeddings, query_embedding) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Добавление сходства в DataFrame и сортировка
        filtered_data['similarity'] = similarities

        # Сортировка сначала по доступности, затем по сходству
        filtered_data = filtered_data.sort_values(
            ['available_tea', 'similarity'],
            ascending=[False, False]
        )

        return filtered_data.head(top_n)

    def query_ollama(self, prompt: str) -> str:
        """Запрос к Ollama API"""
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            return "Извините, не могу получить ответ от модели."

    def generate_recommendation(self, query: str, recommendations: List[Dict]) -> str:
        """Генерация текста рекомендации с помощью LLM"""
        if not recommendations:
            return "К сожалению, не нашлось подходящих чаев по вашему запросу."

        # Подготовка информации о рекомендациях для промпта
        recs_text = "\n\n".join(
            f"Чай #{i + 1}:\n"
            f"Название: {rec['title']}\n"
            f"Описание: {rec['description']}\n"
            f"Дескрипторы вкуса/аромата: {rec['descriptors'].extend(rec['bert_descriptors'])}\n"
            f"Категория: {rec['tea_category']}\n"
            f"Цена: {rec['price']} руб.\n"
            f"Особенности: {rec.get('feature', 'не указаны')}\n"
            f"Доступность: {'Есть в наличии' if rec.get('available_tea', False) else 'Нет в наличии'}\n"
            f"Ссылка: {rec.get('url', 'нет ссылки')}\n"
            f"Отзывы: {rec['comments'][:3]}..."
            for i, rec in enumerate(recommendations)
        )

        # Создание промпта
        prompt = f"""
        Ты — профессиональный чайный сомелье.

        Ответь кратко и по делу на русском языке. Обращайся напрямую к собеседнику (на "вы"), не упоминай слово "пользователь" и не описывай запрос — просто сразу переходи к рекомендации.

        Вот подходящие чаи:
        {recs_text}

        Составь короткую рекомендацию (2–4 предложения), укажи 1–3 чая и объясни, почему они подойдут. Не используй ссылки, не давай длинных описаний. Пиши дружелюбно и уверенно.
        """

        return self.query_ollama(prompt)

    def recommend_tea(self, query: str, top_n: int = 3) -> Dict:
        """Основной метод для рекомендации чая"""
        # Извлечение фильтров из запроса
        filters = self.extract_filters(query)

        # Применение фильтров
        filtered_data = self.apply_filters(filters)

        # Семантический поиск среди отфильтрованных вариантов
        recommendations = self.semantic_search(query, filtered_data, top_n)

        # Конвертация рекомендаций в словари
        recs_dict = recommendations.drop(columns=['embedding', 'similarity'], errors='ignore')
        recs_dict = recs_dict.to_dict('records')

        # Генерация текста рекомендации
        recommendation_text = self.generate_recommendation(query, recs_dict)

        return {
            "recommendations": recs_dict,
            "recommendation_text": recommendation_text
        }
