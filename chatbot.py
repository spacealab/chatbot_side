import datetime
import random
import re
import csv
import argparse
import os
import traceback
import chardet
import logging
import unittest
import requests  # برای ارتباط با API
import time
from sense_hat import SenseHat

sense = SenseHat()

# نماد شروع برنامه
start_symbol = [
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0],
    [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]
]

# نماد شروع بازی
game_start_symbol = [
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
    [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0]
]

# نماد خروج از بازی
game_exit_symbol = [
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255]
]


csv_file_path = "questionPair.csv"

if not os.path.exists(csv_file_path):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Question", "Answer1", "Answer2", "Answer3", "Answer4"])
    print(f"File '{csv_file_path}' created successfully.")


def detect_file_encoding(file_path):
    """تشخیص کدگذاری فایل CSV"""
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
        return result['encoding']


def validate_csv_path(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file path '{file_path}' does not exist.")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(
            f"Insufficient access rights for the file '{file_path}'.")
    if not file_path.endswith('.csv'):
        raise ValueError(f"The file '{file_path}' is not a CSV file.")

# آب و هوا


def get_weather(location, date=None):
    """
    Get weather information for a specific location.
    """
    try:
        api_key = "27cc3b7d2b85a843b63296207b519ca7"  # کلید API شما
        base_url = "http://api.openweathermap.org/data/2.5/weather"  # مسیر پایه API

        # حذف فضای خالی و کاراکترهای اضافی از location
        location = location.strip().replace("?", "")

        if date:  # اگر تاریخ مشخص شده باشد (نسخه پیشرفته)
            return "Historical forecasting requires the advanced version of the API."
        else:  # دریافت آب‌وهوای فعلی
            url = f"{base_url}?q={location}&appid={api_key}&units=metric"

        response = requests.get(url)
        response.raise_for_status()  # بررسی خطاهای HTTP
        data = response.json()

        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return f"Weather {location}: {weather_description} Temp {temperature} Degrees Celsius."
    except Exception as e:
        return f"Unable to receive weather information: {str(e)}"


# def load_existing_questions(csv_file_path):
#     if os.path.exists(csv_file_path):
#         try:
#             encoding = detect_file_encoding(csv_file_path)
#             with open(csv_file_path, mode='r', encoding=encoding) as file:
#                 reader = csv.DictReader(file)
#                 if 'Question' not in reader.fieldnames or 'Answer1' not in reader.fieldnames:
#                     raise ValueError(
#                         "CSV format is invalid. Missing 'Question' or 'Answer' columns.")
#                 for row in reader:
#                     question = row['Question'].strip().lower()
#                     answers = [row[col].strip() for col in [
#                         'Answer1', 'Answer2', 'Answer3', 'Answer4'] if col in row and row[col].strip()]
#                     qa_pairs[question] = answers
#         except UnicodeDecodeError:
#             print("Error: Unable to decode the file. Please check the file encoding.")
#         except ValueError as ve:
#             print(f"Error: {ve}")
#         except Exception as e:
#             print(
#                 f"An unexpected error occurred while loading the CSV file: {e}")
#             save_error_logs(str(e), traceback.format_exc())


def save_error_logs(error_message, traceback_info):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"log_{timestamp}.txt"
        traceback_filename = f"traceback_{timestamp}.txt"

        # ذخیره پیغام خطا
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write(f"Error: {error_message}\n")

        # ذخیره Stack Trace
        with open(traceback_filename, "w", encoding="utf-8") as tb_file:
            tb_file.write(traceback_info)

        print(f"Logs saved successfully to {log_filename} and {traceback_filename}.")
    except Exception as log_error:
        print(f"Failed to save logs: {log_error}")


def load_existing_questions(csv_file_path):
    if os.path.exists(csv_file_path):
        try:
            # تشخیص کدگذاری فایل
            encoding = detect_file_encoding(csv_file_path)
            # چاپ کدگذاری فایل برای اطلاعات بیشتر
            print(f"Detected file encoding: {encoding}")

            # باز کردن فایل با کدگذاری شناسایی‌شده
            with open(csv_file_path, mode='r', encoding=encoding) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    question = row['Question'].strip().lower()
                    answers = [row[col].strip() for col in ['Answer1', 'Answer2', 'Answer3', 'Answer4']if col in row and row[col].strip()]
                    qa_pairs[question] = answers
                if len(qa_pairs) < 10:
                    raise ValueError(
                        "The CSV file must contain at least 10 questions for the Trivia game.")

        except UnicodeDecodeError:
            print("Error: Unable to decode the file. Please check the file encoding.")
    else:
        print(f"File '{csv_file_path}' does not exist. Starting with an empty list of questions.")


