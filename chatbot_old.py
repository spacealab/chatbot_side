import datetime
import random
import re
import csv
import argparse
import os
import traceback
from pymongo import MongoClient
import unittest
import sys 
import logging


client = MongoClient("mongodb://localhost:27017/")
db = client["chatbot_db"]
collection = db["questions_answers"]

csv_file_path = "questionPair.csv"

def print_help():
    help_text = """
ChatBot Command Line Tool

Usage:
  python3 chatbot.py [OPTIONS]

Options:
  --help                Show this help message and exit.
  --log-mode            Enable logging mode.
  --log-level LEVEL     Set the logging level (INFO or WARNING). Default is WARNING.
  --import-file         Import questions and answers from a CSV file.
  --filetype TYPE       Specify the type of the file to import (e.g., CSV).
  --filepath PATH       Specify the path to the file to import.
  --add                 Add a new question and answer to the internal list.
  --question QUESTION   Specify the question to add or remove or ask the chatbot.
  --answer ANSWER       Specify the answer when adding a question.
  --remove              Remove a question from the internal list.
  --remove-answer ANSWER  Specify the answer to remove from the question.
  --remove-tag TAG      Specify the tag to remove from the question.
  --remove-variant VARIANT  Specify the variant to remove from the question.
  --list-questions      List all internal questions.
  --view-logs           View the log and traceback files.
  --test                Run unit tests.

Examples:
  python3 chatbot.py --add --question "What is Python?" --answer "A programming language."
  python3 chatbot.py --import-file --filetype csv --filepath questionPair.csv
  python3 chatbot.py --log-mode --log-level INFO
    """
    print(help_text)

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

# Find the original question from variants
def find_original_question(user_input):
    # جستجو در سوال اصلی و تنوع‌ها
    doc = collection.find_one({
        "$or": [
            {"question": user_input.strip().lower()},
            {"variants": {"$in": [user_input.strip().lower()]}}
        ]
    })
    return doc

# Show suggestions based on keywords
def show_suggestions(keyword):
    docs = collection.find({"tags": keyword})
    questions = [doc["question"] for doc in docs]
    if questions:
        print("Here are some related questions:")
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
        choice = input("Select a question by typing its number: ")
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(questions):
                return questions[choice - 1]
        return "Invalid choice. Please try again."
    else:
        return f"No related questions found for keyword '{keyword}'."

# Respond to user questions
def chatbot_response(user_input, answer=None, variants=None, tags=None):
    try:
        logging.info(f"Searching for answer to: {user_input}")
        # جستجوی سؤال در پایگاه داده
        doc = collection.find_one({
            "$or": [
                {"question": user_input.strip().lower()},
                {"variants": {"$in": [user_input.strip().lower()]}}
            ]
        })

        if not doc:
            logging.warning(f"No document found for input: {user_input}")
            print(f"Document not found for input: {user_input.strip().lower()}")
            
            # اضافه کردن سؤال جدید به پایگاه داده
            new_doc = {
                "question": user_input.strip().lower(),
                "variants": [variant.strip().lower() for variant in (variants or [])],  # اضافه کردن variants
                "answers": [answer.strip()] if answer else [],  # اضافه کردن پاسخ اگر وجود داشت
                "tags": [tag.strip().lower() for tag in (tags or [])],  # اضافه کردن tags
                "created_at": datetime.datetime.now()
            }
            collection.insert_one(new_doc)  # ذخیره سؤال در دیتابیس

            if answer or variants or tags:
                return f"This question was not in the database. I have added it with the provided details."
            else:
                return "This question was not in the database. I have added it for future use, but it currently has no details."

        # اگر سندی پیدا شد
        if doc:
            update_required = False  # پرچم برای آپدیت پایگاه داده

            # اگر پاسخ جدید ارائه شده و قبلاً در لیست پاسخ‌ها وجود نداشته باشد
            if answer and answer.strip() not in doc.get("answers", []):
                doc["answers"].append(answer.strip())
                update_required = True

            # اگر variant جدید ارائه شده و قبلاً در لیست variants وجود نداشته باشد
            if variants:
                for variant in variants:
                    if variant.strip().lower() not in doc.get("variants", []):
                        doc["variants"].append(variant.strip().lower())
                        update_required = True

            # اگر tag جدید ارائه شده و قبلاً در لیست tags وجود نداشته باشد
            if tags:
                for tag in tags:
                    if tag.strip().lower() not in doc.get("tags", []):
                        doc["tags"].append(tag.strip().lower())
                        update_required = True

            # به‌روزرسانی سند در پایگاه داده در صورت نیاز
            if update_required:
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"answers": doc["answers"], "variants": doc["variants"], "tags": doc["tags"]}}
                )
                return f"The details have been updated for the existing question."

            # اگر همه جزئیات موجود باشند
            if doc["answers"]:
                return random.choice(doc["answers"])
            else:
                return "I'm sorry, I don't have an answer for that right now. You can provide one to add."

        # شرط اضافی برای اطمینان
        return "I'm sorry, I couldn't find an answer for your question. Please try asking something else."

    except Exception as e:
        # ثبت خطا و نمایش پیام عمومی
        error_message = str(e)
        traceback_info = traceback.format_exc()
        save_error_logs(error_message, traceback_info)
        return "An unexpected error occurred. Please try again later."

