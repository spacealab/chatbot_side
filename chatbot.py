import datetime
import random
import re
import csv
import argparse
import os
import traceback

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["chatbot_db"]
collection = db["questions_answers"]


csv_file_path = "questionPair.csv"


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
        "Tell me about infraction.",
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


def chatbot_response(user_input):
    original_question = find_original_question(user_input)
    if original_question:
        user_input = original_question

    user_input_lower = user_input.strip().lower()

    # در دیتابیس جستجو کنید
    doc = collection.find_one({"question": user_input_lower})

    if doc:
        # اگر سندی پیدا شد، یکی از پاسخ‌ها را برمی‌گردانیم
        if doc["answers"]:
            return random.choice(doc["answers"])
        else:
            return "I'm sorry, I don't have an answer for that."
    elif "hello" in user_input_lower:
        return "Hello! How can I assist you today?"
    elif "how are you?" in user_input_lower:
        return "I'm here to help you! How can I assist you?"
    elif "bye" in user_input_lower:
        return "Goodbye! Have a great day!"
    else:
        return "I'm sorry, I don't know the answer to that."

# Split compound questions


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

def export_mongo_to_csv(csv_file_path):
    import csv
    
    # تمام اسناد (Documents) را از دیتابیس بخوانید
    docs = collection.find()  # collection: کالکشن questions_answers در MongoDB

    # ابتدا مشخص کنیم بیشترین تعداد پاسخ در همه اسناد چند تاست
    max_answers = 0
    all_docs = list(docs)  # تبدیل Cursor به لیست
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
            # اگر تعداد پاسخ کمتر از max_answers بود، خالی پر کن
            while len(answers) < max_answers:
                answers.append("")
            row = [question] + answers
            writer.writerow(row)

    print(f"Data successfully exported from MongoDB to {csv_file_path}.")