def validate_csv_path(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file path '{file_path}' does not exist.")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(
            f"Insufficient access rights for the file '{file_path}'.")
    if not file_path.endswith('.csv'):
        raise ValueError(f"The file '{file_path}' is not a CSV file.")


def save_error_logs(error_message, traceback_info):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"log_{timestamp}.txt"
        traceback_filename = f"traceback_{timestamp}.txt"

        # Save the error message
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write(f"Error: {error_message}\n")

        # Save the traceback
        with open(traceback_filename, "w", encoding="utf-8") as tb_file:
            tb_file.write(traceback_info)

        print(f"Logs saved successfully to {log_filename} and {traceback_filename}.")
    except Exception as log_error:
        print(f"Failed to save logs: {log_error}")


# Define questions and answers
qa_pairs = {}
try:
    validate_csv_path(csv_file_path)  # بررسی مسیر و نوع فایل
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        # بررسی وجود ستون‌های ضروری
        if not reader.fieldnames or 'Question' not in reader.fieldnames:
            raise ValueError(
                "The CSV file format is unsupported or corrupted.")

        # جایگزینی لیست داخلی
        qa_pairs.clear()
        for row in reader:
            question = row['Question'].strip().lower()
            answers = [row[col].strip() for col in ['Answer1', 'Answer2', 'Answer3', 'Answer4']if col in row and row[col].strip()]
            if len(answers) > 4:
                raise ValueError(
                    f"Question '{question}' has more than 4 answers.")
            qa_pairs[question] = answers

        # بررسی تعداد سوالات
        if len(qa_pairs) < 10:
            raise ValueError(
                "The CSV file must contain at least 10 questions.")

    print(f"Successfully imported {len(qa_pairs)} questions and answers.")
except FileNotFoundError as e:
    print(f"File not found: {e}")
    save_error_logs(str(e), traceback.format_exc())
except PermissionError as e:
    print(f"Permission error: {e}")
    save_error_logs(str(e), traceback.format_exc())
except ValueError as e:
    print(f"Invalid CSV format: {e}")
    save_error_logs(str(e), traceback.format_exc())
except Exception as e:
    print("An unexpected error occurred. Please check the log files for details.")
    save_error_logs(str(e), traceback.format_exc())


# Define keyword-related questions
keyword_questions = {
    "semester": [
        "What is the start date of the semester?",
        "How many semesters are there in a year?",
        "Can I extend my semester duration?"
    ],
    "python": [
        "What is Python?",
        "How do I learn Python?",
        "What are the main features of Python?"
    ],
    "ai": [
        "What is ai?",
        "What are the types of ai?",
        "How does ai impact our daily lives?"
    ]
}

# Define question variants
question_variants = {
    "Where is lecturing hall XXX?": [
        "What is the location of lecturing hall XXX?",
        "Where is lecturing hall XXX located?",
        "How do I reach lecturing hall XXX?"
    ],
    "How do I learn Excel?": [
        "What is the best way to learn Excel?",
        "Can you tell me how to start learning Excel?"
    ],
    "What is language?": [
        "Can you explain communication?",
        "Tell me about intraction.",
        "What does contact mean?"
    ]
}

# Find the original question from variants


def find_original_question(user_input):
    for original, variants in question_variants.items():
        if user_input.strip().lower() == original.strip().lower():
            return original
        for variant in variants:
            if user_input.strip().lower() == variant.strip().lower():
                return original
    return None

# Show suggestions based on keywords


def show_suggestions(keyword):
    if keyword in keyword_questions:
        print("Here are some related questions:")
        for i, question in enumerate(keyword_questions[keyword], 1):
            print(f"{i}. {question}")

        choice = input("Select a question by typing its number: ")
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(keyword_questions[keyword]):
                selected_question = keyword_questions[keyword][choice - 1].strip(
                ).lower()
                # Fetch and return the response from qa_pairs
                if selected_question in qa_pairs:
                    # return chatbot_response(selected_question)
                    return random.choice(qa_pairs[selected_question])
                else:
                    return "I'm sorry, I don't have an answer for that question."
            else:
                return "Invalid choice. Please try again."
        else:
            return "Invalid input. Please enter a number."
    else:
        return "No related question found for this keyword."

