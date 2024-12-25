# Chatbot Console Application

This repository contains a Python-based chatbot console application. The chatbot is designed to handle user queries, respond to commands, and interact with users in a conversational format via the terminal.

## Features

- **Basic Interaction**: The chatbot greets the user with a time-stamped message and interacts with conversational prompts.
- **Keyword Detection**: Recognizes specific keywords like "hello," "hi," and "bye" to provide context-specific responses.
- **Question-Answer Handling**:
  - Responds to predefined questions stored in a MongoDB database.
  - Provides error messages when a question is not found in the database.
- **Compound Question Parsing**: Supports compound questions containing "and" or "or" and splits them for sequential answers.
- **CSV Import/Export**:
  - Import questions and answers from a CSV file into MongoDB.
  - Export questions and answers from MongoDB into a CSV file.
- **Command Line Support**:
  - Allows users to ask questions via command-line arguments using the `--question` flag.
- **Error Logging**: Handles unexpected errors with detailed logs saved as text files.
- **Customizable Responses**: Easily modify the question-answer database for your use case.

## Requirements

- Python 3.7 or higher
- MongoDB server
- Python packages:
  - `pymongo`
  - `argparse`

You can install the required packages using pip:

```bash
pip install pymongo
```

## How to Run

1. Clone this repository:

   ```bash
   git clone https://github.com/spacealab/chatbot-console-app.git
   cd chatbot-console-app
   ```

2. Ensure MongoDB is installed and running on your system.

3. Run the chatbot:

   ```bash
   python chatbot.py
   ```

4. Optional Command-Line Argument: Ask a question directly when starting the chatbot:

   ```bash
   python chatbot.py --question "What is Python?"
   ```

## File Structure

- `chatbot.py`: Main script containing the chatbot logic.
- `questionPair.csv`: Sample CSV file for importing/exporting questions and answers.
- `log.txt` / `traceback.txt`: Logs for debugging errors.
- `README.md`: Project documentation.

## Usage

- **Start the Chatbot**: Type a question in the terminal to receive an answer.
- **Special Commands**:
  - Type `bye` to exit the chatbot.
  - Type `hello` or `hi` to receive a greeting from the chatbot.
- **Database Integration**:
  - Add, remove, or update questions/answers in the MongoDB database.
- **Error Logs**: Review the generated log files (`log.txt`, `traceback.txt`) for any unexpected errors.

## Examples

### Starting the Chatbot:

```bash
22:13:34 Chatbot: Hello! Good day to you!
22:13:38 You: What is Python?
22:13:38 Chatbot: Python is a programming language.
```

### Using Command-Line Arguments:

```bash
$ python chatbot.py --question "What is MongoDB?"
Chatbot: MongoDB is a NoSQL database.
```

### Handling Unknown Questions:

```bash
22:14:15 You: What is AI?
22:14:15 Chatbot: I'm sorry, I couldn't find an answer for your question. Please try asking something else.
```

## Future Improvements

- Add support for graphical user interfaces (GUI).
- Enhance AI-driven responses using NLP libraries.
- Extend database functionality with cloud storage options.
- Add multi-language support.

## Contribution

Feel free to contribute to this project! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.
