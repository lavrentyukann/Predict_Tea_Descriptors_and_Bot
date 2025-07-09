# Tea Recommender System & Descriptor Prediction

## 🫖 Описание / Project Overview

**RU:**
Этот проект помогает автоматизировать подбор чая на основе его описания (дескрипторов) с использованием машинного обучения. Включает парсинг данных с сайтов, предсказание ключевых характеристик чая и чат-бота для рекомендаций на основе запроса пользователя.

Проект включает **две основные задачи:**
- Дообучение модели BERT для предсказания дескрипторов чая по описанию товара.
- Создание Telegram-бота «Чайный сомелье», который рекомендует позиции из интернет-магазина чая (dao-chai.ru) на основе пользовательского запроса.

**Почему это может быть полезно?**
1. Для онлайн-магазинов чая – сокращение используемых ресурсов (особенно человеческих и временных) на разметку позиций, усовершенствование системы рекомендаций, повышение вовлеченности пользователей 
2. Для любителей чая – помощь в выборе новых сортов по описанию, вкусу, аромату или другим характеристикам
3. Для исследователей – изучение взаимосвязи между описанием чая и его восприятием человеком, изучение способов применения NLP-технологий для категоризации товарных описаний

**EN:**
This project addresses **two key tasks:**
- Fine-tuning the BERT model for predicting tea flavor descriptors based on product descriptions.
- Developing a Telegram bot named “Tea Sommelier” that recommends tea items from the dao-chai.ru online store based on user queries.

**Why is this useful?**
1. For online tea stores – Reducing the resources (especially human and time-related) needed for product tagging, improving recommendation systems, and increasing user engagement.
2. For tea enthusiasts – Helping them discover new varieties based on descriptions, taste, aroma, or other characteristics.
3. For data scientists/researchers – Studying the relationship between tea descriptions and human perception, as well as exploring NLP applications and techniques for product categorization.

## 📁 Структура репозитория / Repository Structure

| Файл / Папка            | Описание (RU)                                                                                   | Description (EN)                                                                 |
|------------------------|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `Tea_Parser.ipynb`     | Парсинг данных (описания, дескрипторы и др.) с сайта dao-chai.ru. Данные парсинга в файле daochai_parsed.xlsx                                | Data scraping from dao-chai.ru (descriptions, descriptors, etc.). Parsed data is in file daochai_parsed.xlsx   |
| `LLM_Augment_Program`   | Программа для аугментации текста с использованием LLM                           | Text augmentation scripts using LLM                                        |
| `Tea_Classifier` | Четыре версии классификатора с аугментацией: син. замена через BERT, перефразирование через gemma3:1b, обрезка токенов | Four classifier notebook versions: BERT-based synonym replacement, gemma3:1b paraphrasing, right/left token trimming |
| `Classifier_Results`  | Результаты дообучения классификатора                                            | Fine-tuned classifier results                                              |
| `Tea_Sommelier_Bot`     |  Telegram-бот «Чайный сомелье»                                                  |  The “Tea Sommelier” Telegram bot                                          |


## 🛠️ Технологии/Technologies 
Python, NLP (BERT-based models for Russian language), Scikit-learn, Machine Learning, Telegram API, Web Scrapping (BeautifulSoup)