# Respond to user questions


# def chatbot_response(user_input):
#     # لاگ کردن سوال کاربر
#     logging.info(f"User asked: {user_input}")

#     # پیدا کردن سوال اصلی (اگر وجود دارد)
#     original_question = find_original_question(user_input)
#     if original_question:
#         user_input = original_question
#         logging.info(f"Original question found: {original_question}")

#     # بررسی وجود سوال در qa_pairs
#     if user_input in qa_pairs:
#         if isinstance(qa_pairs[user_input], list):
#             response = random.choice(qa_pairs[user_input])
#         else:
#             response = qa_pairs[user_input]

#         # لاگ کردن پاسخ چتبات
#         logging.info(f"Chatbot responded: {response}")
#         return response


def chatbot_response(user_input):
    # لاگ کردن سوال کاربر
    logging.info(f"User asked: {user_input}")

    # بررسی اینکه سوال درباره مکان است یا خیر
    if "where is" in user_input.lower() or "location of" in user_input.lower():
        location_match = re.search(
            r"location of (.+)|where is (.+)", user_input, re.IGNORECASE)
        if location_match:
            location = location_match.group(1) or location_match.group(2)
            weather_info = get_weather(location.strip())
            return f"The location {location.strip()} is unavailable in the system. {weather_info}"

    # پیدا کردن سوال اصلی (اگر وجود دارد)
    original_question = find_original_question(user_input)
    if original_question:
        user_input = original_question
        logging.info(f"Original question found: {original_question}")

    # بررسی وجود سوال در qa_pairs
    if user_input in qa_pairs:
        if isinstance(qa_pairs[user_input], list):
            response = random.choice(qa_pairs[user_input])
        else:
            response = qa_pairs[user_input]

        # لاگ کردن پاسخ چت‌بات
        logging.info(f"Chatbot responded: {response}")
        return response

        # اگر سوالی پیدا نشد
        return "I'm sorry, I don't know the answer to that."

    # پاسخ به سلام و احوال‌پرسی
    elif "hello" in user_input.lower():
        response = "Hello! How can I assist you today?"
        logging.info(f"Chatbot responded: {response}")
        return response

    elif "how are you?" in user_input.lower():
        response = "I'm here to help you! How can I assist you?"
        logging.info(f"Chatbot responded: {response}")
        return response

    elif "bye" in user_input.lower():
        response = "Goodbye! Have a great day!"
        logging.info(f"Chatbot responded: {response}")
        return response

    # اگر پاسخ مناسبی پیدا نشد
    else:
        logging.warning(f"No answer found for: {user_input}")
        return "I'm sorry, I don't know the answer to that."
# Split compound questions

# Game


def start_trivia():
    show_game_start_symbol()
    """Starts the trivia game."""
    print("Trivia game activated! Answer the following questions:")
    score = 0
    total_questions = 10
    questions = random.sample(list(qa_pairs.keys()),min(total_questions, len(qa_pairs)))

    for index, question in enumerate(questions, 1):
        print(f"Q{index}: {question}")
        options = qa_pairs[question]
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        try:
            user_answer = int(input("Choose the correct option (1-4): "))
            # Assuming first option is correct
            if options[user_answer - 1].lower() == options[0].lower():
                print("Correct!")
                score += 1
            else:
                print(f"Wrong! The correct answer is: {options[0]}")
        except (ValueError, IndexError):
            print(f"Invalid input. The correct answer is: {options[0]}")

    print(f"Trivia game over! Your score: {score}/{total_questions}")
    show_game_exit_symbol(score)

def split_question(user_input):
    user_input = re.sub(r'^(hi|hello|hey), ?', '',
                        user_input.strip(), flags=re.IGNORECASE)
    questions = re.split(r'\?\s*(?:and|or)?\s*', user_input)
    questions = [q.strip() + '?' for q in questions if q.strip()]
    return questions

# Handle compound questions


def handle_compound_question(user_input):
    questions = split_question(user_input)
    if not questions:
        return "I couldn't identify any valid questions in your input."
    responses = []
    for question in questions:
        question_response = chatbot_response(question)
        responses.append(f"Q: {question} A: {question_response}")
    return "\n".join(responses)


