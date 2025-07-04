# Predict_Tea_Descriptors_plus_Bot_Project

## 🫖 Описание / Project Overview

**RU:**
Проект включает **две основные задачи:**
- Дообучение модели BERT для предсказания дескрипторов чая по описанию товара.
- Создание Telegram-бота «Чайный сомелье», который рекомендует позиции из интернет-магазина чая (dao-chai.ru) на основе пользовательского запроса.
  
**EN:**
This project addresses **two key tasks:**
- Fine-tuning the BERT model for predicting tea flavor descriptors based on product descriptions.
- Developing a Telegram bot named “Tea Sommelier” that recommends tea items from the dao-chai.ru online store based on user queries.

## 📁 Структура репозитория / Repository Structure

| Файл / Папка            | Описание (RU)                                                                                   | Description (EN)                                                                 |
|------------------------|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `Tea_Parser.ipynb`     | Парсинг данных (описания, дескрипторы и др.) с сайта dao-chai.ru. Данные парсинга в файле daochai_parsed.xlsx                                | Data scraping from dao-chai.ru (descriptions, descriptors, etc.). Parsed data is in file daochai_parsed.xlsx   |
| `Tea_Classifier` | Четыре версии классификатора с аугментацией: син. замена через BERT, перефразирование через gemma3:1b, обрезка токенов | Four classifier notebook versions: BERT-based synonym replacement, gemma3:1b paraphrasing, right/left token trimming |
| `Classifier_Results`  | Результаты дообучения классификатора                                            | Fine-tuned classifier results                                              |
| `LLM_Augment_Program`   | Программа для аугментации текста с использованием LLM                           | Text augmentation scripts using LLM                                        |
| `Tea_Sommelier_Bot`     |  Telegram-бот «Чайный сомелье»                                                  |  The “Tea Sommelier” Telegram bot                                          |




