import datetime
import random
import re
import csv
import argparse
import os
import traceback


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
except FileNotFoundError:
    print("Error: The specified file does not exist.")
except PermissionError:
    print("Error: Insufficient permissions to read the file.")
except ValueError as ve:
    print(f"Error: {ve}")
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


def chatbot_response(user_input):
    original_question = find_original_question(user_input)
    if original_question:
        user_input = original_question
    if user_input in qa_pairs:
        if isinstance(qa_pairs[user_input], list):
            return random.choice(qa_pairs[user_input])
        else:
            return qa_pairs[user_input]
    elif "hello" in user_input.lower():
        return "Hello! How can I assist you today?"
    elif "how are you?" in user_input.lower():
        return "I'm here to help you! How can I assist you?"
    elif "bye" in user_input.lower():
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


def save_to_csv(csv_file_path, qa_pairs):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Determine the maximum number of answers
        max_answers = max(len(answers) for answers in qa_pairs.values())
        header = ["Question"] + [f"Answer{i+1}" for i in range(max_answers)]

        # Write header
        writer.writerow(header)

        # Write questions and answers
        for question, answers in qa_pairs.items():
            # Ensure all answer columns are filled
            while len(answers) < max_answers:
                answers.append("")
            writer.writerow([question] + answers)

    print(f"Data successfully saved to {csv_file_path}")


def add_question(csv_file_path, question, answers):
    if question in qa_pairs:
        print(f"The question '{question}' already exists.")
        return

    # اضافه کردن سوال جدید
    qa_pairs[question] = answers
    print(f"Added question: '{question}' with answers: {answers}")
    save_to_csv(csv_file_path, qa_pairs)


def remove_question(csv_file_path, question):
    if question in qa_pairs:
        del qa_pairs[question]
        print(f"Removed question: '{question}'")
        save_to_csv(csv_file_path, qa_pairs)
    else:
        print(f"The question '{question}' does not exist.")


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
    #except FileNotFoundError:
        #print("Log or traceback file not found.")
    except FileNotFoundError as e:
        error_message = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_message}")
        save_error_logs(error_message, traceback_info)


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
                raise ValueError("The CSV file format is unsupported or missing required columns.")

            # Process the file
            qa_pairs.clear()
            for row in reader:
                question = row['Question'].strip().lower()
                answers = [row[col].strip() for col in ['Answer1', 'Answer2', 'Answer3', 'Answer4']if col in row and row[col].strip()]
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

if args.add:
    if args.question and args.answer:
        question = args.question.strip().lower()
        answer = args.answer.strip()

        if question in qa_pairs:
            # Add answer to existing question
            if answer not in qa_pairs[question]:
                qa_pairs[question].append(answer)
                print(f"Added answer '{answer}' to existing question: '{question}'")
            else:
                print(f"The answer '{answer}' already exists for question: '{question}'")
        else:
            # Add new question with answer
            qa_pairs[question] = [answer]
            print(f"Added new question: '{question}' with answer: '{answer}'")

        # Save changes to CSV
        save_to_csv(csv_file_path, qa_pairs)
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()



if args.remove and args.answer:
    if args.question:
        # question = args.question.lower()
        remove_answer(csv_file_path, args.question, args.answer)
    exit()


if args.add:
    if args.question and args.answer:
        question = args.question.strip().lower()
        answer = args.answer.strip()

        # Check if the question exists
        if question in qa_pairs:
            if answer not in qa_pairs[question]:
                qa_pairs[question].append(answer)
                print(f"Added answer '{answer}' to existing question: '{question}'")
            else:
                print(f"The answer '{answer}' already exists for question: '{question}'")
        else:
            # Add a new question and answer
            qa_pairs[question] = [answer]
            print(f"Added new question: '{question}' with answer: '{answer}'")

        # Save the updated qa_pairs to the CSV
        save_to_csv(csv_file_path, qa_pairs)
    else:
        print("Error: Both --question and --answer must be specified when using --add.")
    exit()
        
    answers = args.answer.split(';')

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
    if not args.question:
        print("Error: --question must be specified when using --remove.")
        exit()

    question_key = args.question.strip().lower()

    # حذف سوال از لیست
    if args.question in qa_pairs:
        del qa_pairs[args.question]
        save_to_csv('questionPair.csv', qa_pairs)
        print(f"Removed question: '{args.question}' and updated CSV file successfully.")
    else:
        print(f"Question '{args.question}' does not exist.")

    # توقف برنامه
    exit()


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
        # 1) بررسی تک‌کلمه بودن
        user_input_lower = user_input.strip().lower()
        words = user_input_lower.split()
        is_single_word = (len(words) == 1)

        # 2) اگر تک‌کلمه و جزو کلیدواژه‌ها
        if is_single_word and user_input_lower in keyword_questions:
            response = show_suggestions(user_input_lower)
        else:
            # 3) در سایر شرایط برویم سراغ سوال-جواب عادی
            response = chatbot_response(user_input)

    print(f"{current_time} Chatbot: {response}")