def save_to_csv(csv_file_path, qa_pairs):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # تعیین تعداد حداکثری ستون‌ها
        max_answers = max(len(answers) for answers in qa_pairs.values())
        header = ["Question"] + [f"Answer{i+1}" for i in range(max_answers)]

        # نوشتن هدر
        writer.writerow(header)

        # نوشتن سوالات و پاسخ‌ها
        for question, answers in qa_pairs.items():
            while len(answers) < max_answers:
                answers.append("")  # پر کردن ستون‌های خالی
            writer.writerow([question] + answers)

    print(f"Data successfully saved to {csv_file_path}")


def handle_error(message):
    """چاپ پیام خطا و خروج از برنامه"""
    print(f"Error: {message}")
    exit()


def add_question(question, answer):
    # Load existing questions from CSV
    load_existing_questions(csv_file_path)

    # استانداردسازی ورودی‌ها
    question = question.strip().lower()
    answer = answer.strip()

    # بررسی اینکه سوال از قبل وجود دارد یا خیر
    if question in qa_pairs:
        if answer not in qa_pairs[question]:
            qa_pairs[question].append(answer)  # افزودن پاسخ جدید به سوال موجود
            print(f"Added answer '{answer}' to existing question: '{question}'")
        else:
            print(f"The answer '{answer}' already exists for question: '{question}'")
    else:
        qa_pairs[question] = [answer]  # ایجاد سوال جدید با پاسخ
        print(f"Added new question: '{question}' with answer: '{answer}'")

    # ذخیره به فایل CSV
    save_to_csv(csv_file_path, qa_pairs)

    # بررسی اینکه سوال از قبل وجود دارد یا خیر
    if question in qa_pairs:
        if answer not in qa_pairs[question]:
            qa_pairs[question].append(answer)  # افزودن پاسخ جدید به سوال موجود
            print(f"Added answer '{answer}' to existing question: '{question}'")
        else:
            print(f"The answer '{answer}' already exists for question: '{question}'")
    else:
        qa_pairs[question] = [answer]  # ایجاد سوال جدید با پاسخ
        print(f"Added new question: '{question}' with answer: '{answer}'")

    # ذخیره به فایل CSV
    save_to_csv(csv_file_path, qa_pairs)


def handle_error(message):
    print(f"Error: {message}")
    exit()


def remove_question(question):
    question = question.strip().lower()

    if question in qa_pairs:
        del qa_pairs[question]
        print(f"Removed question: '{question}'")
        save_to_csv(csv_file_path, qa_pairs)
    else:
        print(f"Error: The question '{question}' does not exist.")


def add_answer(csv_file_path, question, answer):
    question = question.lower().strip()
    if question in qa_pairs:
        if answer not in qa_pairs[question]:
            qa_pairs[question].append(answer)
            print(f"Added answer '{answer}' to question: '{question}'")
        else:
            print(f"The answer '{answer}' already exists for question: '{question}'")
    else:
        # If the question doesn't exist, create it with the new answer
        qa_pairs[question] = [answer]
        print(f"Added new question '{question}' with answer '{answer}'")
    save_to_csv(csv_file_path, qa_pairs)


def remove_answer(csv_file_path, question, answer):
    question = question.lower().strip()
    if question in qa_pairs:
        if answer in qa_pairs[question]:
            qa_pairs[question].remove(answer)
            print(f"Removed answer '{answer}' from question: '{question}'")
        else:
            print(f"The answer '{answer}' does not exist for question: '{question}' ")
    else:
        print(f"The question '{question}' does not exist.")
    save_to_csv(csv_file_path, qa_pairs)


def read_logs():
    log_filename = "log.txt"
    traceback_filename = "traceback.txt"

    try:
        with open(log_filename, "r") as log_file:
            log_content = log_file.read()
        with open(traceback_filename, "r") as tb_file:
            traceback_content = tb_file.read()

        print("Log Content:")
        print(log_content)
        print("\nTraceback Content:")
        print(traceback_content)
    # except FileNotFoundError:
        # print("Log or traceback file not found.")
    except FileNotFoundError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
        
def show_start_symbol():
    sense.set_pixels(start_symbol)

def show_game_start_symbol():
    sense.set_pixels(game_start_symbol)

def show_game_exit_symbol(score):
    sense.show_message(f"Score: {score}", scroll_speed=0.1)
    sense.set_pixels(game_exit_symbol)


