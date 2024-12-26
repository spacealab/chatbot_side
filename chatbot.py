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

# Find the original question from variants
def find_original_question(user_input):
    doc = collection.find_one({"variants": {"$in": [user_input.strip().lower()]}})
    return doc["question"] if doc else None

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
def chatbot_response(user_input):
    try:
        original_question = find_original_question(user_input)
        if original_question:
            user_input = original_question

        user_input_lower = user_input.strip().lower()

        # Search the database for the question
        doc = collection.find_one({"question": user_input_lower})
        if doc:
            # If a document is found, return one of the answers
            if doc["answers"]:
                return random.choice(doc["answers"])
            else:
                return "I'm sorry, I don't have an answer for that."
        else:
            return "I'm sorry, I couldn't find an answer for your question. Please try asking something else."
    except Exception as e:
        # Log the error and return a generic message
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
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # 1) Extract fields from the CSV file
            question_text = row['question'].strip()  # Column name should match exactly in the CSV, either lowercase or as is
            answers_str = row.get('answers', '').strip()  # String containing answers
            tags_str = row.get('tags', '').strip()
            created_at_value = row.get('created_at', '').strip()

            # 2) Convert answers to a list
            answers_list = []
            if answers_str:
                # Assume answers are separated by a semicolon (;)
                answers_list = [ans.strip() for ans in answers_str.split(';') if ans.strip()]

            # 3) Convert tags to a list
            tags_list = []
            if tags_str:
                tags_list = [tag.strip() for tag in tags_str.split(';') if tag.strip()]

            # 4) Check if the question already exists in the database (to avoid duplicates)
            existing_doc = collection.find_one({"question": question_text.lower()})

            # 5) Handle created_at field
            if not created_at_value:
                # If empty, use the current time
                created_at_value = datetime.datetime.now()
            else:
                # Attempt to convert the string to a datetime object
                try:
                    created_at_value = datetime.datetime.strptime(created_at_value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # If the format is invalid, you can issue a warning or store it as a string
                    pass

            # 6) If the document does not exist, insert a new one
            if not existing_doc:
                doc = {
                    "question": question_text.lower(),  # Use lower() or leave it as-is based on requirements
                    "answers": answers_list,
                    "tags": tags_list,
                    "created_at": created_at_value
                }
                collection.insert_one(doc)
                print(f"Inserted new question: {question_text}")
            else:
                # Duplicate data found (question already exists)
                print(f"Question '{question_text}' already exists in DB. Skipped inserting.")

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


parser = argparse.ArgumentParser(description="ChatBot Command Line Tool")
parser.add_argument('--view-logs', action='store_true',help="View the log and traceback files")
parser.add_argument('--list-questions', action='store_true',help="List all internal questions")
parser.add_argument('--add', action='store_true',help="Add a new question and answer to the internal list")
parser.add_argument('--remove', action='store_true',help="Remove a question from the internal list")
parser.add_argument('--question', type=str,help="Specify the question to add or remove or ask the chatbot")
parser.add_argument('--answer', type=str,help="Specify the answer when adding a question")
parser.add_argument('--import-file', action='store_true',help="Import questions and answers from a CSV file")
parser.add_argument('--filetype', type=str,help="Specify the type of the file to import (e.g., CSV)")
parser.add_argument('--filepath', type=str,help="Specify the path to the file to import")


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
        # Instead of the previous logic, simply call the new function:
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
    remove_question(args.question)
    exit()

# Main program loop
current_time = datetime.datetime.now().strftime("%H:%M:%S")
print(f"{current_time} Hello! You can ask me questions. Type 'exit' to stop.")

while True:
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    user_input = input(f"{current_time} You: ").strip().lower()
    
    # Handle empty or invalid inputs
    if not user_input.strip():
        print(f"{current_time} Chatbot: Please enter a valid question or command.")
        continue  # Skip further processing and prompt the user again

    if user_input == "bye":
        print(f"{current_time} Chatbot: Goodbye! Have a great day!")
        break  # Exit the program when "bye" is typed
    
    elif user_input in ["hello", "hi"]:
        print(f"{current_time} Chatbot: Hello! How can I assist you today?")
        continue  # Skip further processing for "hi" or "hello"

    # If the input contains compound questions...
    if "?" in user_input and ("and" in user_input or "or" in user_input):
        response = handle_compound_question(user_input)
        print(f"{current_time} Chatbot:\n{response}")
    else:
        if is_single_word(user_input):
            # If the input is a single word
            questions = display_questions_by_tag(user_input)
            if questions:
                get_answer_by_selection(questions)
        else:
            # In other cases, use normal question-answer logic
            response = chatbot_response(user_input)
            print(f"{current_time} Chatbot: {response}")