# Split compound questions
def split_question(user_input):
    # Remove initial greetings like "hi", "hello", or "hey"
    user_input = re.sub(r'^(hi|hello|hey),?', '', user_input.strip(), flags=re.IGNORECASE)
    
    # Split the input into questions using keywords "and", "or", or question marks
    questions = re.split(r'\?\s*(?:and|or)?\s*', user_input)
    
    # Remove empty questions from the list and add a question mark at the end of each question
    questions = [q.strip() + '?' for q in questions if q.strip()]
    
    return questions

# Handle compound questions
def handle_compound_question(user_input):
    # Split the input into individual questions
    questions = split_question(user_input)
    
    # If no valid questions are found
    if not questions:
        return "I couldn't identify any valid questions in your input."
    
    # Process each question and generate a response
    responses = []
    for question in questions:
        if question.strip():  # Check that the question is not empty
            question_response = chatbot_response(question.strip())
            responses.append(f"Q: {question} A: {question_response}")
    
    # Combine responses into a single string
    return "\n".join(responses)

def export_mongo_to_csv(csv_file_path):
    import csv
    
    # Read all documents from the database
    docs = collection.find()  # collection: questions_answers collection in MongoDB

    # Determine the maximum number of answers in all documents
    max_answers = 0
    all_docs = list(docs)  # Convert Cursor to a list
    for d in all_docs:
        if "answers" in d and len(d["answers"]) > max_answers:
            max_answers = len(d["answers"])
    header = ["Question"] + [f"Answer{i+1}" for i in range(max_answers)]

    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for d in all_docs:
            question = d["question"]
            answers = d["answers"] if "answers" in d else []
            # If the number of answers is less than max_answers, fill with empty values
            while len(answers) < max_answers:
                answers.append("")
            row = [question] + answers
            writer.writerow(row)

    print(f"Data successfully exported from MongoDB to {csv_file_path}.")

def add_question(question, answers_list):
    question_lower = question.strip().lower()
    existing_doc = collection.find_one({"question": question_lower})
    
    if existing_doc:
        # If the question exists, add the answers to the existing list
        for answer in answers_list:
            if answer not in existing_doc["answers"]:
                existing_doc["answers"].append(answer)
        
        # Update the document in the database
        collection.update_one(
            {"_id": existing_doc["_id"]},
            {"$set": {"answers": existing_doc["answers"]}}
        )
        print(f"Updated question '{question}' with new answers: {answers_list}")
    else:
        # If the question does not exist, add a new question and answers
        doc = {
            "question": question_lower,
            "answers": answers_list
        }
        collection.insert_one(doc)
        print(f"Added new question '{question}' with answers {answers_list} to MongoDB.")

def remove_question(question):
    question_lower = question.strip().lower()
    result = collection.delete_one({"question": question_lower})
    if result.deleted_count > 0:
        print(f"Removed question: '{question}' from MongoDB.")
    else:
        print(f"The question '{question}' does not exist in database.")

