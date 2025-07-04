import logging
import pandas as pd
import ast


logger = logging.getLogger(__name__)


class DFPreparingService:
    def __init__(self, path_to_excel: str):
        # Загрузка данных
        self.data = pd.read_excel(path_to_excel)
        logger.debug("Загрузили файл")
        # Превратим текст из колонок в коллекции
        self.data['descriptors'] = self.data['descriptors'].apply(lambda x: ast.literal_eval(x))
        self.data['feature'] = self.data['feature'].apply(lambda x: ast.literal_eval(x))
        self.data['tea_category'] = self.data['tea_category'].apply(lambda x: ast.literal_eval(x))
        self.data['comments'] = self.data['comments'].apply(lambda x: ast.literal_eval(x))
        # Соединяем комментарии с описаниями
        self.data['description_with_comments'] = self.data.apply(DFPreparingService.__set_description_with_comments, axis=1)
        # Извлекли дескрипторы из классов
        self.data['descriptors'] = self.data['descriptors'].apply(DFPreparingService.__get_descriptors)
        # Убираем строчки с пустыми дескрипторами
        self.data = self.data[self.data['descriptors'].apply(len) > 0]
        self.data['augmented_text'] = self.data['description_with_comments']
        self.data['original'] = True
        logger.debug("Подготовили датафрейм")

    @staticmethod
    def __set_description_with_comments(df_row) -> str:
        """Объединяет основное описание чая с комментариями в одну строку"""
        try:
            # Получаем основное описание из колонок
            old_description = df_row['description']
            comments_list = df_row['comments']
            # Объединяем описание с комментариями через пробел
            return old_description + ' ' + ' '.join(comments_list)
        except Exception as e:
            logger.error(f"Ошибка объединения комментария и описания: {e}")
            # В случае ошибки возвращаем пустую строку
            return ''

    @staticmethod
    def __get_descriptors(descriptor: dict) -> list:
        """Извлекает уникальные дескрипторы из словаря категорий дескрипторов"""
        try:
            unique_descriptors = set()
            for descriptor_category in descriptor:
                for descriptor_item in descriptor[descriptor_category]:
                    unique_descriptors.add(descriptor_item)

            return list(unique_descriptors)
        except Exception as e:
            logger.error(f"Ошибка выделения дескрипторов из классов: {e}")
            # В случае ошибки возвращаем пустой список
            return []

    def get_rare_descriptor_rows(self) -> pd.DataFrame:
        """Выделяем из датафрейма редкие дескрипторы"""
        tea_df_flat = self.data.explode('descriptors')
        grouped_df = tea_df_flat.groupby('descriptors').size().reset_index(name='count')
        rare_descriptors = grouped_df[grouped_df['count'] < 10]['descriptors'].tolist()

        for_augment_df = self.data[
            self.data['descriptors'].apply(lambda x: any(item in rare_descriptors for item in x)) > 0].copy()
        logger.debug("Выделяем из датафрейма редкие дескрипторы")
        return for_augment_df

    def get_loaded_df(self) -> pd.DataFrame:
        return self.data