parser = argparse.ArgumentParser(
    description="ChatBot Command Line Tool: Manage questions and answers via CLI.",
    epilog="Example usage: python chatbot.py --add --question 'What is AI?' --answer 'Artificial Intelligence'"
)

parser.add_argument('--debug', action='store_true',
                    help="Enable debug mode for detailed output.")
parser.add_argument('--view-logs', action='store_true',
                    help="View the log and traceback files.")
parser.add_argument('--list-questions', action='store_true',
                    help="List all internal questions.")
parser.add_argument('--log-mode', action='store_true',
                    help="Enable logging mode to save logs to a file.")
parser.add_argument('--log-level', type=str, choices=['INFO', 'WARNING'], default='WARNING',
                    help="Set the logging level (INFO or WARNING). Default is WARNING.")
parser.add_argument('--add', action='store_true',
                    help="Add a new question and answer to the internal list.")
parser.add_argument('--remove', action='store_true',
                    help="Remove a question from the internal list.")
parser.add_argument('--question', type=str,
                    help="Specify the question to add or remove.")
parser.add_argument('--answer', type=str,
                    help="Specify the answer when adding a question.")
parser.add_argument('--import-file', action='store_true',
                    help="Import questions and answers from a CSV file.")
parser.add_argument('--filetype', type=str,
                    help="Specify the type of the file to import (e.g., CSV).")
parser.add_argument('--filepath', type=str,
                    help="Specify the path to the file to import.")
parser.add_argument('--test', action='store_true', help="Run unit tests.")

parser.add_argument('--monitor', action='store_true',
                    help="Enable temperature monitoring.")


# args = parser.parse_args()
"""
try:
    args = parser.parse_args()
except argparse.ArgumentError as e:
    print(f"Error: {e}")
    parser.print_help()
    exit(1)
"""
try:
    args = parser.parse_args()
except SystemExit:
    print("Invalid argument provided. Use '--help' to see the list of valid arguments.")
    parser.print_help()
    exit(1)

if '--help' in vars(args):
    parser.print_help()
    exit(0)


if args.debug:
    print("Debug mode is enabled.")