def add_answer(question, new_answer):
    question_lower = question.strip().lower()
    doc = collection.find_one({"question": question_lower})
    if not doc:
        # If the question does not exist, add a new question and answer
        doc = {
            "question": question_lower,
            "answers": [new_answer],
            "tags": []  # You can also add tags here if needed
        }
        collection.insert_one(doc)
        print(f"Added new question '{question}' with answer '{new_answer}' to MongoDB.")
    else:
        # If the question exists
        if new_answer in doc["answers"]:
            # If the answer already exists
            print(f"The answer '{new_answer}' already exists for question '{question}'. No changes made.")
        else:
            # If the answer is new, add it
            doc["answers"].append(new_answer)
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"answers": doc["answers"]}}
            )
            print(f"Added new answer '{new_answer}' to existing question '{question}'.")

def remove_answer(question, answer):
    question_lower = question.strip().lower()
    doc = collection.find_one({"question": question_lower})
    if not doc:
        print(f"The question '{question}' does not exist in database.")
    else:
        if answer in doc["answers"]:
            doc["answers"].remove(answer)
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"answers": doc["answers"]}}
            )
            print(f"Removed answer '{answer}' from question '{question}'.")
        else:
            print(f"The answer '{answer}' does not exist for question '{question}'.")

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
    #except FileNotFoundError:
        #print("Log or traceback file not found.")
    except FileNotFoundError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)

def import_csv_to_mongo(csv_path):
    logging.info(f"Importing data from CSV file: {csv_path}")
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # بررسی تعداد سوالات در فایل CSV
            rows = list(reader)
            if len(rows) < 10:
                logging.warning("The CSV file must contain at least 10 Q&A entries.")
                raise ValueError("The CSV file must contain at least 10 Q&A entries.")
            
            for row in rows:
                # 1) Extract fields from the CSV file
                question_text = row['question'].strip().lower()
                variants_str = row.get('variants', '').strip()  # New field for variants
                answers_str = row.get('answers', '').strip()
                tags_str = row.get('tags', '').strip()
                created_at_value = row.get('created_at', '').strip()

                # 2) Convert answers to a list
                answers_list = [ans.strip() for ans in answers_str.split(';') if ans.strip()]
                
                # بررسی تعداد پاسخ‌ها
                if len(answers_list) > 4:
                    logging.warning(f"Each question can have a maximum of 4 answers. Question: '{question_text}' has {len(answers_list)} answers.")
                    raise ValueError(f"Each question can have a maximum of 4 answers. Question: '{question_text}' has {len(answers_list)} answers.")

                # 3) Convert tags to a list
                tags_list = [tag.strip() for tag in tags_str.split(';') if tag.strip()]

                # 4) Convert variants to a list
                variants_list = [variant.strip().lower() for variant in variants_str.split(';') if variant.strip()]

                # 5) Handle created_at field
                if not created_at_value:
                    created_at_value = datetime.datetime.now()
                else:
                    try:
                        created_at_value = datetime.datetime.strptime(created_at_value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        logging.warning(f"Invalid date format for question: '{question_text}'. Using current time.")
                        created_at_value = datetime.datetime.now()

                # 6) Check if the question already exists in the database
                existing_doc = collection.find_one({"question": question_text})

                if existing_doc:
                    # Update the existing document
                    existing_answers = set(existing_doc.get("answers", []))
                    existing_tags = set(existing_doc.get("tags", []))
                    existing_variants = set(existing_doc.get("variants", []))

                    # Add new answers, tags, and variants
                    updated_answers = list(existing_answers.union(answers_list))
                    updated_tags = list(existing_tags.union(tags_list))
                    updated_variants = list(existing_variants.union(variants_list))

                    collection.update_one(
                        {"_id": existing_doc["_id"]},
                        {"$set": {
                            "answers": updated_answers,
                            "tags": updated_tags,
                            "variants": updated_variants,
                            "created_at": created_at_value
                        }}
                    )
                    logging.info(f"Updated question: '{question_text}'")
                else:
                    # Insert a new document
                    doc = {
                        "question": question_text,
                        "variants": variants_list,
                        "answers": answers_list,
                        "tags": tags_list,
                        "created_at": created_at_value
                    }
                    collection.insert_one(doc)
                    logging.info(f"Inserted new question: '{question_text}'")

    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logging.error(f"Error importing CSV: {e}")
        raise

def is_single_word(input_text):
    # Check if the input is a single word
    return len(input_text.strip().split()) == 1

def find_questions_by_tag(tag):
    # Search for all questions that include the specified tag
    questions_with_tag = collection.find({"tags": tag})
    return list(questions_with_tag)

def display_questions_by_tag(tag):
    questions = find_questions_by_tag(tag)
    if not questions:
        print(f"Sorry, I couldn't find any questions related to '{tag}'. Please try another word.")
        return None

    print(f"Questions with tag '{tag}':")
    for i, question in enumerate(questions, start=1):
        print(f"{i}. {question['question']}")

    return questions
def get_answer_by_selection(questions):
    choice = input("Enter the number of the question you want the answer for: ").strip()
    
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(questions):
        print("Invalid choice. Please try again.")
        return None

    selected_question = questions[int(choice) - 1]
    print(f"Selected Question: {selected_question['question']}")
    print(f"Answers: {', '.join(selected_question['answers'])}")
    
def remove_question(question):
    question_lower = question.strip().lower()
    result = collection.delete_one({"question": question_lower})
    if result.deleted_count > 0:
        print(f"Removed question: '{question}' from MongoDB.")
    else:
        print(f"The question '{question}' does not exist in database.")

def remove_answer(question, answer):
    question_lower = question.strip().lower()
    doc = collection.find_one({"question": question_lower})
    if not doc:
        print(f"The question '{question}' does not exist in database.")
    else:
        if answer in doc["answers"]:
            doc["answers"].remove(answer)
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"answers": doc["answers"]}}
            )
            print(f"Removed answer '{answer}' from question '{question}'.")
        else:
            print(f"The answer '{answer}' does not exist for question '{question}'.")