def add_question(question, answers_list):
    question_lower = question.strip().lower()
    existing_doc = collection.find_one({"question": question_lower})
    
    if existing_doc:
        # اگر سوال وجود دارد، جواب‌ها را به لیست موجود اضافه کن
        for answer in answers_list:
            if answer not in existing_doc["answers"]:
                existing_doc["answers"].append(answer)
        
        # به‌روزرسانی سند در دیتابیس
        collection.update_one(
            {"_id": existing_doc["_id"]},
            {"$set": {"answers": existing_doc["answers"]}}
        )
        print(f"Updated question '{question}' with new answers: {answers_list}")
    else:
        # اگر سوال وجود ندارد، سوال و جواب جدید اضافه کن
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
        # اگر سوال وجود ندارد، سوال و جواب جدید را اضافه کنیم
        doc = {
            "question": question_lower,
            "answers": [new_answer],
            "tags": []  # می‌توانید در صورت نیاز تگ‌ها را نیز اضافه کنید
        }
        collection.insert_one(doc)
        print(f"Added new question '{question}' with answer '{new_answer}' to MongoDB.")
    else:
        # اگر سوال وجود دارد
        if new_answer in doc["answers"]:
            # اگر جواب موجود باشد
            print(f"The answer '{new_answer}' already exists for question '{question}'. No changes made.")
        else:
            # اگر جواب جدید باشد، آن را اضافه کنیم
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
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # 1) گرفتن فیلدها از فایل CSV
            question_text = row['question'].strip()  # نام ستون باید در CSV lowercase یا همانطور که هست باشد
            answers_str = row.get('answers', '').strip()  # رشته پاسخ‌ها
            tags_str = row.get('tags', '').strip()
            created_at_value = row.get('created_at', '').strip()

            # 2) تبدیل answers به لیست
            answers_list = []
            if answers_str:
                # فرض می‌کنیم با ; از هم جدا شده
                answers_list = [ans.strip() for ans in answers_str.split(';') if ans.strip()]

            # 3) تبدیل tags به لیست
            tags_list = []
            if tags_str:
                tags_list = [tag.strip() for tag in tags_str.split(';') if tag.strip()]

            # 4) بررسی اینکه آیا question در دیتابیس موجود است (جلوگیری از تکراری بودن)
            existing_doc = collection.find_one({"question": question_text.lower()})

            # 5) محاسبه created_at
            if not created_at_value:
                # اگر خالی بود، زمان فعلی را قرار دهید
                created_at_value = datetime.datetime.now()
            else:
                # تلاش برای تبدیل رشته به datetime
                try:
                    created_at_value = datetime.datetime.strptime(created_at_value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # اگر فرمت درست نبود، می‌توانید warning بدهید یا به عنوان استرینگ ذخیره کنید
                    pass

            # 6) اگر سند وجود نداشت، درج جدید
            if not existing_doc:
                doc = {
                    "question": question_text.lower(),  # یا بدون lower() اگر می‌خواهید عیناً ذخیره شود
                    "answers": answers_list,
                    "tags": tags_list,
                    "created_at": created_at_value
                }
                collection.insert_one(doc)
                print(f"Inserted new question: {question_text}")
            else:
                # داده تکراری یافت شد (سوال از قبل موجود)
                print(f"Question '{question_text}' already exists in DB. Skipped inserting.")
                # اگر می‌خواهید پاسخ‌ها و تگ‌های جدید را به سند قبلی اضافه کنید،
                # باید منطق آپدیت (update_one) بنویسید. درغیراینصورت کاری نکنید.
                # ...

def is_single_word(input_text):
    # بررسی می‌کند آیا ورودی فقط یک کلمه است
    return len(input_text.split()) == 1

def find_questions_by_tag(tag):
    # جستجوی تمام سوالاتی که شامل تگ مشخص شده باشند
    questions_with_tag = collection.find({"tags": tag})
    return list(questions_with_tag)

def display_questions_by_tag(tag):
    questions = find_questions_by_tag(tag)
    if not questions:
        print(f"No questions found with the tag '{tag}'.")
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


parser = argparse.ArgumentParser(description="ChatBot Command Line Tool")
# parser.add_argument("--question", type=str, help="Question to ask the chatbot")
parser.add_argument('--view-logs', action='store_true',
                    help="View the log and traceback files")

parser.add_argument('--list-questions', action='store_true',
                    help="List all internal questions")
# تعریف آرگومان‌های جدید برای اضافه و حذف کردن سوالات
parser.add_argument('--add', action='store_true',
                    help="Add a new question and answer to the internal list")
parser.add_argument('--remove', action='store_true',
                    help="Remove a question from the internal list")
parser.add_argument('--question', type=str,
                    help="Specify the question to add or remove")
parser.add_argument('--answer', type=str,
                    help="Specify the answer when adding a question")

parser.add_argument('--import-file', action='store_true',
                    help="Import questions and answers from a CSV file")
parser.add_argument('--filetype', type=str,
                    help="Specify the type of the file to import (e.g., CSV)")
parser.add_argument('--filepath', type=str,
                    help="Specify the path to the file to import")


args = parser.parse_args()

if args.import_file:
    # همچنان بررسی اینکه حتماً فایل CSV باشد
    if args.filetype.lower() != "csv":
        error_message = "Error: Only CSV filetype is supported."
        traceback_info = "Unsupported file type provided for import."
        print(error_message)
        save_error_logs(error_message, traceback_info)
        exit()

    try:
        validate_csv_path(args.filepath)  # بررسی مسیر و دسترسی فایل
        # به‌جای منطق قبلی، فقط تابع جدید را صدا بزنید:
        import_csv_to_mongo(args.filepath)
        
        print("Successfully imported questions and answers to MongoDB from", args.filepath)

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

if args.add:
    if args.question and args.answer:
        question = args.question.strip().lower()
        answer = args.answer.strip()

        # Check if the question exists
        existing_doc = collection.find_one({"question": question})
        if existing_doc:
            # اگر سوال وجود دارد، پاسخ را اضافه کن
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
            # اگر سوال وجود ندارد، سوال و پاسخ جدید اضافه کن
            doc = {"question": question, "answers": [answer], "tags": []}
            collection.insert_one(doc)
            print(f"Added new question: '{question}' with answer: '{answer}'")
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()



if args.remove:
    if args.question and args.answer:
        # حذف پاسخ خاص
        remove_answer(args.question, args.answer)
    elif args.question:
        # حذف کل سوال
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



    # From keyword_questions
    print("\nKeyword-based questions:")
    for keyword, questions in keyword_questions.items():
        print(f"\nKeyword: {keyword}")
        for question in questions:
            print(f"  - {question}")

    # Exit the program after printing questions
    exit()
    
if args.add and args.question and args.answer:
    add_answer(args.question, args.answer)
    exit()
    
if args.remove and args.question:
    remove_question(args.question)
    exit()




# Main program loop
def is_single_word(input_text):
    # بررسی می‌کند آیا ورودی فقط یک کلمه است
    return len(input_text.split()) == 1

# Main program loop
current_time = datetime.datetime.now().strftime("%H:%M:%S")
print(f"{current_time} Hello! You can ask me questions. Type 'exit' to stop.")

while True:
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    user_input = input("You: ")
    print(f"{current_time} You: {user_input}")

    if user_input.lower() == "exit":
        print(f"{current_time} Chatbot: Goodbye!")
        break

    # اگر ورودی حاوی پرسش‌های مرکب است...
    if "?" in user_input and ("and" in user_input or "or" in user_input):
        response = handle_compound_question(user_input)
    else:
        if is_single_word(user_input):
            # اگر ورودی فقط یک کلمه باشد
            questions = display_questions_by_tag(user_input)
            if questions:
                get_answer_by_selection(questions)
        else:
            # 3) در سایر شرایط برویم سراغ سوال-جواب عادی
            response = chatbot_response(user_input)
            print(f"{current_time} Chatbot: {response}")