if args.import_file:
    if args.filetype.lower() != "csv":
        error_message = "Error: Only CSV filetype is supported."
        traceback_info = "Unsupported file type provided for import."
        print(error_message)
        save_error_logs(error_message, traceback_info)
        exit()

    try:
        validate_csv_path(args.filepath)  # Check file path and access
        with open(args.filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Check for required columns
            if not reader.fieldnames or 'Question' not in reader.fieldnames:
                raise ValueError(
                    "The CSV file format is unsupported or missing required columns.")

            # Process the file
            qa_pairs.clear()
            for row in reader:
                question = row['Question'].strip().lower()
                answers = [row[col].strip() for col in [
                    'Answer1', 'Answer2', 'Answer3', 'Answer4'] if col in row and row[col].strip()]
                qa_pairs[question] = answers

            print(f"Successfully imported {len(qa_pairs)} questions and answers from {args.filepath}.")

    except FileNotFoundError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    except PermissionError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    except ValueError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    except csv.Error as e:
        error_message = "The CSV file is corrupted and cannot be processed."
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    except Exception as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    exit()


if args.view_logs:
    read_logs()
    exit()


def e_logging(log_mode, log_level):
    if log_mode:
        logging.basicConfig(
            filename='app.log',
            level=logging.INFO if log_level == 'INFO' else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    else:
        # غیرفعال کردن لاگ‌گیری اگر log-mode فعال نباشد
        logging.disable(logging.CRITICAL)


def add_answer(csv_file_path, question, answer):
    load_existing_questions(csv_file_path)
    question = question.lower().strip()
    answer = answer.strip()
    if question in qa_pairs:
        if answer not in qa_pairs[question]:
            qa_pairs[question].append(answer)
            print(f"Added answer '{answer}' to question: '{question}'")
        else:
            print(f"The answer '{answer}' already exists for question: '{question}'")
    else:
        qa_pairs[question] = [answer]
        print(f"Added new question '{question}' with answer '{answer}'")
    save_to_csv(csv_file_path, qa_pairs)

# کد اصلی برنامه
# def remove_answer(csv_file_path, question, answer):
#     load_existing_questions(csv_file_path)
#     question = question.lower().strip()
#     answer = answer.strip()
#     if question in qa_pairs:
#         if answer in qa_pairs[question]:
#             qa_pairs[question].remove(answer)
#             print(f"Removed answer '{answer}' from question: '{question}'")
#             if not qa_pairs[question]:
#                 del qa_pairs[question]
#                 print(f"Removed question '{question}' as it had no more answers.")
#         else:
#             print(f"The answer '{answer}' does not exist for question: '{question}'")
#     else:
#         print(f"The question '{question}' does not exist.")
#     save_to_csv(csv_file_path, qa_pairs)

# کد برنامه جانبی


def remove_answer(csv_file_path, question, answer):
    load_existing_questions(csv_file_path)
    answer = answer.strip()

    # اگر سوال مشخص نشده باشد، سوال مربوط به پاسخ را پیدا کن
    if not question or question.strip() == "":
        question_found = None
        for q, answers in qa_pairs.items():
            if answer in answers:
                question_found = q
                break

        if not question_found:
            print(
                f"Error: No question found containing the answer '{answer}'.")
            return
        question = question_found

    # حالا حذف پاسخ از سوال مشخص‌شده
    question = question.lower().strip()
    if question in qa_pairs:
        if answer in qa_pairs[question]:
            qa_pairs[question].remove(answer)
            print(f"Removed answer '{answer}' from question: '{question}'")
            if not qa_pairs[question]:  # اگر دیگر جوابی نمانده، سوال را نیز حذف کن
                del qa_pairs[question]
                print(f"Removed question '{question}' as it had no more answers.")
        else:
            print(f"Error: The answer '{answer}' does not exist for question: '{question}'")
    else:
        print(f"Error: The question '{question}' does not exist.")

    save_to_csv(csv_file_path, qa_pairs)


"""
if args.add:
    if args.question and args.answer:
        question = args.question.strip().lower()
        answer = args.answer.strip()

        # افزودن یا به‌روزرسانی سوال
        if question in qa_pairs:
            if answer not in qa_pairs[question]:
                qa_pairs[question].append(answer)
                print(f"Added answer '{answer}' to existing question: '{question}'")
            else:
                print(f"The answer '{answer}' already exists for question: '{question}'")
        else:
            qa_pairs[question] = [answer]
            print(f"Added new question: '{question}' with answer: '{answer}'")

        # ذخیره تغییرات
        save_to_csv(csv_file_path, qa_pairs)
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()

    # اضافه کردن سوال و پاسخ به لیست
    if args.question in qa_pairs:
        print(f"Question '{args.question}' already exists.")
    else:
        qa_pairs[args.question] = answers
        print(f"Added question: '{args.question}' with answer: '{args.answer}'")

    save_to_csv('questionPair.csv', qa_pairs)

    # توقف برنامه
    exit()

if args.remove:
    if args.question:
        question = args.question.strip().lower()

        # حذف سوال
        if question in qa_pairs:
            del qa_pairs[question]
            print(f"Removed question: '{question}'")
            save_to_csv(csv_file_path, qa_pairs)
        else:
            print(f"Error: The question '{question}' does not exist.")
    else:
        print("Error: --question must be specified when using --remove.")
    exit()
"""

if args.add:
    if args.question and args.answer:
        add_question(args.question, args.answer)
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()

# کد اصلی برنامه
# if args.remove:
#     if args.question:
#         remove_question(args.question)
#     else:
#         handle_error("--question must be specified when using --remove.")
#     exit()


if args.list_questions:
    print("Listing all internal questions:\n")

    # From qa_pairs
    print("Questions from CSV:")
    for question in qa_pairs.keys():
        print(f"- {question}")

    # From keyword_questions
    print("\nKeyword-based questions:")
    for keyword, questions in keyword_questions.items():
        print(f"\nKeyword: {keyword}")
        for question in questions:
            print(f"  - {question}")

    # Exit the program after printing questions
    exit()
if args.add:
    if args.question and args.answer:
        add_answer(csv_file_path, args.question, args.answer)
    else:
        handle_error(
            "Both --question and --answer must be specified when using --add.")
# کد اصلی
# if args.remove:
#     if args.question and args.answer:
#         remove_answer(csv_file_path, args.question, args.answer)
#     else:
#         handle_error("Both --question and --answer must be specified when using --remove.")

# کد برنامه جانبی
if args.remove:
    if args.answer:  # فقط بررسی می‌کند که پاسخ مشخص شده باشد
        # اگر سوال مشخص نشده باشد، مقدار خالی ارسال کن
        question = args.question if args.question else ""
        remove_answer(csv_file_path, question, args.answer)
    else:
        handle_error("--answer must be specified when using --remove.")


class TestChatbot(unittest.TestCase):

    def setUp(self):
        # ایجاد یک فایل CSV موقت برای تست
        self.test_csv_file = "test_questionPair.csv"
        with open(self.test_csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Question", "Answer1", "Answer2", "Answer3", "Answer4"])
            writer.writerow(
                ["what is python?", "Python is a programming language.", "", "", ""])

    def tearDown(self):
        # حذف فایل CSV موقت بعد از اتمام تست
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)

    # def test_chatbot_response(self):
    #     # تست پاسخ‌دهی چتبات
    #     response = chatbot_response("What is Python?")
    #     self.assertIn(response, ["Python is a programming language."])

    def test_add_question(self):
        # تست اضافه کردن سوال جدید
        add_question("What is AI?", "AI stands for Artificial Intelligence.")
        self.assertIn("what is ai?", qa_pairs)
        self.assertIn("AI stands for Artificial Intelligence.",qa_pairs["what is ai?"])

    def test_remove_question(self):
        # تست حذف سوال
        add_question("What is AI?", "AI stands for Artificial Intelligence.")
        remove_question("What is AI?")
        self.assertNotIn("what is ai?", qa_pairs)

    def test_load_existing_questions(self):
        # تست بارگذاری سوالات از فایل CSV
        load_existing_questions(self.test_csv_file)
        self.assertIn("what is python?", qa_pairs)
        self.assertIn("Python is a programming language.",qa_pairs["what is python?"])


temperature_data = {"local": [], "forecast": []}


def record_temperature(sensor_temp, forecast_temp):
    """
    ثبت دمای محلی و پیش‌بینی‌شده
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temperature_data["local"].append(
        {"time": current_time, "temp": sensor_temp})
    temperature_data["forecast"].append(
        {"time": current_time, "temp": forecast_temp})

    # نگه داشتن فقط 3 روز اخیر
    three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
    temperature_data["local"] = [
        entry for entry in temperature_data["local"]
        if datetime.datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S") > three_days_ago
    ]
    temperature_data["forecast"] = [
        entry for entry in temperature_data["forecast"]
        if datetime.datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S") > three_days_ago
    ]


def calculate_temperature_changes():
    """
    محاسبه تغییرات دما برای 3 روز اخیر
    """
    local_changes = [
        abs(temperature_data["local"][i]["temp"] -
            temperature_data["local"][i-1]["temp"])
        for i in range(1, len(temperature_data["local"]))
    ]
    forecast_changes = [
        abs(temperature_data["forecast"][i]["temp"] -
            temperature_data["forecast"][i-1]["temp"])
        for i in range(1, len(temperature_data["forecast"]))
    ]
    return local_changes, forecast_changes


def simulate_temperatures():
    """
    شبیه‌سازی دماهای حسگر و پیش‌بینی‌شده
    """
    sensor_temp = random.uniform(15.0, 30.0)
    forecast_temp = random.uniform(15.0, 30.0)
    return sensor_temp, forecast_temp


if __name__ == '__main__':
    show_start_symbol()
    e_logging(args.log_mode, args.log_level)


if args.monitor:
    print("Temperature monitoring started. Type 'stop' to terminate.")
    try:
        while True:
            # شبیه‌سازی دما یا داده‌های واقعی
            sensor_temp, forecast_temp = simulate_temperatures()
            record_temperature(sensor_temp, forecast_temp)
            local_changes, forecast_changes = calculate_temperature_changes()

            # نمایش خروجی
            print("Temperature changes (last 3 days):")
            print(f"Local Sensor: {local_changes}")
            print(f"Weather Forecast: {forecast_changes}")

            # توقف با ورودی کاربر
            user_input = input(
                "Type 'stop' to terminate or press Enter to continue: ").strip().lower()
            if user_input == "stop":
                print("Monitoring stopped.")
                break

            time.sleep(5)  # هر 5 ثانیه برای تست (برای حالت واقعی: 1800 ثانیه)
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user.")
else:
    print("Hello! You can ask me questions. Type 'exit' to stop.")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            elif user_input.lower() == "trivia":
                start_trivia()
                continue

            response = chatbot_response(user_input)
            print(f"Chatbot: {response}")
        except KeyboardInterrupt:
            print("\nChatbot interaction stopped by user.")
            break