def setup_logging(log_level="WARNING"):
    """
    Configure logging based on the provided log level.
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='chatbot.log',  # Save logs to a file
        filemode='a'  # Append to the log file
    )

parser = argparse.ArgumentParser(description="ChatBot Command Line Tool", add_help=False)
parser.add_argument('--help', action='store_true', help="Show help message and exit")
parser.add_argument('--log-mode', action='store_true', help="Enable logging mode")
parser.add_argument('--log-level', type=str, choices=['INFO', 'WARNING'], default='WARNING', help="Set the logging level (INFO or WARNING)")
parser.add_argument('--test', action='store_true', help="Run unit tests")
parser.add_argument('--view-logs', action='store_true',help="View the log and traceback files")
parser.add_argument('--list-questions', action='store_true', help="List all internal questions")
parser.add_argument('--add', action='store_true',help="Add a new question and answer to the internal list")
parser.add_argument('--remove', action='store_true',help="Remove a question from the internal list")
parser.add_argument('--remove-answer', type=str, help="Specify the answer to remove from the question")
parser.add_argument('--remove-tag', type=str, help="Specify the tag to remove from the question")
parser.add_argument('--remove-variant', type=str, help="Specify the variant to remove from the question")
parser.add_argument('--question', type=str,help="Specify the question to add or remove or ask the chatbot")
parser.add_argument('--answer', type=str,help="Specify the answer when adding a question")
parser.add_argument('--import-file', action='store_true',help="Import questions and answers from a CSV file")
parser.add_argument('--filetype', type=str,help="Specify the type of the file to import (e.g., CSV)")
parser.add_argument('--filepath', type=str,help="Specify the path to the file to import")
parser.add_argument('--variants', type=str, help="Specify variants for the question, separated by semicolons")
parser.add_argument('--tags', type=str, help="Specify tags for the question, separated by semicolons")


args = parser.parse_args()

if args.import_file:
    # Ensure that the file type is CSV
    if args.filetype.lower() != "csv":
        error_message = "Error: Only CSV filetype is supported."
        traceback_info = "Unsupported file type provided for import."
        print(error_message)
        save_error_logs(error_message, traceback_info)
        exit()

    try:
        validate_csv_path(args.filepath)  # Check the file path and access permissions
        import_csv_to_mongo(args.filepath)
        print("Successfully imported questions and answers to MongoDB from", args.filepath)

    except Exception as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)
    exit()
    


if args.view_logs:
    read_logs()
    exit()
    
if args.add and args.question:
    question = args.question.strip().lower()
    answer = args.answer.strip() if args.answer else None
    variants = [v.strip() for v in args.variants.split(";")] if args.variants else None
    tags = [t.strip() for t in args.tags.split(";")] if args.tags else None

    response = chatbot_response(question, answer=answer, variants=variants, tags=tags)
    print(f"Chatbot: {response}")
    exit()

if args.remove:
    if args.question and args.answer:
        # Remove a specific answer
        remove_answer(args.question, args.answer)
    elif args.question:
        # Remove the entire question
        remove_question(args.question)
    else:
        print("Error: Please specify a question to remove.")
    exit()

if args.list_questions:  # تغییر از list-questions به list_questions
    docs = collection.find({}, {"_id": 0, "question": 1})
    print("List of all questions:")
    for doc in docs:
        print(f"- {doc['question']}")
    exit()


if args.view_logs:
    read_logs()
    exit()
    
if args.question:
    response = chatbot_response(args.question)
    print(f"Chatbot: {response}")
    exit()

if args.add:
    if args.question and args.answer:
        question = args.question.strip().lower()
        answer = args.answer.strip()

        # Check if the question exists
        existing_doc = collection.find_one({"question": question})
        if existing_doc:
            # If the question exists, add the answer
            if answer not in existing_doc["answers"]:
                existing_doc["answers"].append(answer)
                collection.update_one(
                    {"_id": existing_doc["_id"]},
                    {"$set": {"answers": existing_doc["answers"]}}
                )
                print(f"Added new answer '{answer}' to existing question: '{question}'")
            else:
                print(f"The answer '{answer}' already exists for question: '{question}'")
        else:
            # If the question does not exist, add the new question and answer
            doc = {"question": question, "answers": [answer], "tags": []}
            collection.insert_one(doc)
            print(f"Added new question: '{question}' with answer: '{answer}'")
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()

if args.remove:
    if args.question and args.answer:
        # Remove a specific answer
        remove_answer(args.question, args.answer)
    elif args.question:
        # Remove the entire question
        remove_question(args.question)
    else:
        print("Error: Please specify a question to remove.")
    exit()

def remove_question(question):
    question_lower = question.strip().lower()
    result = collection.delete_one({"question": question_lower})
    if result.deleted_count > 0:
        print(f"Removed question: '{question}' from MongoDB.")
    else:
        print(f"The question '{question}' does not exist in database.")

    # Exit the program after printing questions
    exit()
    
if args.add and args.question and args.answer:
    add_answer(args.question, args.answer)
    exit()
    
if args.remove and args.question:
    question = args.question.strip().lower()

    if args.remove_answer:
        answer_to_remove = args.remove_answer.strip()
        doc = collection.find_one({"question": question})
        if doc and answer_to_remove in doc.get("answers", []):
            doc["answers"].remove(answer_to_remove)
            collection.update_one({"_id": doc["_id"]}, {"$set": {"answers": doc["answers"]}})
            print(f"Removed answer '{answer_to_remove}' from question '{question}'.")
        else:
            print(f"Answer '{answer_to_remove}' not found for question '{question}'.")

    if args.remove_tag:
        tag_to_remove = args.remove_tag.strip().lower()
        doc = collection.find_one({"question": question})
        if doc and tag_to_remove in doc.get("tags", []):
            doc["tags"].remove(tag_to_remove)
            collection.update_one({"_id": doc["_id"]}, {"$set": {"tags": doc["tags"]}})
            print(f"Removed tag '{tag_to_remove}' from question '{question}'.")
        else:
            print(f"Tag '{tag_to_remove}' not found for question '{question}'.")

    if args.remove_variant:
        variant_to_remove = args.remove_variant.strip().lower()
        doc = collection.find_one({"question": question})
        if doc and variant_to_remove in doc.get("variants", []):
            doc["variants"].remove(variant_to_remove)
            collection.update_one({"_id": doc["_id"]}, {"$set": {"variants": doc["variants"]}})
            print(f"Removed variant '{variant_to_remove}' from question '{question}'.")
        else:
            print(f"Variant '{variant_to_remove}' not found for question '{question}'.")

    # اگر هیچکدام از شرایط بالا فعال نبود، کل سؤال حذف می‌شود
    if not args.remove_answer and not args.remove_tag and not args.remove_variant:
        result = collection.delete_one({"question": question})
        if result.deleted_count > 0:
            print(f"Removed question: '{question}' from MongoDB.")
        else:
            print(f"The question '{question}' does not exist in database.")
    exit()
    
if args.list_questions:  # تغییر از list-questions به list_questions
    docs = collection.find({}, {"_id": 0, "question": 1})
    print("List of all questions:")
    for doc in docs:
        print(f"- {doc['question']}")
    exit()
    

class TestChatbot(unittest.TestCase):
    def test_chatbot_response(self):
        # تست جستجوی پاسخ
        add_answer("what is question?", "This is a question.")  # اضافه کردن سوال و پاسخ
        response = chatbot_response("what is question?")  # جستجوی سوال
        self.assertEqual(response, "This is a question.")  # بررسی پاسخ

    def test_add_answer(self):
        # تست اضافه کردن پاسخ
        add_answer("what is question?", "This is a question.")  # اضافه کردن سوال و پاسخ
        response = chatbot_response("what is question?")  # جستجوی سوال
        self.assertEqual(response, "This is a question.")  # بررسی پاسخ

    def test_remove_answer(self):
        # تست حذف پاسخ
        add_answer("what is question?", "This is a question.")  # اضافه کردن سوال و پاسخ
        remove_answer("what is question?", "This is a question.")  # حذف پاسخ
        response = chatbot_response("what is question?")  # جستجوی سوال
        self.assertNotEqual(response, "This is a question.")  # بررسی عدم وجود پاسخ

    def test_import_csv(self):
        # تست وارد کردن فایل CSV
        try:
            import_csv_to_mongo("questionPair.csv")  # وارد کردن فایل CSV
            self.assertTrue(True)  # اگر خطایی ندهد، تست موفق است
        except Exception as e:
            self.fail(f"Importing CSV failed with error: {e}")

if __name__ == '__main__':
    
    if args.help:
        print_help()
        exit(0)
    
    if args.log_mode:
        setup_logging(args.log_level)
        logging.info("Logging mode is enabled with level: %s", args.log_level)
        
    # اگر آرگومان --test وجود داشت، تست‌ها را اجرا کن
    if '--test' in sys.argv:
        unittest.main(argv=[''], exit=False)
    else:
        # در غیر این صورت، برنامه اصلی را اجرا کن
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{current_time} Hello! You can ask me questions. Type 'exit' to stop.")

        while True:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            user_input = input(f"{current_time} You: ").strip().lower()
            
            if not user_input.strip():
                print(f"{current_time} Chatbot: Please enter a valid question or command.")
                continue

            if user_input == "exit":
                print(f"{current_time} Chatbot: Goodbye! Have a great day!")
                break
            
            elif user_input in ["hello", "hi"]:
                print(f"{current_time} Chatbot: Hello! How can I assist you today?")
                continue

            if "?" in user_input and ("and" in user_input or "or" in user_input):
                response = handle_compound_question(user_input)
                print(f"{current_time} Chatbot:\n{response}")
            else:
                if is_single_word(user_input):
                    questions = display_questions_by_tag(user_input)
                    if questions:
                        get_answer_by_selection(questions)
                else:
                    response = chatbot_response(user_input)
                    print(f"{current_time} Chatbot: {response}")