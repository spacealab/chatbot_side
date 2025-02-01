# erstsemester-projekt-g2

# Documentation for the Chatbot Program

## Overview

This chatbot program is designed to interact with users by answering questions, managing a trivia game, and monitoring temperature data. It supports various features such as adding/removing questions, importing questions from a CSV file, and logging errors. The program also integrates with a Sense HAT (if available) to display visual symbols and messages.

## Features

1. **Question-Answer Management**:
   - Add new questions and answers.
   - Remove existing questions or answers.
   - Import questions and answers from a CSV file.

2. **Trivia Game**:
   - Start a trivia game with questions from the loaded dataset.
   - Display game start and exit symbols on the Sense HAT.

3. **Temperature Monitoring**:
   - Simulate temperature data (local and forecast).
   - Record and display temperature changes over the last 3 days.

4. **Error Handling and Logging**:
   - Log errors and traceback information to files.
   - View logs and traceback information.

5. **Sense HAT Integration**:
   - Display start, game start, and game exit symbols on the Sense HAT.
   - Show game scores on the Sense HAT.

## Installation

1. **Prerequisites**:
   - Python 3.x
   - Required Python packages: `requests`, `sense-hat`, `chardet`, `argparse`, `csv`, `datetime`, `random`, `re`, `os`, `traceback`, `logging`, `unittest`

2. **Installation Steps**:
   - Clone the repository or download the script.
   - Install the required packages using pip:
     ```bash
     pip install requests sense-hat chardet
     ```
   - Ensure the Sense HAT is connected if you plan to use its features.

## Usage

### Running the Program

To run the program, use the following command:

Usage:
    python chatbot.py [options]

Command Line Options:
    --debug              Enable debug mode for detailed output.
    --view-logs          View the log and traceback files.
    --list-questions     List all internal questions.
    --log-mode           Enable logging mode to save logs to a file.
    --log-level          Set the logging level (INFO or WARNING). Default is WARNING.
    --add                Add a new question and answer to the internal list.
    --remove             Remove a question from the internal list.
    --question           Specify the question to add or remove.
    --answer             Specify the answer when adding a question.
    --import-file        Import questions and answers from a CSV file.
    --filetype           Specify the type of the file to import (e.g., CSV).
    --filepath           Specify the path to the file to import.
    --test               Run unit tests.
    --monitor            Enable temperature monitoring.

Examples:

1. Adding a New Question and Answer:
    To add a new question and its answer to the chatbot's database, use the following command:
    
    ```bash
    python chatbot.py --add --question "What is Python?" --answer "Python is a programming language."
    ```
    
    This command adds the question "What is Python?" with the answer "Python is a programming language." to the CSV file.

2. Removing a Question:
    To remove a question from the chatbot's database, use the following command:
    
    ```bash
    python chatbot.py --remove --question "What is Python?"
    ```
    
    This command removes the question "What is Python?" and all its associated answers from the CSV file.

3. Listing All Questions:
    To list all the questions stored in the chatbot's database, use the following command:
    
    ```bash
    python chatbot.py --list-questions
    ```
    
    This command prints all the questions available in the CSV file and keyword-based questions.

4. Starting the Trivia Game:
    To start the trivia game, simply run the chatbot and type "trivia" when prompted:
    
    ```bash
    python chatbot.py
    ```
    
    Then, when the chatbot asks for input, type:
    
    ```
    trivia
    ```
    
    This will start the trivia game with 10 random questions from the database.

5. Monitoring Temperature:
    To enable temperature monitoring, use the following command:
    
    ```bash
    python chatbot.py --monitor
    ```
    
    This command starts monitoring local and forecasted temperatures. Type "stop" to terminate the monitoring.

6. Viewing Logs:
    To view the logs and traceback information, use the following command:
    
    ```bash
    python chatbot.py --view-logs
    ```
    
    This command displays the contents of the log and traceback files.

7. Importing Questions from a CSV File:
    To import questions and answers from a CSV file, use the following command:
    
    ```bash
    python chatbot.py --import-file --filetype CSV --filepath /path/to/your/file.csv
    ```
    
    Replace `/path/to/your/file.csv` with the actual path to your CSV file. This command imports questions and answers from the specified CSV file.

8. Running Unit Tests:
    To run the unit tests for the chatbot, use the following command:
    
    ```bash
    python chatbot.py --test
    ```
    
    This command runs the unit tests defined in the `TestChatbot` class.

CSV File Format:
    The CSV file used by the chatbot should follow this structure:
    
    | Question         | Answer1                          | Answer2 | Answer3 | Answer4 |
    |------------------|----------------------------------|---------|---------|---------|
    | What is Python?  | Python is a programming language. |         |         |         |
    | What is AI?      | AI stands for Artificial Intelligence. |         |         |         |

    - The first row must contain the headers: Question, Answer1, Answer2, Answer3, Answer4.
    - Each subsequent row represents a question and its possible answers.
    - If a question has fewer than 4 answers, leave the remaining columns empty.

Log Files:
    - Log files are saved in the format: `log_YYYYMMDD_HHMMSS.txt`.
    - Traceback files are saved in the format: `traceback_YYYYMMDD_HHMMSS.txt`.
    - These files contain error messages and stack traces for debugging purposes.

Sense HAT Symbols:
    - Start Symbol: A grid of red pixels displayed on the Sense HAT when the program starts.
    - Game Start Symbol: A grid of green pixels displayed when the trivia game starts.
    - Game Exit Symbol: A grid of blue pixels displayed when the trivia game ends, along with the player's score.

Unit Testing:
    To run unit tests for the chatbot, use the following command:
    
    ```bash
    python chatbot.py --test

Contributing:
    To contribute to this project, follow these steps:

    1. Fork the repository:
       - Click the "Fork" button on the GitHub repository page to create a copy of the project in your GitHub account.

    2. Create a new branch:
       - Clone your forked repository to your local machine:
         ```bash
         git clone https://github.com/YOUR_USERNAME/REPOSITORY_NAME.git
         ```
       - Create a new branch for your feature or bugfix:
         ```bash
         git checkout -b feature/your-feature-name
         ```

    3. Commit your changes:
       - Make your changes to the code.
       - Stage your changes:
         ```bash
         git add .
         ```
       - Commit your changes with a descriptive message:
         ```bash
         git commit -m "Add new feature: your feature description"
         ```

    4. Push your branch to your fork:
       - Push your changes to your forked repository:
         ```bash
         git push origin feature/your-feature-name
         ```

    5. Submit a pull request:
       - Go to the original repository on GitHub.
       - Click the "New Pull Request" button.
       - Select your branch and provide a description of your changes.
       - Submit the pull request for review.

License:
    This project is licensed under the MIT License. See the **LICENSE** file in the repository for details.

Support:
    For any issues or questions, please open an issue on the GitHub repository:
    - Go to the "Issues" tab on the repository page.
    - Click "New Issue" and provide details about the problem or question.

